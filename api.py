from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

import schemas
from database import get_db_session
from claims_service import ClaimsService

# Add logging configuration
import logging
logging.basicConfig(level=logging.DEBUG)

# Create RootResponse model
class RootResponse(BaseModel):
    title: str
    version: str
    description: str
    endpoints: dict[str, str]

app = FastAPI(
    title="Claims Management System API",
    description="API for managing insurance claims, policies, and policyholders",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from your frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Dependency to get ClaimsService
async def get_claims_service(session: AsyncSession = Depends(get_db_session)):
    return ClaimsService(session)

# Root endpoint with proper response model
@app.get("/", response_model=RootResponse, tags=["Root"])
async def root() -> RootResponse:
    return RootResponse(
        title="Claims Management System API",
        version="1.0.0",
        description="API for managing insurance claims and policies",
        endpoints={
            "policies": "/policies/",
            "policyholders": "/policyholders/",
            "claims": "/claims/",
            "health": "/health",
            "documentation": "/docs"
        }
    )

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Policyholder endpoints
@app.post("/policyholders/", response_model=schemas.PolicyholderResponse, 
          status_code=status.HTTP_201_CREATED, tags=["Policyholders"])
async def create_policyholder(
    policyholder: schemas.PolicyholderCreate,
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        result = await claims_service.create_policyholder(policyholder)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policyholders/{policyholder_id}", response_model=schemas.PolicyholderResponse, 
         tags=["Policyholders"])
async def get_policyholder(
    policyholder_id: UUID,
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        policyholder = await claims_service.get_policyholder(policyholder_id)
        if not policyholder:
            raise HTTPException(status_code=404, detail="Policyholder not found")
        return policyholder
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policyholders/", response_model=List[schemas.PolicyholderResponse], 
         tags=["Policyholders"])
async def list_policyholders(
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        return await claims_service.get_all_policyholders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Policy endpoints
@app.post("/policies/", response_model=schemas.PolicyResponse, 
          status_code=status.HTTP_201_CREATED, tags=["Policies"])
async def create_policy(
    policy: schemas.PolicyCreate,
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        result = await claims_service.create_policy(policy)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policies/{policy_id}", response_model=schemas.PolicyResponse, 
         tags=["Policies"])
async def get_policy(
    policy_id: UUID,
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        policy = await claims_service.get_policy(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policies/", response_model=List[schemas.PolicyResponse], 
         tags=["Policies"])
async def list_policies(
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        return await claims_service.get_all_policies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Claims endpoints
@app.post("/claims/", response_model=schemas.ClaimResponse, 
          status_code=status.HTTP_201_CREATED, tags=["Claims"])
async def submit_claim(
    claim: schemas.ClaimCreate,
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        result = await claims_service.submit_claim(claim)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/claims/{claim_id}", response_model=schemas.ClaimResponse, 
         tags=["Claims"])
async def get_claim(
    claim_id: UUID,
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        claim = await claims_service.get_claim(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        return claim
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/claims/", response_model=List[schemas.ClaimResponse], 
         tags=["Claims"])
async def list_claims(
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        return await claims_service.get_all_claims()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/claims/{claim_id}/status", response_model=schemas.ClaimResponse, 
         tags=["Claims"])
async def update_claim_status(
    claim_id: UUID,
    status_update: schemas.ClaimStatusUpdate,
    claims_service: ClaimsService = Depends(get_claims_service)
):
    try:
        updated = await claims_service.process_claim(
            claim_id, 
            status_update.status,
            status_update.adjuster_id
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Claim not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)