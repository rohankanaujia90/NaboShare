from fastapi import APIRouter

from app.api.routes import auth, communities, health, items, rentals, users

api_router = APIRouter()
api_router.include_router(rentals.router, prefix="/rentals", tags=["rentals"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    communities.router,
    prefix="/communities",
    tags=["communities"],
)
api_router.include_router(health.router, prefix="/health", tags=["health"])
