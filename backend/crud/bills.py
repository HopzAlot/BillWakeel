from sqlalchemy.orm import Session

from models.db_models import Bill


def create_bill(
    db: Session,
    bill_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    file_path: str,
) -> Bill:
    """Create and persist a bill record."""
    bill = Bill(
        bill_id=bill_id,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        file_path=file_path,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def get_bill(db: Session, bill_id: str) -> Bill | None:
    """Fetch a bill by its ID."""
    return db.query(Bill).filter(Bill.bill_id == bill_id).first()


def save_extraction(db: Session, bill_id: str, extraction) -> Bill | None:
    """Save or replace a bill's Pydantic extraction as JSON."""
    bill = get_bill(db, bill_id)
    if bill is None:
        return None

    bill.extraction = extraction.model_dump(mode="json")
    db.commit()
    db.refresh(bill)
    return bill


def get_extraction(db: Session, bill_id: str) -> dict | None:
    """Fetch the stored extraction JSON for a bill."""
    bill = get_bill(db, bill_id)
    return bill.extraction if bill is not None else None


def delete_bill(db: Session, bill_id: str) -> bool:
    """Delete a bill record. Returns False if it does not exist."""
    bill = get_bill(db, bill_id)
    if bill is None:
        return False

    db.delete(bill)
    db.commit()
    return True

