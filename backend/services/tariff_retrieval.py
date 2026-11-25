"""Vector store and clause retrieval over tariff documents (SCRUM-30).

Chunks each DISCO's raw tariff extract (``data/tariffs/raw/<disco>/tariff_extract_2026.md``,
SCRUM-27) by its numbered section headings, embeds each chunk with a local
sentence-transformers model, and answers queries by cosine similarity.

The extracts are copies of a secondary guide, so rows that disagree with the
notified SROs are replaced at index time by the rows in
``data/tariffs/raw/_official/`` (SCRUM-31): ``sro_rows_2026.md`` for every
DISCO, ``<disco>_rows_2026.md`` for one. The guide files stay unedited.

No Gemini calls here: embeddings are local per the locked decision in
``docs/decisions.md`` (2026-11-14) — a second rate-limited API call path on
top of extraction and grounding was judged too risky after Sprint 1's
free-tier problems. Gemini is only used later, in the Grounding Agent's
reasoning step (SCRUM-31).
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

import numpy as np
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from config import PROJECT_ROOT

RAW_TARIFF_DIR = PROJECT_ROOT / "data" / "tariffs" / "raw"
OFFICIAL_DIR = RAW_TARIFF_DIR / "_official"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Folder name under data/tariffs/raw/, and the short code used in clause ids,
# for every spelling of a DISCO name a caller might pass in.
_DISCO_DIRS = {
    "k-electric": "k-electric",
    "k-electric (ke)": "k-electric",
    "ke": "k-electric",
    "iesco": "iesco",
    "lesco": "lesco",
}
_SHORT_CODES = {"k-electric": "KE", "iesco": "IESCO", "lesco": "LESCO"}
_FULL_NAMES = {"KE": "K-Electric", "IESCO": "IESCO", "LESCO": "LESCO"}

# Matches the extract files' section headings, e.g. "**2.1 Category A-1: ...**"
# or "**2\. NEPRA & ...**" (the literal backslash is how the source escapes
# the period on whole-number headings).
_HEADING_RE = re.compile(r"^\*\*(?P<number>\d+(?:\.\d+)*)\\?\.?\s+(?P<title>.+?)\*\*\s*$")
_FRONT_MATTER_RE = re.compile(r"^---\n(?P<meta>.*?)\n---\n", re.DOTALL)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_CLAUSE_CODE_RE = re.compile(r"^([A-Z]+-?\d[\w().\-]*)")
# Per-section metadata lines, used by the official rows file.
_SOURCE_RE = re.compile(r"^Source:\s*(\S+)\s*$", re.MULTILINE)
_MONTHS_RE = re.compile(r"^Billing months:\s*(\d{4}-\d{2}) to (\d{4}-\d{2})\s*$", re.MULTILINE)
_SUPERSEDES_RE = re.compile(r"^Supersedes:\s*(.+)$", re.MULTILINE)


class TariffChunk(BaseModel):
    """One retrievable section of a tariff document."""

    disco: str
    clause_id: str
    heading: str
    text: str
    source_file: str
    row_label: str | None = None  # first cell, for chunks made from a table row
    # Set only for official rows: where the clause was notified, and the
    # billing months it is limited to ("YYYY-MM", inclusive).
    source_url: str | None = None
    effective_from_month: str | None = None
    effective_to_month: str | None = None

    def covers(self, billing_month: str | None) -> bool:
        if billing_month is None or self.effective_from_month is None:
            return True
        return self.effective_from_month <= billing_month <= self.effective_to_month


class ChunkResult(BaseModel):
    """A chunk plus its cosine similarity to a query."""

    chunk: TariffChunk
    score: float


def _resolve_disco_dir(disco: str) -> str:
    key = disco.strip().lower()
    if key not in _DISCO_DIRS:
        known = sorted({d for d in _DISCO_DIRS.values()})
        raise ValueError(f"Unknown DISCO '{disco}'. Known DISCOs: {known}")
    return _DISCO_DIRS[key]


def _strip_front_matter(raw_text: str) -> str:
    match = _FRONT_MATTER_RE.match(raw_text)
    return raw_text[match.end():] if match else raw_text


def _clean_cell(cell: str) -> str:
    """Strip markdown bold markers and escape backslashes from a table cell."""
    return _BOLD_RE.sub(r"\1", cell).replace("\\", "").strip()


def _split_table(
    body_lines: list[str],
) -> tuple[list[str], list[str], list[list[str]]]:
    """Split a section's lines into (intro_lines, header_cells, data_rows).

    `header_cells`/`data_rows` are empty if the section has no markdown
    table. The separator row ("---|---") is dropped automatically.
    """
    table_start = next(
        (i for i, line in enumerate(body_lines) if line.strip().startswith("|")),
        None,
    )
    if table_start is None:
        return body_lines, [], []

    def split_row(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    table_lines = [
        line.strip() for line in body_lines[table_start:] if line.strip().startswith("|")
    ]
    header_cells = [_clean_cell(c) for c in split_row(table_lines[0])]
    data_rows = []
    for line in table_lines[1:]:
        cells = split_row(line)
        if all(re.fullmatch(r"-+", c) for c in cells):
            continue  # markdown's header/body separator row
        data_rows.append([_clean_cell(c) for c in cells])
    return body_lines[:table_start], header_cells, data_rows


def _table_row_chunks(
    data_rows: list[list[str]],
    header_cells: list[str],
    short_code: str,
    number: str,
    title: str,
    source_file: str,
    superseded: frozenset[str],
) -> list[TariffChunk]:
    """One chunk per data row, so a lookup like "Lifeline rate" or "GST rate"
    hits a chunk about just that clause instead of a whole category table.

    A row where every cell but the first is blank is a sub-heading embedded
    in the table (e.g. "...PROTECTED CONSUMERS...") rather than real data;
    it becomes context carried into the following rows instead of its own
    chunk.
    """
    chunks = []
    current_label: str | None = None
    row_index = 0
    for cells in data_rows:
        if sum(1 for c in cells if c) <= 1:
            if cells and cells[0]:
                current_label = cells[0]
            continue

        row_index += 1
        first_cell = cells[0]
        if first_cell in superseded:
            continue  # replaced by an official row
        # A natural-language sentence, not a "field: value" list. Measured
        # directly against this corpus: the same row phrased as key/value
        # pairs scores ~0.48 cosine similarity against a plainly relevant
        # query, phrased as a sentence it scores ~0.69-0.77 — MiniLM was
        # trained on sentences, not table dumps, and the gap decides
        # whether the right chunk lands in the top 3 at all.
        fields = ", ".join(
            f"{header} is {value}"
            for header, value in zip(header_cells[1:], cells[1:])
            if value
        )
        context = ", under ".join(filter(None, [title, current_label]))
        disco_name = _FULL_NAMES[short_code]
        text = f"For {disco_name}, under {context}, {first_cell}: {fields}."

        code_match = _CLAUSE_CODE_RE.match(first_cell)
        clause_suffix = code_match.group(1) if code_match else str(row_index)

        chunks.append(
            TariffChunk(
                disco=short_code,
                clause_id=f"{short_code}-{number}-{clause_suffix}",
                heading=f"{title} — {first_cell}" if first_cell else title,
                text=text,
                source_file=source_file,
                row_label=first_cell,
            )
        )
    return chunks


def row_tariff_code(row_label: str) -> str | None:
    """The engine's tariff code for a rate-table row label, if it has one."""
    if row_label.startswith("A-1a("):
        return "A-1(a)"  # the guide writes the bill's "A-1a(01)" form
    for prefix, code in (("Pre-Paid Bulk", "Prepaid Bulk"), ("Pre-Paid Industrial", "Prepaid Industrial")):
        if row_label.startswith(prefix):
            return code
    letter = re.match(r"^Tariff ([A-Z])\b", row_label)
    if letter:
        return letter.group(1)
    code = re.match(r"^[A-E]-\d(\([a-z]+\))?", row_label)
    return code.group(0) if code else None


def chunk_document(
    path: Path, short_code: str, superseded: frozenset[str] = frozenset()
) -> list[TariffChunk]:
    """Chunk one tariff extract: one chunk per section's intro text, plus
    one chunk per table row within that section (see `_table_row_chunks`).

    Text before the first numbered heading (source notes, applicability
    caveats) is boilerplate rather than billable clause text, so it is
    dropped.
    """
    raw_text = path.read_text(encoding="utf-8")
    body = _strip_front_matter(raw_text)
    source_file = str(path.relative_to(PROJECT_ROOT))

    sections: list[tuple[str, str, list[str]]] = []
    current: tuple[str, str, list[str]] | None = None
    for line in body.splitlines():
        heading_match = _HEADING_RE.match(line.strip())
        if heading_match:
            if current is not None:
                sections.append(current)
            current = (heading_match.group("number"), heading_match.group("title"), [])
        elif current is not None:
            current[2].append(line)
    if current is not None:
        sections.append(current)

    chunks = []
    for number, title, body_lines in sections:
        intro_lines, header_cells, data_rows = _split_table(body_lines)

        intro_text = "\n".join(intro_lines).strip()
        source = _SOURCE_RE.search(intro_text)
        months = _MONTHS_RE.search(intro_text)
        official = {
            "source_url": source.group(1) if source else None,
            "effective_from_month": months.group(1) if months else None,
            "effective_to_month": months.group(2) if months else None,
        }
        # A section with a Source line is metadata plus rows, not a clause.
        if intro_text and not source:
            chunks.append(
                TariffChunk(
                    disco=short_code,
                    clause_id=f"{short_code}-{number}",
                    heading=title,
                    text=f"{title}\n\n{intro_text}",
                    source_file=source_file,
                )
            )

        rows = _table_row_chunks(
            data_rows, header_cells, short_code, number, title, source_file, superseded
        )
        chunks.extend(row.model_copy(update=official) for row in rows)
    return chunks


def official_paths(disco_dir: str) -> list[Path]:
    """The official rows files that apply to one DISCO."""
    paths = [OFFICIAL_DIR / "sro_rows_2026.md", OFFICIAL_DIR / f"{disco_dir}_rows_2026.md"]
    return [path for path in paths if path.exists()]


def superseded_rows(disco_dir: str) -> frozenset[str]:
    """Guide row labels that the official rows replace for this DISCO."""
    return frozenset(
        label.strip()
        for path in official_paths(disco_dir)
        for line in _SUPERSEDES_RE.findall(path.read_text(encoding="utf-8"))
        for label in line.split("|")
    )


_model_lock = threading.Lock()
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


class _DiscoIndex:
    def __init__(self, chunks: list[TariffChunk], embeddings: np.ndarray) -> None:
        self.chunks = chunks
        self.embeddings = embeddings  # (n_chunks, dim), L2-normalized rows


_index_cache: dict[str, _DiscoIndex] = {}
_index_lock = threading.Lock()


def _build_index(disco_dir: str) -> _DiscoIndex:
    path = RAW_TARIFF_DIR / disco_dir / "tariff_extract_2026.md"
    short_code = _SHORT_CODES[disco_dir]
    chunks = chunk_document(path, short_code, superseded_rows(disco_dir))
    if not chunks:
        raise ValueError(f"No chunks could be extracted from {path}")
    for official in official_paths(disco_dir):
        chunks += chunk_document(official, short_code)

    model = _get_model()
    embeddings = np.asarray(
        model.encode([chunk.text for chunk in chunks], normalize_embeddings=True)
    )
    return _DiscoIndex(chunks=chunks, embeddings=embeddings)


def _get_index(disco_dir: str) -> _DiscoIndex:
    if disco_dir not in _index_cache:
        with _index_lock:
            if disco_dir not in _index_cache:
                _index_cache[disco_dir] = _build_index(disco_dir)
    return _index_cache[disco_dir]


def retrieve(
    query: str,
    disco: str,
    top_k: int = 3,
    billing_month: str | None = None,
    tariff_code: str | None = None,
    row_label: str | None = None,
    contains: str | None = None,
) -> list[ChunkResult]:
    """Return the top-k tariff chunks for `disco` closest to `query`.

    With a `billing_month`, clauses limited to other months are left out.
    `tariff_code` limits the search to that tariff's rate rows, `row_label` to
    one named line, and `contains` to chunks printing that text (a rate).
    Similarity alone often picks a neighbouring tariff's row, since the rows
    read almost the same. The result is empty if nothing qualifies.
    """
    disco_dir = _resolve_disco_dir(disco)
    index = _get_index(disco_dir)

    model = _get_model()
    query_vec = np.asarray(model.encode([query], normalize_embeddings=True))[0]

    # Both sides are L2-normalized, so the dot product is cosine similarity.
    scores = index.embeddings @ query_vec
    def qualifies(chunk: TariffChunk) -> bool:
        if not chunk.covers(billing_month):
            return False
        if row_label is not None and chunk.row_label != row_label:
            return False
        if tariff_code is not None and (
            chunk.row_label is None or row_tariff_code(chunk.row_label) != tariff_code
        ):
            return False
        return contains is None or contains in chunk.text

    top_indices = [i for i in np.argsort(-scores) if qualifies(index.chunks[i])][:top_k]

    return [
        ChunkResult(chunk=index.chunks[i], score=float(scores[i]))
        for i in top_indices
    ]
