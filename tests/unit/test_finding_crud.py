
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db import Base
from models.db_models import Bill, Finding
from crud.bills import create_bill
from crud.findings import (
    save_findings,
    get_findings,
    get_bill_with_findings,
)


def test_finding_crud_operations():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    try:
        with TestSession() as db:
            # Create a bill
            create_bill(
                db,
                "finding-test-001",
                "test.pdf",
                "application/pdf",
                1024,
                "data/test.pdf",
            )

            # Prepare findings using Rehan's exact schema fields
            findings = [
                {
                    "charge_name": "Electricity charges",
                    "billed_amount_pkr": 3000.0,
                    "expected_amount_pkr": 2500.0,
                    "difference_pkr": 500.0,
                    "clause_id": "CLAUSE-01",
                    "clause_text": "Test tariff clause",
                    "explanation": "The billed amount exceeds the expected amount.",
                    "source_url": "https://example.com/tariff",
                    "confidence": "high",
                },
                {
                    "charge_name": "Fuel adjustment",
                    "billed_amount_pkr": 1000.0,
                    "expected_amount_pkr": 800.0,
                    "difference_pkr": 200.0,
                    "clause_id": "CLAUSE-02",
                    "clause_text": "Another test tariff clause",
                    "explanation": "The charge differs from the expected amount.",
                    "source_url": "https://example.com/tariff",
                    "confidence": "medium",
                },
            ]

            # Save findings
            saved = save_findings(db, "finding-test-001", findings)

            assert saved is not None
            assert len(saved) == 2

            # Retrieve findings
            retrieved = get_findings(db, "finding-test-001")

            assert len(retrieved) == 2
            assert retrieved[0].charge_name == "Electricity charges"
            assert retrieved[0].difference_pkr == 500.0
            assert retrieved[1].confidence == "medium"

            # Retrieve bill with its findings
            bill = get_bill_with_findings(db, "finding-test-001")

            assert bill is not None
            assert len(bill.findings) == 2

            # Saving again should replace old findings
            save_findings(db, "finding-test-001", [findings[0]])

            updated = get_findings(db, "finding-test-001")
            assert len(updated) == 1
            assert updated[0].charge_name == "Electricity charges"

            # Non-existent bill should return None
            assert save_findings(db, "missing-bill", findings) is None

    finally:
        engine.dispose()
