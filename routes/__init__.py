from fastapi import APIRouter
from routes.generation import router as generation_router
from routes.image import router as image_router
from routes.leo import router as leo_router
from routes.variation import router as variation_router

api_router = APIRouter()

api_router.include_router(generation_router, prefix="/generations", tags=["Generations"])
api_router.include_router(image_router, prefix="", tags=["Images"])
api_router.include_router(leo_router, prefix="/leo", tags=["Leo"])
api_router.include_router(variation_router, prefix="/var", tags=["Variations"])