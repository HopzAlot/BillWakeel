
from sqlalchemy import Column, String, Integer, Float, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from db import Base


class Bill(Base):
    """Database record for an uploaded utility bill."""

    __tablename__ = "bills"

    bill_id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    extraction = Column(JSON, nullable=True)

    findings = relationship(
        "Finding",
        back_populates="bill",
        cascade="all, delete-orphan",
    )


class Finding(Base):
    """Database record for an individual tariff finding."""

    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(
        String,
        ForeignKey("bills.bill_id"),
        nullable=False,
        index=True,
    )

    charge_name = Column(String, nullable=False)
    billed_amount_pkr = Column(Float, nullable=False)
    expected_amount_pkr = Column(Float, nullable=False)
    difference_pkr = Column(Float, nullable=False)

    clause_id = Column(String, nullable=False)
    clause_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    source_url = Column(String, nullable=False)
    confidence = Column(String, nullable=False, default="high")

    bill = relationship("Bill", back_populates="findings")
