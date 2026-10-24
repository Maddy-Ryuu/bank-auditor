"""Tests for REST API endpoints."""
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"] == "ok"


@pytest.mark.asyncio
async def test_accounts_and_tiers_api(async_client):
    res_accounts = await async_client.get("/api/v1/accounts")
    assert res_accounts.status_code == 200
    accounts = res_accounts.json()
    assert len(accounts) >= 3

    res_tiers = await async_client.get("/api/v1/accounts/tiers")
    assert res_tiers.status_code == 200
    tiers = res_tiers.json()
    assert len(tiers) >= 3


@pytest.mark.asyncio
async def test_audit_api_flow(async_client):
    # 1. List statements
    stmts_res = await async_client.get("/api/v1/statements?is_subsequent=false")
    assert stmts_res.status_code == 200
    statements = stmts_res.json()
    assert len(statements) >= 1
    stmt_id = statements[0]["id"]

    # 2. Run audit
    audit_res = await async_client.post(f"/api/v1/audits/run/{stmt_id}")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["findings_count"] > 0

    # 3. List findings
    findings_res = await async_client.get("/api/v1/audits/findings")
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) > 0
    first_finding_id = findings[0]["id"]

    # 4. Draft reversal
    draft_res = await async_client.post(f"/api/v1/reversals/draft/{first_finding_id}")
    assert draft_res.status_code == 200
    reversal = draft_res.json()
    reversal_id = reversal["id"]
    assert reversal["status"] == "PENDING_APPROVAL"

    # 5. Approve reversal
    action_res = await async_client.post(
        f"/api/v1/reversals/{reversal_id}/action",
        json={"action": "APPROVE", "approved_by_user": "Senior Auditor", "notes": "Approved for submission"}
    )
    assert action_res.status_code == 200
    assert action_res.json()["status"] == "APPROVED"

    # 6. Submit to Mock Bank
    submit_res = await async_client.post(f"/api/v1/reversals/{reversal_id}/submit-mock-bank")
    assert submit_res.status_code == 200
    submit_data = submit_res.json()
    assert submit_data["success"] is True
    assert "MB-TKT-" in submit_data["acknowledgement"]["ticket_id"]

    # 7. Check mock bank status
    mb_res = await async_client.get("/api/v1/mock-bank/status")
    assert mb_res.status_code == 200
    assert mb_res.json()["is_simulation"] is True
