#schemas.py
from pydantic import BaseModel, Field, EmailStr, UUID4, validator
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum
import pytz

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

# Base Models
class PolicyholderBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: EmailStr
    phone: str = Field(pattern=r"^\+?1?\d{9,15}$")
    alternate_phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    street: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)

    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        if v >= date.today():
            raise ValueError("Birth date cannot be in the future")
        return v

class PolicyBase(BaseModel):
    policyholder_id: UUID4
    policy_type: PolicyType
    start_date: date
    end_date: date
    coverage_amount: float
    premium: float
    deductible: float
    terms_and_conditions: Dict[str, Any] = Field(default_factory=dict)
    status: PolicyStatus = PolicyStatus.PENDING

    @validator('coverage_amount', 'premium', 'deductible')
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v

# Document Models
class ClaimDocumentBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    document_type: str = Field(min_length=1, max_length=50)
    content_type: str = Field(min_length=1, max_length=100)
    size: int = Field(gt=0)
    file_path: str = Field(min_length=1, max_length=512)
    doc_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True

# Request Models
class PolicyholderCreate(PolicyholderBase):
    pass

class PolicyholderUpdate(PolicyholderBase):
    pass

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    id: UUID4
    policy_type: Optional[PolicyType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    coverage_amount: Optional[float] = None
    premium: Optional[float] = None
    deductible: Optional[float] = None
    terms_and_conditions: Optional[Dict[str, Any]] = None
    status: Optional[PolicyStatus] = None

    @validator('coverage_amount', 'premium', 'deductible')
    def validate_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError("Amount cannot be negative")
        return v

    @validator('end_date')
    def validate_dates(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v

    class Config:
        from_attributes = True

class ClaimCreate(BaseModel):
    policy_id: UUID4
    incident_date: datetime
    description: str = Field(min_length=1)
    incident_description: str = Field(min_length=1, max_length=1000)
    amount_requested: float

    @validator('amount_requested')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount requested must be positive")
        return v

    @validator('incident_date')
    def validate_incident_date(cls, v):
        now = datetime.now(pytz.UTC)
        incident_date = v.astimezone(pytz.UTC) if v.tzinfo else pytz.UTC.localize(v)
        if incident_date > now:
            raise ValueError("Incident date cannot be in the future")
        return incident_date

class ClaimDocumentCreate(ClaimDocumentBase):
    pass

# Response Models
class PolicyholderResponse(PolicyholderBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PolicyResponse(PolicyBase):
    id: UUID4
    policy_number: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClaimDocumentResponse(ClaimDocumentBase):
    id: UUID4
    claim_id: UUID4
    upload_date: datetime

    class Config:
        from_attributes = True

class ClaimResponse(BaseModel):
    id: UUID4
    policy_id: UUID4
    claim_number: str
    incident_date: datetime
    description: str
    incident_description: str
    amount_requested: float
    status: ClaimStatus
    filing_date: datetime
    assigned_adjuster_id: Optional[UUID4] = None
    settlement_amount: Optional[float] = None
    settlement_date: Optional[datetime] = None
    notes: List[str] = []
    created_at: datetime
    updated_at: datetime
    documents: List[ClaimDocumentResponse] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class ClaimStatusUpdate(BaseModel):
    status: ClaimStatus
    adjuster_id: Optional[UUID4] = None

class ClaimProcess(BaseModel):
    new_status: ClaimStatus
    adjuster_id: Optional[UUID4] = None
    notes: Optional[str] = None
    settlement_amount: Optional[float] = None

    @validator('settlement_amount')
    def validate_settlement_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError("Settlement amount cannot be negative")
        return v

    class Config:
        from_attributes = True