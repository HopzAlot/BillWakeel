
from sqlalchemy.orm import Session

from models.db_models import Finding as FindingRecord
from models.db_models import Bill


def save_findings(
    db: Session,
    bill_id: str,
    findings: list,
    warnings: list[str] | None = None,
) -> list[FindingRecord] | None:
    """Replace findings and save response warnings for a bill."""

    bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()

    if bill is None:
        return None

    db.query(FindingRecord).filter(
        FindingRecord.bill_id == bill_id
    ).delete(synchronize_session="fetch")

    records = []

    for finding in findings:
        data = (
            finding.model_dump()
            if hasattr(finding, "model_dump")
            else finding
        )

        records.append(
            FindingRecord(
                bill_id=bill_id,
                **data,
            )
        )

    bill.warnings = warnings if warnings is not None else []

    db.add_all(records)
    db.commit()

    for record in records:
        db.refresh(record)

    return records


def get_findings(
    db: Session,
    bill_id: str,
) -> list[FindingRecord]:
    """Retrieve all findings associated with a bill."""

    return (
        db.query(FindingRecord)
        .filter(FindingRecord.bill_id == bill_id)
        .all()
    )


def get_bill_with_findings(
    db: Session,
    bill_id: str,
) -> Bill | None:
    """Retrieve a bill together with its extraction, warnings, and findings."""

    return db.query(Bill).filter(Bill.bill_id == bill_id).first()
