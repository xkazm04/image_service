from fastapi import APIRouter
from routes.image import router as image_router
from routes.leo import router as leo_router
from routes.variation import router as variation_router
from routes.projects import router as projects_router
from routes.unified import router as unified_router

api_router = APIRouter()

# Unified generation endpoints (primary interface)
api_router.include_router(unified_router, prefix="/unified", tags=["Unified Generation"])

# Legacy and specific endpoints
api_router.include_router(projects_router, prefix="", tags=["Projects"])
api_router.include_router(image_router, prefix="", tags=["Images"])
api_router.include_router(leo_router, prefix="/leo", tags=["Leonardo AI"])
api_router.include_router(variation_router, prefix="/var", tags=["Variations"])