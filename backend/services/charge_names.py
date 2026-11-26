"""How charge lines printed on a bill map to the engine's components."""

import re

# Normalized bill charge-line wording -> canonical component key.
# "Canonical key" is either "energy"/"fixed" (the engine's own fields) or
# the slug of a tax/adjustment's name in the tariff JSON (e.g. "gst").
CHARGE_NAME_ALIASES: dict[str, str] = {
    "cost of electricity": "energy",
    "energy charges": "energy",
    "energy charge": "energy",
    "units charges": "energy",
    "electricity charges": "energy",
    "fixed charges": "fixed",
    "fixed charge": "fixed",
    "meter rent": "fixed",
    "service rent": "fixed",
    "electricity duty": "electricity_duty",
    "e d": "electricity_duty",
    "gst": "gst",
    "general sales tax": "gst",
    "sales tax": "gst",
    "quarterly tariff adjustment": "qta",
    "qtr tariff adjustment": "qta",
    "qta": "qta",
}


def is_surcharge(name: str) -> bool:
    """A levy added to the bill that GST applies to, e.g. "F.C surcharge".
    Late payment surcharge and tax-on-tax lines are not part of the supply.
    """
    # "L.P." normalises to two words, so rejoin it before checking.
    words = re.sub(r"\bl p\b", "lp", normalize_charge_name(name)).split()
    return "surcharge" in words and not {"late", "lp", "gst", "ed", "on"} & set(words)


def normalize_charge_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.strip().lower()).strip()
