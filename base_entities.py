from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, date, timezone



class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ADDITIONAL_INFO_REQUIRED = "ADDITIONAL_INFO_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"

class PolicyType(str, Enum):
    AUTO = "AUTO"
    HEALTH = "HEALTH"
    PROPERTY = "PROPERTY"
    LIFE = "LIFE"

class PolicyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"

# Value Objects
class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str

    def validate(self):
        if not all([self.street, self.city, self.state, self.postal_code, self.country]):
            raise ValueError("All address fields are required")
        if not isinstance(self.postal_code, str) or not self.postal_code.strip():
            raise ValueError("Invalid postal code")

class Contact(BaseModel):
    email: str
    phone: str
    alternate_phone: Optional[str] = None

    def validate(self):
        if '@' not in self.email or '.' not in self.email:
            raise ValueError("Invalid email format")
        if not self.phone.strip():
            raise ValueError("Phone number is required")

# Core Entities
class Policyholder(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    date_of_birth: date
    contact: Contact
    address: Address
    policies: List[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def validate(self):
        if not all([self.first_name, self.last_name]):
            raise ValueError("First name and last name are required")
        if self.date_of_birth >= date.today():
            raise ValueError("Invalid date of birth")
        self.contact.validate()
        self.address.validate()

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

class Policy(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    policyholder_id: UUID
    policy_type: PolicyType
    start_date: date
    end_date: date
    coverage_amount: float
    premium: float
    deductible: float
    terms_and_conditions: Dict[str, Any]
    policy_number: Optional[str] = None
    status: PolicyStatus = PolicyStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __init__(self, **data):
        super().__init__(**data)
        if not self.policy_number:
            self.policy_number = f"POL-{str(self.id)[:8]}"
        self.validate()

    def validate(self):
        if self.start_date >= self.end_date:
            raise ValueError("End date must be after start date")
        if self.coverage_amount <= 0 or self.premium <= 0:
            raise ValueError("Coverage amount and premium must be positive")
        if self.deductible < 0:
            raise ValueError("Deductible cannot be negative")

class ClaimDocument(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    document_type: str
    content_type: str
    size: int
    file_path: str
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def validate(self):
        if not all([self.name, self.document_type, self.content_type, self.file_path]):
            raise ValueError("All document fields are required")
        if self.size <= 0:
            raise ValueError("Document size must be positive")

class Claim(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    policy_id: UUID
    incident_date: datetime
    description: str
    amount_requested: float
    claim_number: Optional[str] = None
    filing_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ClaimStatus = ClaimStatus.SUBMITTED
    documents: List[ClaimDocument] = Field(default_factory=list)
    assigned_adjuster_id: Optional[UUID] = None
    settlement_amount: Optional[float] = None
    settlement_date: Optional[datetime] = None
    notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __init__(self, **data):
        super().__init__(**data)
        if not self.claim_number:
            self.claim_number = f"CLM-{str(self.id)[:8]}"
        self.validate()

    def validate(self):
        # Ensure incident_date has timezone info
        if self.incident_date.tzinfo is None:
            self.incident_date = self.incident_date.replace(tzinfo=timezone.utc)
            
        # Compare with current time in UTC
        current_time = datetime.now(timezone.utc)
        if self.incident_date > current_time:
            raise ValueError("Incident date cannot be in the future")
            
        if self.amount_requested <= 0:
            raise ValueError("Claim amount must be positive")
        if self.settlement_amount is not None and self.settlement_amount < 0:
            raise ValueError("Settlement amount cannot be negative")
        if not self.description.strip():
            raise ValueError("Claim description is required")