from uuid import UUID, uuid4
from datetime import datetime, timezone, date
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import (
    Claim, Policy, Policyholder, ClaimStatus, PolicyStatus,
    PolicyType, ClaimDocument
)
import schemas
from repository import PostgresRepository

class ClaimsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.claims_repo = PostgresRepository[Claim](session, Claim)
        self.policies_repo = PostgresRepository[Policy](session, Policy)
        self.policyholders_repo = PostgresRepository[Policyholder](session, Policyholder)
        self.documents_repo = PostgresRepository[ClaimDocument](session, ClaimDocument)

    async def create_policyholder(self, policyholder_data: schemas.PolicyholderCreate) -> Policyholder:
        try:
            new_policyholder = Policyholder(
                first_name=policyholder_data.first_name,
                last_name=policyholder_data.last_name,
                date_of_birth=policyholder_data.date_of_birth,
                email=policyholder_data.email,
                phone=policyholder_data.phone,
                alternate_phone=policyholder_data.alternate_phone,
                street=policyholder_data.street,
                city=policyholder_data.city,
                state=policyholder_data.state,
                postal_code=policyholder_data.postal_code,
                country=policyholder_data.country
            )
            
            if new_policyholder.date_of_birth >= date.today():
                raise ValueError("Invalid date of birth")
            
            created_policyholder = await self.policyholders_repo.create(new_policyholder)
            await self.session.commit()
            return created_policyholder
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to create policyholder: {str(e)}")

    async def get_policyholder(self, policyholder_id: UUID) -> Optional[Policyholder]:
        try:
            stmt = select(Policyholder).where(Policyholder.id == policyholder_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise ValueError(f"Failed to get policyholder: {str(e)}")

    async def update_policyholder(self, policyholder: Policyholder) -> Optional[Policyholder]:
        try:
            if policyholder.date_of_birth >= date.today():
                raise ValueError("Invalid date of birth")
            
            existing = await self.get_policyholder(policyholder.id)
            if not existing:
                return None
                
            policyholder.updated_at = datetime.now(timezone.utc)
            updated_policyholder = await self.policyholders_repo.update(policyholder)
            await self.session.commit()
            return updated_policyholder
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to update policyholder: {str(e)}")

    async def delete_policyholder(self, policyholder_id: UUID) -> bool:
        try:
            stmt = select(Policy).where(
                Policy.policyholder_id == policyholder_id,
                Policy.status == PolicyStatus.ACTIVE
            )
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("Cannot delete policyholder with active policies")
                
            deleted = await self.policyholders_repo.delete(policyholder_id)
            if deleted:
                await self.session.commit()
            return deleted
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to delete policyholder: {str(e)}")

    async def get_all_policyholders(self) -> List[Policyholder]:
        try:
            stmt = select(Policyholder)
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            raise ValueError(f"Failed to get policyholders: {str(e)}")

    async def create_policy(self, policy_data: schemas.PolicyCreate) -> Policy:
        try:
            policyholder = await self.get_policyholder(policy_data.policyholder_id)
            if not policyholder:
                raise ValueError("Policyholder not found")

            temp_id = uuid4()

            new_policy = Policy(
                id=temp_id,
                policyholder_id=policy_data.policyholder_id,
                policy_type=policy_data.policy_type,
                start_date=policy_data.start_date,
                end_date=policy_data.end_date,
                coverage_amount=policy_data.coverage_amount,
                premium=policy_data.premium,
                deductible=policy_data.deductible,
                status=PolicyStatus.ACTIVE,
                policy_number=f"POL-{str(temp_id)[:8]}"
            )

            if new_policy.start_date >= new_policy.end_date:
                raise ValueError("End date must be after start date")
                
            if new_policy.coverage_amount <= 0 or new_policy.premium <= 0:
                raise ValueError("Coverage amount and premium must be positive")
            if new_policy.deductible < 0:
                raise ValueError("Deductible cannot be negative")

            created_policy = await self.policies_repo.create(new_policy)
            await self.session.commit()
            return created_policy
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to create policy: {str(e)}")

    async def get_policy(self, policy_id: UUID) -> Optional[Policy]:
        try:
            stmt = select(Policy).where(Policy.id == policy_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise ValueError(f"Failed to get policy: {str(e)}")

    async def update_policy(self, policy_data: schemas.PolicyUpdate) -> Optional[Policy]:
        try:
            existing = await self.get_policy(policy_data.id)
            if not existing:
                return None

            for field, value in policy_data.dict(exclude_unset=True).items():
                setattr(existing, field, value)

            if existing.start_date >= existing.end_date:
                raise ValueError("End date must be after start date")
                
            existing.updated_at = datetime.now(timezone.utc)
            updated_policy = await self.policies_repo.update(existing)
            await self.session.commit()
            return updated_policy
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to update policy: {str(e)}")

    async def delete_policy(self, policy_id: UUID) -> bool:
        try:
            stmt = select(Claim).where(
                Claim.policy_id == policy_id,
                Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW])
            )
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("Cannot delete policy with active claims")
                
            deleted = await self.policies_repo.delete(policy_id)
            if deleted:
                await self.session.commit()
            return deleted
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to delete policy: {str(e)}")

    async def get_all_policies(self) -> List[Policy]:
        try:
            stmt = select(Policy)
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            raise ValueError(f"Failed to get policies: {str(e)}")

    async def submit_claim(self, claim_data: schemas.ClaimCreate) -> schemas.ClaimResponse:
        try:
            # Get policy using repository
            stmt = select(Policy).where(Policy.id == claim_data.policy_id)
            policy = await self.session.execute(stmt)
            policy = policy.scalar_one_or_none()
            
            if not policy:
                raise ValueError(f"Policy with ID {claim_data.policy_id} not found")
                
            if policy.status != PolicyStatus.ACTIVE:
                raise ValueError(f"Policy {policy.policy_number} is not active. Current status: {policy.status}")
            temp_id = uuid4()
            
            # Create new claim instance
            new_claim = Claim(
                id=temp_id,
                policy_id=claim_data.policy_id,
                claim_number=f"CLM-{str(temp_id)[:8]}",
                incident_date=claim_data.incident_date,
                description=claim_data.description,
                incident_description=claim_data.incident_description,
                amount_requested=claim_data.amount_requested,
                status=ClaimStatus.SUBMITTED,
                filing_date=datetime.now(timezone.utc)
            )
            # Timezone validation
            if new_claim.incident_date.tzinfo is None:
                new_claim.incident_date = new_claim.incident_date.replace(tzinfo=timezone.utc)
            # Policy period validation
            policy_start = datetime.combine(policy.start_date, datetime.min.time(), tzinfo=timezone.utc)
            policy_end = datetime.combine(policy.end_date, datetime.max.time(), tzinfo=timezone.utc)
            
            if not (policy_start <= new_claim.incident_date <= policy_end):
                raise ValueError(
                    f"Claim incident date ({new_claim.incident_date.date()}) must be within policy period "
                    f"({policy.start_date} to {policy.end_date})"
                )
            # Amount validations
            if new_claim.amount_requested <= 0:
                raise ValueError("Claim amount must be positive")
                
            if new_claim.amount_requested > policy.coverage_amount:
                raise ValueError(
                    f"Claim amount ({new_claim.amount_requested}) exceeds policy coverage ({policy.coverage_amount})"
                )
            # Description validations
            if not new_claim.description or len(new_claim.description.strip()) == 0:
                raise ValueError("Description is required")
                
            if not new_claim.incident_description or len(new_claim.incident_description.strip()) == 0:
                raise ValueError("Incident description is required")
            # Create the claim using repository
            created_claim = await self.claims_repo.create(new_claim)
            
            # Commit the transaction
            await self.session.commit()
            
            # Get associated documents
            documents = await self.get_claim_documents(created_claim.id)
            created_claim.documents = documents
            
            return schemas.ClaimResponse.from_orm(created_claim)
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Database error while creating claim: {str(e)}")

    async def process_claim(self, claim_id: UUID, process_data: schemas.ClaimProcess) -> Optional[Claim]:
        try:
            claim = await self.get_claim(claim_id)
            if not claim:
                return None

            if process_data.new_status == ClaimStatus.UNDER_REVIEW:
                if not process_data.adjuster_id:
                    raise ValueError("Adjuster ID required for claims under review")
                claim.assigned_adjuster_id = process_data.adjuster_id

            if process_data.new_status == ClaimStatus.SETTLED and claim.status != ClaimStatus.APPROVED:
                raise ValueError("Cannot settle unapproved claim")

            claim.status = process_data.new_status
            claim.updated_at = datetime.now(timezone.utc)

            if process_data.new_status == ClaimStatus.SETTLED:
                claim.settlement_date = datetime.now(timezone.utc)

            updated_claim = await self.claims_repo.update(claim)
            await self.session.commit()
            return updated_claim
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to process claim: {str(e)}")

    async def get_claim(self, claim_id: UUID) -> Optional[Claim]:
        try:
            stmt = select(Claim).where(Claim.id == claim_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise ValueError(f"Failed to get claim: {str(e)}")

    async def delete_claim(self, claim_id: UUID) -> bool:
        try:
            claim = await self.get_claim(claim_id)
            if not claim:
                return False
                
            if claim.status not in [ClaimStatus.REJECTED, ClaimStatus.SETTLED]:
                raise ValueError("Can only delete rejected or settled claims")
                
            deleted = await self.claims_repo.delete(claim_id)
            if deleted:
                await self.session.commit()
            return deleted
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to delete claim: {str(e)}")

    async def get_all_claims(self) -> List[Claim]:
        try:
            stmt = select(Claim)
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            raise ValueError(f"Failed to get claims: {str(e)}")

    async def add_claim_document(self, document_data: schemas.ClaimDocumentCreate) -> ClaimDocument:
        try:
            claim = await self.get_claim(document_data.claim_id)
            if not claim:
                raise ValueError("Claim not found")
                
            new_document = ClaimDocument(
                claim_id=document_data.claim_id,
                document_type=document_data.document_type,
                file_name=document_data.file_name,
                file_path=document_data.file_path,
                uploaded_by=document_data.uploaded_by
            )
            
            created_document = await self.documents_repo.create(new_document)
            await self.session.commit()
            return created_document
            
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Failed to add claim document: {str(e)}")

    async def get_claim_documents(self, claim_id: UUID) -> List[ClaimDocument]:
        try:
            stmt = select(ClaimDocument).where(ClaimDocument.claim_id == claim_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            raise ValueError(f"Failed to get claim documents: {str(e)}")