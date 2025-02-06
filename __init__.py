# Import core entities and new database models
from .models import (
    ClaimStatus,
    PolicyType,
    PolicyStatus,
    Policyholder,
    Policy,
    ClaimDocument,
    Claim
)

# Import repository classes
from .repository import PostgresRepository
from .database import get_session

# Import service
from .claims_service import ClaimsService

# Version info
__version__ = '0.2.0'

# Export all important components
__all__ = [
    # Enums
    'ClaimStatus',
    'PolicyType',
    'PolicyStatus',
    
    # Entity classes
    'Policyholder',
    'Policy',
    'ClaimDocument',
    'Claim',
    
    # Database
    'PostgresRepository',
    'get_session',
    
    # Service
    'ClaimsService',
]