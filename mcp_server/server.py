import os
import sys
import json
import requests
from typing import Dict, Any, Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MERCHANT_URL = os.getenv("MERCHANT_URL", "http://localhost:8001")

def check_mandate(mandate_id: str = "mandate_daily_ops") -> Dict[str, Any]:
    """Inspect current budget, remaining balance, and limits before attempting a purchase."""
    try:
        res = requests.get(f"{BACKEND_URL}/api/mandates/{mandate_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            remaining = data["total_budget"] - data["spent_amount"] - data["reserved_amount"]
            return {
                "mandate_id": data["id"],
                "total_budget": data["total_budget"],
                "spent_amount": data["spent_amount"],
                "reserved_amount": data["reserved_amount"],
                "available_balance": remaining,
                "max_per_tx": data["max_per_tx"],
                "auto_approve_threshold": data["auto_approve_under"],
                "allowed_categories": data["allowed_categories"]
            }
        return {"error": f"Failed to fetch mandate: {res.text}"}
    except Exception as e:
        return {"error": str(e)}

def request_payment(
    mandate_id: str,
    amount: float,
    merchant: str,
    category: str,
    declared_intent: str,
    actual_item: str,
    agent_id: str = "agent_autonomous_1"
) -> Dict[str, Any]:
    """Request GuardPay authorization or escrow hold for a transaction."""
    payload = {
        "mandate_id": mandate_id,
        "agent_id": agent_id,
        "merchant": merchant,
        "category": category,
        "amount": amount,
        "declared_intent": declared_intent,
        "actual_item": actual_item
    }
    try:
        res = requests.post(f"{BACKEND_URL}/api/intents", json=payload, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_payment_status(intent_id: str) -> Dict[str, Any]:
    """Poll or query the status of a pending payment intent."""
    try:
        res = requests.get(f"{BACKEND_URL}/api/intents/{intent_id}", timeout=5)
        if res.status_code == 200:
            return res.json()
        return {"error": f"Intent not found: {res.text}"}
    except Exception as e:
        return {"error": str(e)}

def pay_402_endpoint(url: str, declared_intent: str, mandate_id: str = "mandate_daily_ops") -> Dict[str, Any]:
    """
    Automates handling of an HTTP 402 Payment Required endpoint.
    1. Probes endpoint -> receives 402 terms.
    2. Calls GuardPay engine to request approval/settlement token.
    3. Re-calls endpoint with Authorization: Bearer <settlement_token> to retrieve data.
    """
    try:
        # Step 1: Probe 402 endpoint
        probe = requests.get(url, timeout=5)
        if probe.status_code != 402:
            return {"status": "UNEXPECTED_STATUS", "status_code": probe.status_code, "body": probe.text}

        terms = probe.json()
        price = terms.get("price", 0.0)
        merchant = terms.get("merchant", "mock_merchant")
        category = terms.get("category", "data_api")
        item_name = terms.get("message", "API Resource Unlock")

        # Step 2: Request payment via GuardPay
        gp_res = request_payment(
            mandate_id=mandate_id,
            amount=price,
            merchant=merchant,
            category=category,
            declared_intent=declared_intent,
            actual_item=item_name
        )

        status_result = gp_res.get("status")
        if status_result == "DENIED":
            return {
                "status": "PAYMENT_DENIED",
                "reason": gp_res.get("denial_reason"),
                "guardpay_response": gp_res
            }

        if status_result == "PENDING_HUMAN":
            return {
                "status": "PENDING_HUMAN_APPROVAL",
                "intent_id": gp_res.get("intent_id"),
                "message": "Payment paused in escrow awaiting operator sign-off.",
                "guardpay_response": gp_res
            }

        token = gp_res.get("settlement_token")
        if not token:
            return {"status": "ERROR", "message": "No settlement token issued by GuardPay", "guardpay_response": gp_res}

        # Step 3: Present settlement token to unlock paywalled data
        unlock_res = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=5)
        return {
            "status": "SUCCESS_UNLOCKED",
            "settlement_token": token,
            "data": unlock_res.json() if unlock_res.status_code == 200 else unlock_res.text
        }
    except Exception as e:
        return {"error": str(e)}

# Dual-mode runner: FastMCP/Standard MCP or HTTP API fallback for lightweight agent triggers
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("GuardPay Agent Payment Gateway")

    @mcp.tool()
    def tool_check_mandate(mandate_id: str = "mandate_daily_ops") -> str:
        return json.dumps(check_mandate(mandate_id))

    @mcp.tool()
    def tool_request_payment(
        mandate_id: str,
        amount: float,
        merchant: str,
        category: str,
        declared_intent: str,
        actual_item: str,
        agent_id: str = "agent_autonomous_1"
    ) -> str:
        return json.dumps(request_payment(mandate_id, amount, merchant, category, declared_intent, actual_item, agent_id))

    @mcp.tool()
    def tool_get_payment_status(intent_id: str) -> str:
        return json.dumps(get_payment_status(intent_id))

    @mcp.tool()
    def tool_pay_402_endpoint(url: str, declared_intent: str, mandate_id: str = "mandate_daily_ops") -> str:
        return json.dumps(pay_402_endpoint(url, declared_intent, mandate_id))

except Exception:
    mcp = None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        # Run HTTP bridge for external agents
        from fastapi import FastAPI
        import uvicorn
        bridge = FastAPI(title="GuardPay MCP HTTP Bridge")

        @bridge.get("/tools/check_mandate")
        def api_check_mandate(mandate_id: str = "mandate_daily_ops"):
            return check_mandate(mandate_id)

        @bridge.post("/tools/request_payment")
        def api_request_payment(payload: Dict[str, Any]):
            return request_payment(**payload)

        @bridge.get("/tools/get_payment_status/{intent_id}")
        def api_get_status(intent_id: str):
            return get_payment_status(intent_id)

        @bridge.post("/tools/pay_402_endpoint")
        def api_pay_402(payload: Dict[str, Any]):
            return pay_402_endpoint(payload.get("url"), payload.get("declared_intent"), payload.get("mandate_id", "mandate_daily_ops"))

        uvicorn.run(bridge, host="0.0.0.0", port=8000)
    else:
        if mcp:
            mcp.run()
        else:
            # Fallback simple CLI test
            print(json.dumps(check_mandate()))
