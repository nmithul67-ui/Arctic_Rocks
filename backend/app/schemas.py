from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MandateCreate(BaseModel):
    id: str
    name: str
    total_budget: float = 25.0
    max_per_tx: float = 10.0
    auto_approve_under: float = 5.0
    allowed_categories: List[str] = ["groceries", "data_api"]
    allowed_merchants: List[str] = ["mock_merchant", "data_provider"]
    active: bool = True

class MandateUpdate(BaseModel):
    total_budget: Optional[float] = None
    max_per_tx: Optional[float] = None
    auto_approve_under: Optional[float] = None
    active: Optional[bool] = None

class MandateResponse(BaseModel):
    id: str
    name: str
    total_budget: float
    spent_amount: float
    reserved_amount: float
    max_per_tx: float
    auto_approve_under: float
    allowed_categories: List[str]
    allowed_merchants: List[str]
    active: bool

    class Config:
        from_attributes = True

class PaymentIntentCreate(BaseModel):
    mandate_id: str
    agent_id: str
    merchant: str
    category: str
    amount: float
    declared_intent: str
    actual_item: str

class PaymentIntentResponse(BaseModel):
    id: str
    mandate_id: str
    agent_id: str
    merchant: str
    category: str
    amount: float
    declared_intent: str
    actual_item: str
    status: str
    denial_reason: Optional[str] = None
    settlement_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditEventResponse(BaseModel):
    id: int
    intent_id: Optional[str]
    event_type: str
    rule_evaluated: str
    outcome: str
    details: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True

class HumanReviewAction(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    reason: Optional[str] = None
