"""API v1 routers aggregator."""
from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.accounts import router as accounts_router
from backend.app.api.v1.tariffs import router as tariffs_router
from backend.app.api.v1.statements import router as statements_router
from backend.app.api.v1.audits import router as audits_router
from backend.app.api.v1.reversals import router as reversals_router
from backend.app.api.v1.verifications import router as verifications_router
from backend.app.api.v1.mock_bank import router as mock_bank_router
from backend.app.api.v1.seed import router as seed_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(accounts_router)
api_v1_router.include_router(tariffs_router)
api_v1_router.include_router(statements_router)
api_v1_router.include_router(audits_router)
api_v1_router.include_router(reversals_router)
api_v1_router.include_router(verifications_router)
api_v1_router.include_router(mock_bank_router)
api_v1_router.include_router(seed_router)
