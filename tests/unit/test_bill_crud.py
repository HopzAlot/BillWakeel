import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base
from models.bill import BillExtraction, ChargeLine
from crud.bills import (
    create_bill,
    get_bill,
    save_extraction,
    get_extraction,
    delete_bill,
)


def test_bill_crud_operations():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    try:
        with TestSession() as db:
            # Create and retrieve bill
            create_bill(
                db, "test-001", "test.pdf",
                "application/pdf", 1024, "data/test.pdf"
            )
            bill = get_bill(db, "test-001")
            assert bill is not None
            assert bill.filename == "test.pdf"

            # Save and retrieve extraction
            extraction = BillExtraction(
                utility="electricity",
                provider="IESCO",
                units_consumed=125.5,
                charges=[
                    ChargeLine(
                        name="Electricity charges",
                        amount_pkr=2500.0
                    )
                ],
            )

            save_extraction(db, "test-001", extraction)
            saved = get_extraction(db, "test-001")

            assert saved["provider"] == "IESCO"
            assert saved["units_consumed"] == 125.5
            assert saved["charges"][0]["name"] == "Electricity charges"

            # Delete bill
            assert delete_bill(db, "test-001") is True
            assert get_bill(db, "test-001") is None
    finally:
        engine.dispose()
