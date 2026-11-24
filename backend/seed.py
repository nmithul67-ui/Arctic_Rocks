import json
from app.database import SessionLocal, init_db
from app.models import Mandate, AuditEvent

def seed():
    init_db()
    db = SessionLocal()
    
    mandate = db.query(Mandate).filter(Mandate.id == "mandate_daily_ops").first()
    if not mandate:
        mandate = Mandate(
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
        db.add(mandate)
        
        event = AuditEvent(
            intent_id=None,
            event_type="SYSTEM",
            rule_evaluated="Database Initial Seeding",
            outcome="PASS",
            details=json.dumps({"message": "Daily Ops Mandate seeded ($25 budget, $5 auto-approve)"})
        )
        db.add(event)
        db.commit()
        print("Default mandate seeded successfully.")
    else:
        print("Mandate already exists.")
    db.close()

if __name__ == "__main__":
    seed()
