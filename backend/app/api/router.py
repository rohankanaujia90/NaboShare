from fastapi import APIRouter

from app.api.routes import auth, communities, health

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    communities.router,
    prefix="/communities",
    tags=["communities"],
)
api_router.include_router(health.router, prefix="/health", tags=["health"])
