from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum, ForeignKey, Text, JSON, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates, declarative_base
from datetime import datetime, timezone
from uuid import uuid4
import enum
from database import Base
import re

class ClaimStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ADDITIONAL_INFO_REQUIRED = "ADDITIONAL_INFO_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"

class PolicyType(str, enum.Enum):
    AUTO = "AUTO"
    HEALTH = "HEALTH"
    PROPERTY = "PROPERTY"
    LIFE = "LIFE"

class PolicyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"

class Policyholder(Base):
    __tablename__ = 'policyholders'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = Column(String(100), nullable=False, server_default=None)
    last_name = Column(String(100), nullable=False, server_default=None)
    date_of_birth = Column(Date, nullable=False, server_default=None)
    email = Column(String(255), nullable=False, unique=True, server_default=None)
    phone = Column(String(20), nullable=False, server_default=None)
    alternate_phone = Column(String(20), server_default=None)
    street = Column(String(255), nullable=False, server_default=None)
    city = Column(String(100), nullable=False, server_default=None)
    state = Column(String(100), nullable=False, server_default=None)
    postal_code = Column(String(20), nullable=False, server_default=None)
    country = Column(String(100), nullable=False, server_default=None)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships with selectin loading
    policies = relationship("Policy", back_populates="policyholder", cascade="all, delete-orphan", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index('idx_policyholder_email', 'email'),
        Index('idx_policyholder_name', 'last_name', 'first_name'),
    )

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        return email

    @validates('phone', 'alternate_phone')
    def validate_phone(self, key, phone):
        if phone and not re.match(r"^\+?1?\d{9,15}$", phone):
            raise ValueError("Invalid phone number format")
        return phone

class Policy(Base):
    __tablename__ = 'policies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    policyholder_id = Column(UUID(as_uuid=True), ForeignKey('policyholders.id', ondelete='CASCADE'), nullable=False)
    policy_type = Column(Enum(PolicyType, native_enum=True), nullable=False)
    policy_number = Column(String(50), unique=True, nullable=False, server_default=None)
    start_date = Column(Date, nullable=False, server_default=None)
    end_date = Column(Date, nullable=False, server_default=None)
    coverage_amount = Column(Float(precision=2), nullable=False, server_default=None)
    premium = Column(Float(precision=2), nullable=False, server_default=None)
    deductible = Column(Float(precision=2), nullable=False, server_default=None)
    terms_and_conditions = Column(JSON, nullable=False, default={}, server_default='{}')
    status = Column(Enum(PolicyStatus, native_enum=True), default=PolicyStatus.PENDING)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships with selectin loading
    policyholder = relationship("Policyholder", back_populates="policies", lazy="selectin")
    claims = relationship("Claim", back_populates="policy", cascade="all, delete-orphan", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index('idx_policy_number', 'policy_number'),
        Index('idx_policy_dates', 'start_date', 'end_date'),
    )

    @validates('coverage_amount', 'premium', 'deductible')
    def validate_amounts(self, key, amount):
        if amount < 0:
            raise ValueError(f"{key} cannot be negative")
        return amount

    @validates('end_date')
    def validate_dates(self, key, end_date):
        if hasattr(self, 'start_date') and self.start_date and end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return end_date

class ClaimDocument(Base):
    __tablename__ = 'claim_documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False, server_default=None)
    document_type = Column(String(50), nullable=False, server_default=None)
    content_type = Column(String(100), nullable=False, server_default=None)
    size = Column(Integer, nullable=False, server_default=None)
    file_path = Column(String(512), nullable=False, server_default=None)
    upload_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    doc_metadata = Column(JSON, default={}, server_default='{}')

    # Relationships with selectin loading
    claim = relationship("Claim", back_populates="documents", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index('idx_document_claim', 'claim_id'),
    )

    @validates('size')
    def validate_size(self, key, size):
        if size <= 0:
            raise ValueError("Document size must be positive")
        return size

class Claim(Base):
    __tablename__ = 'claims'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey('policies.id', ondelete='CASCADE'), nullable=False)
    claim_number = Column(String(50), unique=True, nullable=False, server_default=None)
    incident_date = Column(DateTime(timezone=True), nullable=False, server_default=None)
    description = Column(Text, nullable=False, server_default=None)
    incident_description = Column(Text, nullable=False, server_default=None)
    amount_requested = Column(Float(precision=2), nullable=False, server_default=None)
    status = Column(Enum(ClaimStatus, native_enum=True), default=ClaimStatus.SUBMITTED)
    filing_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    assigned_adjuster_id = Column(UUID(as_uuid=True), server_default=None)
    settlement_amount = Column(Float(precision=2), server_default=None)
    settlement_date = Column(DateTime(timezone=True))
    notes = Column(JSON, default=list, server_default='[]')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships with selectin loading
    policy = relationship("Policy", back_populates="claims", lazy="selectin")
    documents = relationship("ClaimDocument", back_populates="claim", cascade="all, delete-orphan", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index('idx_claim_number', 'claim_number'),
        Index('idx_claim_status', 'status'),
        Index('idx_claim_dates', 'incident_date', 'filing_date'),
    )

    @validates('amount_requested', 'settlement_amount')
    def validate_amounts(self, key, amount):
        if amount is not None and amount < 0:
            raise ValueError(f"{key} cannot be negative")
        return amount

    @validates('incident_date')
    def validate_incident_date(self, key, incident_date):
        if incident_date > datetime.now(timezone.utc):
            raise ValueError("Incident date cannot be in the future")
        return incident_date