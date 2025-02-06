import pytest
from datetime import datetime, date
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from models import Policy, Claim, PolicyType, ClaimStatus
from claims_service import ClaimsService
from database import get_session

@pytest.fixture
async def db_session():
    async with get_session() as session:
        yield session

@pytest.fixture
async def claims_service(db_session: AsyncSession):
    return ClaimsService(db_session)

@pytest.mark.asyncio
async def test_claim_submission(claims_service: ClaimsService):
    # Create test policy
    policy = Policy(
        policyholder_id=uuid4(),
        policy_type=PolicyType.AUTO,
        start_date=date(2024, 1, 1),
        end_date=date(2025, 1, 1),
        coverage_amount=50000.0,
        premium=1000.0,
        deductible=500.0,
        terms_and_conditions={}
    )
    created_policy = await claims_service.policies_repo.create(policy)
    
    # Test valid claim
    valid_claim = Claim(
        policy_id=created_policy.id,
        incident_date=datetime(2024, 6, 1),
        description="Valid claim",
        amount_requested=25000.0
    )
    created_claim = await claims_service.submit_claim(valid_claim)
    assert created_claim.status == ClaimStatus.SUBMITTED
    
    # Test invalid scenarios...