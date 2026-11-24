from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Mandate(Base):
    __tablename__ = "mandates"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    total_budget = Column(Float, default=25.0)
    spent_amount = Column(Float, default=0.0)
    reserved_amount = Column(Float, default=0.0)
    max_per_tx = Column(Float, default=10.0)
    auto_approve_under = Column(Float, default=5.0)
    allowed_categories = Column(Text, default='["groceries", "data_api"]')
    allowed_merchants = Column(Text, default='["mock_merchant", "data_provider"]')
    expires_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    def get_allowed_categories(self):
        try:
            return json.loads(self.allowed_categories)
        except Exception:
            return []

    def get_allowed_merchants(self):
        try:
            return json.loads(self.allowed_merchants)
        except Exception:
            return []


class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id = Column(String, primary_key=True, index=True)
    mandate_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=False)
    merchant = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    declared_intent = Column(String, nullable=False)
    actual_item = Column(String, nullable=False)
    status = Column(String, default="PENDING_HUMAN")  # APPROVED, PENDING_HUMAN, DENIED, SETTLED, REJECTED_BY_HUMAN
    denial_reason = Column(String, nullable=True)
    settlement_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intent_id = Column(String, nullable=True, index=True)
    event_type = Column(String, nullable=False)  # e.g., "POLICY_CHECK", "SETTLEMENT", "HUMAN_OVERRIDE"
    rule_evaluated = Column(String, nullable=False)
    outcome = Column(String, nullable=False)  # PASS, WARN, BLOCK
    details = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.utcnow)
