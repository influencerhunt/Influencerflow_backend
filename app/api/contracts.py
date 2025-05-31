from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.services.contract_service import contract_service
from app.models.negotiation_models import ContractStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contracts", tags=["contracts"])

class SignContractRequest(BaseModel):
    signer_type: str = Field(..., pattern="^(brand|influencer)$", description="Type of signer: 'brand' or 'influencer'")
    signer_name: str = Field(..., min_length=1, description="Name of the person signing")
    signer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$', description="Email of the signer")

@router.get("/{contract_id}")
async def get_contract(contract_id: str) -> Dict[str, Any]:
    """Get contract details by ID"""
    contract = contract_service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    
    return contract_service.get_contract_summary(contract_id)

@router.get("/session/{session_id}")
async def get_contract_by_session(session_id: str) -> Dict[str, Any]:
    """Get contract by session ID"""
    contract = contract_service.get_contract_by_session(session_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"No contract found for session {session_id}")
    
    return contract_service.get_contract_summary(contract.contract_id)

@router.get("/{contract_id}/view")
async def view_contract_html(contract_id: str) -> Dict[str, Any]:
    """Get contract HTML content for viewing/printing"""
    try:
        html_content = contract_service.generate_contract_pdf_content(contract_id)
        contract = contract_service.get_contract(contract_id)
        
        return {
            "contract_id": contract_id,
            "html_content": html_content,
            "status": contract.status.value if contract else "unknown",
            "ready_for_signatures": contract.status == ContractStatus.PENDING_SIGNATURES if contract else False
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating contract HTML: {e}")
        raise HTTPException(status_code=500, detail="Error generating contract view")

@router.post("/{contract_id}/sign")
async def sign_contract(contract_id: str, request: SignContractRequest, http_request: Request) -> Dict[str, Any]:
    """Sign a contract digitally"""
    try:
        # Get IP address and user agent for signature verification
        ip_address = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")
        
        contract = contract_service.sign_contract(
            contract_id=contract_id,
            signer_type=request.signer_type,
            signer_name=request.signer_name,
            signer_email=request.signer_email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "message": f"Contract successfully signed by {request.signer_type}",
            "contract_id": contract_id,
            "status": contract.status.value,
            "fully_executed": contract.status == ContractStatus.FULLY_EXECUTED,
            "signatures": {
                "brand_signed": contract.brand_signature is not None,
                "influencer_signed": contract.influencer_signature is not None
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error signing contract {contract_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing signature")

@router.get("/{contract_id}/status")
async def get_contract_status(contract_id: str) -> Dict[str, Any]:
    """Get contract signature status"""
    contract = contract_service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    
    signatures_info = {}
    
    if contract.brand_signature:
        signatures_info["brand"] = {
            "signed": True,
            "signer_name": contract.brand_signature.signer_name,
            "signer_email": contract.brand_signature.signer_email,
            "signed_at": contract.brand_signature.signature_timestamp.isoformat()
        }
    else:
        signatures_info["brand"] = {"signed": False}
    
    if contract.influencer_signature:
        signatures_info["influencer"] = {
            "signed": True,
            "signer_name": contract.influencer_signature.signer_name,
            "signer_email": contract.influencer_signature.signer_email,
            "signed_at": contract.influencer_signature.signature_timestamp.isoformat()
        }
    else:
        signatures_info["influencer"] = {"signed": False}
    
    return {
        "contract_id": contract_id,
        "status": contract.status.value,
        "fully_executed": contract.status == ContractStatus.FULLY_EXECUTED,
        "signatures": signatures_info,
        "next_action": _get_next_action(contract)
    }

@router.get("/")
async def list_contracts() -> Dict[str, Any]:
    """List all contracts"""
    contracts = contract_service.list_contracts()
    
    return {
        "contracts": contracts,
        "total_count": len(contracts),
        "status_breakdown": _get_status_breakdown(contracts)
    }

def _get_next_action(contract) -> str:
    """Determine the next action needed for the contract"""
    if contract.status == ContractStatus.PENDING_SIGNATURES:
        if not contract.brand_signature and not contract.influencer_signature:
            return "Waiting for signatures from both parties"
        elif contract.brand_signature and not contract.influencer_signature:
            return "Waiting for influencer signature"
        elif not contract.brand_signature and contract.influencer_signature:
            return "Waiting for brand signature"
    elif contract.status == ContractStatus.FULLY_EXECUTED:
        return "Contract fully executed - campaign can begin"
    else:
        return f"Contract status: {contract.status.value.replace('_', ' ')}"

def _get_status_breakdown(contracts: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get breakdown of contract statuses"""
    status_count = {}
    for contract in contracts:
        status = contract["status"]
        status_count[status] = status_count.get(status, 0) + 1
    return status_count
