"""
Comprehensive Supabase Manager for Negotiation Agent Logging
Handles all Supabase operations for negotiation data, contracts, and analytics
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
import uuid

from app.services.supabase import SupabaseService
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, LocationType, 
    NegotiationStatus, ContentType
)

logger = logging.getLogger(__name__)

@dataclass
class NegotiationLogEntry:
    """Log entry for negotiation operations"""
    id: str
    session_id: str
    operation: str
    operation_type: str  # 'start', 'continue', 'deliverable_update', 'budget_change', 'contract_generation'
    user_input: Optional[str] = None
    agent_response: Optional[str] = None
    brand_details: Optional[Dict] = None
    influencer_profile: Optional[Dict] = None
    deliverables: Optional[List[Dict]] = None
    budget_info: Optional[Dict] = None
    contract_id: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.id is None:
            self.id = str(uuid.uuid4())

class SupabaseManager:
    """Comprehensive Supabase manager for negotiation agent operations"""
    
    def __init__(self):
        self.supabase_service = SupabaseService()
        
    # ==================== CORE LOGGING METHODS ====================
    
    async def log_negotiation_operation(
        self,
        session_id: str,
        operation: str,
        operation_type: str,
        user_input: Optional[str] = None,
        agent_response: Optional[str] = None,
        brand_details: Optional[BrandDetails] = None,
        influencer_profile: Optional[InfluencerProfile] = None,
        deliverables: Optional[List[Dict]] = None,
        budget_info: Optional[Dict] = None,
        contract_id: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Log any negotiation operation to Supabase"""
        try:
            log_entry = NegotiationLogEntry(
                id=str(uuid.uuid4()),
                session_id=session_id,
                operation=operation,
                operation_type=operation_type,
                user_input=user_input,
                agent_response=agent_response,
                brand_details=asdict(brand_details) if brand_details else None,
                influencer_profile=asdict(influencer_profile) if influencer_profile else None,
                deliverables=deliverables,
                budget_info=budget_info,
                contract_id=contract_id,
                status=status,
                metadata=metadata or {}
            )
            
            # Insert into negotiation_operations table
            data = asdict(log_entry)
            data['timestamp'] = log_entry.timestamp.isoformat()
            
            result = await self.supabase_service.insert_data("negotiation_operations", data)
            
            logger.info(f"Logged negotiation operation: {operation} for session {session_id}")
            return log_entry.id
            
        except Exception as e:
            logger.error(f"Failed to log negotiation operation: {e}")
            raise

    async def log_conversation_message(
        self,
        session_id: str,
        message_type: str,  # 'user' or 'agent'
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Log individual conversation messages"""
        try:
            message_data = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "message_type": message_type,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self.supabase_service.insert_data("conversation_messages", message_data)
            
            logger.info(f"Logged {message_type} message for session {session_id}")
            return message_data["id"]
            
        except Exception as e:
            logger.error(f"Failed to log conversation message: {e}")
            raise

    # ==================== SESSION MANAGEMENT ====================
    
    async def create_negotiation_session(
        self,
        session_id: str,
        brand_details: BrandDetails,
        influencer_profile: InfluencerProfile,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new negotiation session"""
        try:
            session_data = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "user_id": user_id,
                "brand_details": asdict(brand_details),
                "influencer_profile": asdict(influencer_profile),
                "status": "initiated",
                "negotiation_round": 1,
                "current_offer": None,
                "counter_offers": [],
                "agreed_terms": None,
                "conversation_history": [],
                "deliverables": [],
                "payment_terms": None,
                "contract_terms": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True,
                "metadata": {}
            }
            
            result = await self.supabase_service.insert_data("negotiation_sessions", session_data)
            
            # Log the session creation
            await self.log_negotiation_operation(
                session_id=session_id,
                operation="session_created",
                operation_type="start",
                brand_details=brand_details,
                influencer_profile=influencer_profile,
                status="initiated"
            )
            
            logger.info(f"Created negotiation session: {session_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create negotiation session: {e}")
            raise

    async def update_negotiation_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update negotiation session"""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = await self.supabase_service.update_data(
                "negotiation_sessions",
                updates,
                {"session_id": session_id}
            )
            
            logger.info(f"Updated negotiation session: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update negotiation session: {e}")
            raise

    async def get_negotiation_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get negotiation session by ID"""
        try:
            result = await self.supabase_service.fetch_data(
                "negotiation_sessions",
                {"session_id": session_id}
            )
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to get negotiation session: {e}")
            return None

    # ==================== DELIVERABLES MANAGEMENT ====================
    
    async def save_deliverables(
        self,
        session_id: str,
        deliverables: List[Dict[str, Any]]
    ) -> bool:
        """Save deliverables for a session"""
        try:
            # Update session with deliverables
            await self.update_negotiation_session(
                session_id,
                {"deliverables": deliverables}
            )
            
            # Log deliverables update
            await self.log_negotiation_operation(
                session_id=session_id,
                operation="deliverables_updated",
                operation_type="deliverable_update",
                deliverables=deliverables,
                metadata={"deliverable_count": len(deliverables)}
            )
            
            logger.info(f"Saved {len(deliverables)} deliverables for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save deliverables: {e}")
            return False

    async def get_deliverables(self, session_id: str) -> List[Dict[str, Any]]:
        """Get deliverables for a session"""
        try:
            session = await self.get_negotiation_session(session_id)
            return session.get("deliverables", []) if session else []
            
        except Exception as e:
            logger.error(f"Failed to get deliverables: {e}")
            return []

    # ==================== BUDGET MANAGEMENT ====================
    
    async def log_budget_change(
        self,
        session_id: str,
        old_budget: float,
        new_budget: float,
        currency: str,
        change_reason: str
    ) -> bool:
        """Log budget changes"""
        try:
            budget_info = {
                "old_budget": old_budget,
                "new_budget": new_budget,
                "currency": currency,
                "change_amount": new_budget - old_budget,
                "change_percentage": ((new_budget - old_budget) / old_budget) * 100 if old_budget > 0 else 0,
                "change_reason": change_reason
            }
            
            await self.log_negotiation_operation(
                session_id=session_id,
                operation="budget_changed",
                operation_type="budget_change",
                budget_info=budget_info,
                metadata={"change_reason": change_reason}
            )
            
            logger.info(f"Logged budget change for session {session_id}: {old_budget} -> {new_budget} {currency}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log budget change: {e}")
            return False

    # ==================== CONTRACT MANAGEMENT ====================
    
    async def save_contract(
        self,
        session_id: str,
        contract_id: str,
        contract_data: Dict[str, Any]
    ) -> bool:
        """Save contract information"""
        try:
            contract_record = {
                "id": str(uuid.uuid4()),
                "contract_id": contract_id,
                "session_id": session_id,
                "contract_data": contract_data,
                "status": "pending_signatures",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = await self.supabase_service.insert_data("contracts", contract_record)
            
            # Update session with contract ID
            await self.update_negotiation_session(
                session_id,
                {"contract_id": contract_id, "status": "contract_generated"}
            )
            
            # Log contract generation
            await self.log_negotiation_operation(
                session_id=session_id,
                operation="contract_generated",
                operation_type="contract_generation",
                contract_id=contract_id,
                metadata={"contract_amount": contract_data.get("total_amount")}
            )
            
            logger.info(f"Saved contract {contract_id} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save contract: {e}")
            return False

    async def upload_contract_pdf(
        self,
        contract_id: str,
        pdf_bytes: bytes,
        filename: str
    ) -> Optional[str]:
        """Upload contract PDF to Supabase storage"""
        try:
            # Upload to Supabase storage
            file_path = f"contracts/{contract_id}/{filename}"
            storage_url = await self.supabase_service.upload_file(
                bucket="contracts",
                file_path=file_path,
                file_data=pdf_bytes,
                content_type="application/pdf"
            )
            
            if storage_url:
                # Update contract record with PDF URL
                await self.supabase_service.update_data(
                    "contracts",
                    {"pdf_url": storage_url, "updated_at": datetime.utcnow().isoformat()},
                    {"contract_id": contract_id}
                )
                
                logger.info(f"Uploaded contract PDF for {contract_id}")
                return storage_url
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to upload contract PDF: {e}")
            return None

    # ==================== ANALYTICS & REPORTING ====================
    
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a specific session"""
        try:
            # Get session data
            session = await self.get_negotiation_session(session_id)
            if not session:
                return {}
            
            # Get operation logs
            operations = await self.supabase_service.fetch_data(
                "negotiation_operations",
                {"session_id": session_id}
            )
            
            # Get conversation messages
            messages = await self.supabase_service.fetch_data(
                "conversation_messages",
                {"session_id": session_id}
            )
            
            analytics = {
                "session_id": session_id,
                "status": session.get("status"),
                "created_at": session.get("created_at"),
                "duration_hours": self._calculate_session_duration(session),
                "negotiation_rounds": session.get("negotiation_round", 0),
                "total_operations": len(operations),
                "total_messages": len(messages),
                "user_messages": len([m for m in messages if m.get("message_type") == "user"]),
                "agent_messages": len([m for m in messages if m.get("message_type") == "agent"]),
                "operations_breakdown": self._analyze_operations(operations),
                "budget_changes": len([op for op in operations if op.get("operation_type") == "budget_change"]),
                "deliverable_updates": len([op for op in operations if op.get("operation_type") == "deliverable_update"]),
                "has_contract": session.get("contract_id") is not None,
                "brand_name": session.get("brand_details", {}).get("name"),
                "influencer_name": session.get("influencer_profile", {}).get("name")
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get session analytics: {e}")
            return {}

    async def get_global_analytics(self) -> Dict[str, Any]:
        """Get global analytics across all sessions"""
        try:
            # Get all sessions
            sessions = await self.supabase_service.fetch_data("negotiation_sessions", {})
            
            # Get all operations
            operations = await self.supabase_service.fetch_data("negotiation_operations", {})
            
            # Get all contracts
            contracts = await self.supabase_service.fetch_data("contracts", {})
            
            analytics = {
                "total_sessions": len(sessions),
                "active_sessions": len([s for s in sessions if s.get("is_active", True)]),
                "completed_sessions": len([s for s in sessions if s.get("status") == "agreed"]),
                "cancelled_sessions": len([s for s in sessions if s.get("status") == "cancelled"]),
                "total_operations": len(operations),
                "total_contracts": len(contracts),
                "operations_by_type": self._group_operations_by_type(operations),
                "sessions_by_status": self._group_sessions_by_status(sessions),
                "average_negotiation_rounds": self._calculate_average_rounds(sessions),
                "success_rate": self._calculate_success_rate(sessions)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get global analytics: {e}")
            return {}

    # ==================== UTILITY METHODS ====================
    
    async def archive_session(self, session_id: str) -> bool:
        """Archive a negotiation session"""
        try:
            await self.update_negotiation_session(
                session_id,
                {"is_active": False, "archived_at": datetime.utcnow().isoformat()}
            )
            
            await self.log_negotiation_operation(
                session_id=session_id,
                operation="session_archived",
                operation_type="archive",
                status="archived"
            )
            
            logger.info(f"Archived session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive session: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete a negotiation session and all related data"""
        try:
            # Delete related data first
            await self.supabase_service.delete_data("negotiation_operations", {"session_id": session_id})
            await self.supabase_service.delete_data("conversation_messages", {"session_id": session_id})
            await self.supabase_service.delete_data("contracts", {"session_id": session_id})
            
            # Delete session
            await self.supabase_service.delete_data("negotiation_sessions", {"session_id": session_id})
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active negotiation sessions"""
        try:
            sessions = await self.supabase_service.fetch_data(
                "negotiation_sessions",
                {"is_active": True}
            )
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list active sessions: {e}")
            return []

    # ==================== PRIVATE HELPER METHODS ====================
    
    def _calculate_session_duration(self, session: Dict[str, Any]) -> float:
        """Calculate session duration in hours"""
        try:
            created_at = datetime.fromisoformat(session.get("created_at", "").replace("Z", "+00:00"))
            updated_at = datetime.fromisoformat(session.get("updated_at", "").replace("Z", "+00:00"))
            duration = updated_at - created_at
            return duration.total_seconds() / 3600
        except:
            return 0.0

    def _analyze_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze operations breakdown"""
        breakdown = {}
        for op in operations:
            op_type = op.get("operation_type", "unknown")
            breakdown[op_type] = breakdown.get(op_type, 0) + 1
        return breakdown

    def _group_operations_by_type(self, operations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group operations by type"""
        return self._analyze_operations(operations)

    def _group_sessions_by_status(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group sessions by status"""
        breakdown = {}
        for session in sessions:
            status = session.get("status", "unknown")
            breakdown[status] = breakdown.get(status, 0) + 1
        return breakdown

    def _calculate_average_rounds(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate average negotiation rounds"""
        if not sessions:
            return 0.0
        
        total_rounds = sum(session.get("negotiation_round", 0) for session in sessions)
        return total_rounds / len(sessions)

    def _calculate_success_rate(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate success rate (percentage of agreed sessions)"""
        if not sessions:
            return 0.0
        
        agreed_sessions = len([s for s in sessions if s.get("status") == "agreed"])
        return (agreed_sessions / len(sessions)) * 100

# Decorator for automatic logging
def log_to_supabase(operation_name: str, operation_type: str):
    """Decorator to automatically log operations to Supabase"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract session_id from function arguments
            session_id = None
            
            # Try to find session_id in various locations
            if 'session_id' in kwargs:
                session_id = kwargs['session_id']
            elif len(args) > 0:
                # Check if first argument has session_id attribute (request object)
                first_arg = args[0]
                if hasattr(first_arg, 'session_id'):
                    session_id = first_arg.session_id
                # Check if it's a direct session_id string
                elif isinstance(first_arg, str):
                    session_id = first_arg
            elif len(args) > 1 and isinstance(args[1], str):
                session_id = args[1]
            
            # Execute the function
            try:
                result = await func(*args, **kwargs)
                
                # Log successful operation (only if we found a session_id)
                if session_id:
                    try:
                        supabase_manager = SupabaseManager()
                        await supabase_manager.log_negotiation_operation(
                            session_id=session_id,
                            operation=operation_name,
                            operation_type=operation_type,
                            status="success",
                            metadata={"function": func.__name__}
                        )
                    except Exception as log_error:
                        # Don't fail the main operation if logging fails
                        logger.warning(f"Failed to log operation: {log_error}")
                
                return result
                
            except Exception as e:
                # Log failed operation (only if we found a session_id)
                if session_id:
                    try:
                        supabase_manager = SupabaseManager()
                        await supabase_manager.log_negotiation_operation(
                            session_id=session_id,
                            operation=operation_name,
                            operation_type=operation_type,
                            status="error",
                            metadata={"function": func.__name__, "error": str(e)}
                        )
                    except Exception as log_error:
                        # Don't fail the main operation if logging fails
                        logger.warning(f"Failed to log error: {log_error}")
                raise
        
        return wrapper
    return decorator
