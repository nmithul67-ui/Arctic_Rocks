import asyncio
import json
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .models import Mandate, PaymentIntent, AuditEvent
from .database import init_db, get_db
from .schemas import (
    MandateResponse,
    MandateUpdate,
    PaymentIntentCreate,
    PaymentIntentResponse,
    AuditEventResponse,
    HumanReviewAction
)
from .policy import evaluate_intent, settle_pending_intent, log_audit

app = FastAPI(title="GuardPay Policy & Escrow Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed default mandate on startup
def seed_default_mandate():
    from .database import SessionLocal
    db = SessionLocal()
    existing = db.query(Mandate).filter(Mandate.id == "mandate_daily_ops").first()
    if not existing:
        default_mandate = Mandate(
            id="mandate_daily_ops",
            name="Daily Ops Mandate",
            total_budget=25.0,
            spent_amount=0.0,
            reserved_amount=0.0,
            max_per_tx=10.0,
            auto_approve_under=5.0,
            allowed_categories=json.dumps(["groceries", "data_api"]),
            allowed_merchants=json.dumps(["mock_merchant", "data_provider"]),
            active=True
        )
        db.add(default_mandate)
        db.commit()
    db.close()

@app.on_event("startup")
def startup_event():
    init_db()
    seed_default_mandate()

@app.get("/health")
def health():
    return {"status": "ok", "service": "guardpay-backend"}

@app.get("/api/mandates/{mandate_id}", response_model=MandateResponse)
def get_mandate(mandate_id: str, db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    return MandateResponse(
        id=mandate.id,
        name=mandate.name,
        total_budget=mandate.total_budget,
        spent_amount=mandate.spent_amount,
        reserved_amount=mandate.reserved_amount,
        max_per_tx=mandate.max_per_tx,
        auto_approve_under=mandate.auto_approve_under,
        allowed_categories=mandate.get_allowed_categories(),
        allowed_merchants=mandate.get_allowed_merchants(),
        active=mandate.active
    )

@app.patch("/api/mandates/{mandate_id}", response_model=MandateResponse)
def update_mandate(mandate_id: str, payload: MandateUpdate, db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    if payload.total_budget is not None:
        mandate.total_budget = payload.total_budget
    if payload.max_per_tx is not None:
        mandate.max_per_tx = payload.max_per_tx
    if payload.auto_approve_under is not None:
        mandate.auto_approve_under = payload.auto_approve_under
    if payload.active is not None:
        mandate.active = payload.active

    db.commit()
    db.refresh(mandate)
    return MandateResponse(
        id=mandate.id,
        name=mandate.name,
        total_budget=mandate.total_budget,
        spent_amount=mandate.spent_amount,
        reserved_amount=mandate.reserved_amount,
        max_per_tx=mandate.max_per_tx,
        auto_approve_under=mandate.auto_approve_under,
        allowed_categories=mandate.get_allowed_categories(),
        allowed_merchants=mandate.get_allowed_merchants(),
        active=mandate.active
    )

@app.post("/api/intents")
def create_payment_intent(intent_in: PaymentIntentCreate, db: Session = Depends(get_db)):
    status_result, reason, token, record = evaluate_intent(db, intent_in.model_dump())
    
    response_data = {
        "intent_id": record.id,
        "mandate_id": record.mandate_id,
        "status": status_result,
        "amount": record.amount,
        "merchant": record.merchant,
        "denial_reason": reason,
        "settlement_token": token
    }
    
    if status_result == "SETTLED":
        return response_data
    elif status_result == "PENDING_HUMAN":
        return StreamingResponse(
            content=iter([json.dumps(response_data)]),
            status_code=status.HTTP_202_ACCEPTED,
            media_type="application/json"
        ) if False else (response_data, 202)[0]  # Standard JSON 202
    else:
        # DENIED
        return response_data

@app.get("/api/intents", response_model=List[PaymentIntentResponse])
def list_intents(status: str = None, db: Session = Depends(get_db)):
    query = db.query(PaymentIntent)
    if status:
        query = query.filter(PaymentIntent.status == status)
    return query.order_by(PaymentIntent.created_at.desc()).all()

@app.get("/api/intents/{intent_id}", response_model=PaymentIntentResponse)
def get_intent(intent_id: str, db: Session = Depends(get_db)):
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    return intent

@app.post("/api/intents/{intent_id}/review")
def review_payment_intent(intent_id: str, review: HumanReviewAction, db: Session = Depends(get_db)):
    approved = review.action.upper() == "APPROVE"
    success, new_status, token = settle_pending_intent(db, intent_id, approved, review.reason)
    if not success:
        raise HTTPException(status_code=400, detail=new_status)
    return {
        "intent_id": intent_id,
        "status": new_status,
        "settlement_token": token
    }

@app.get("/api/audit-events")
def get_audit_events(limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    results = []
    for e in events:
        try:
            details_json = json.loads(e.details)
        except Exception:
            details_json = {"raw": e.details}
        results.append({
            "id": e.id,
            "intent_id": e.intent_id,
            "event_type": e.event_type,
            "rule_evaluated": e.rule_evaluated,
            "outcome": e.outcome,
            "details": details_json,
            "timestamp": e.timestamp.isoformat()
        })
    return results

@app.post("/api/demo/reset")
def reset_demo_state(db: Session = Depends(get_db)):
    # Clear audit events and intents
    db.query(AuditEvent).delete()
    db.query(PaymentIntent).delete()
    
    # Reset default mandate
    mandate = db.query(Mandate).filter(Mandate.id == "mandate_daily_ops").first()
    if mandate:
        mandate.spent_amount = 0.0
        mandate.reserved_amount = 0.0
        mandate.total_budget = 25.0
        mandate.max_per_tx = 10.0
        mandate.auto_approve_under = 5.0
        mandate.active = True
    else:
        seed_default_mandate()
    
    db.commit()
    log_audit(db, None, "SYSTEM", "Demo Reset", "PASS", {"message": "State reset to initial demo values"})
    return {"status": "success", "message": "Demo state reset successfully"}

@app.get("/api/events/stream")
async def events_stream(db: Session = Depends(get_db)):
    """Server-Sent Events (SSE) stream for live console updates."""
    async def event_generator():
        last_event_id = 0
        from .database import SessionLocal
        while True:
            sub_db = SessionLocal()
            try:
                new_events = sub_db.query(AuditEvent).filter(AuditEvent.id > last_event_id).order_by(AuditEvent.id.asc()).all()
                for event in new_events:
                    last_event_id = event.id
                    payload = {
                        "id": event.id,
                        "intent_id": event.intent_id,
                        "event_type": event.event_type,
                        "rule_evaluated": event.rule_evaluated,
                        "outcome": event.outcome,
                        "details": json.loads(event.details) if event.details else {},
                        "timestamp": event.timestamp.isoformat()
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
            finally:
                sub_db.close()
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
