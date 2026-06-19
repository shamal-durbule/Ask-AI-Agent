from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.properties import router as properties_router
from app.api.tenants import router as tenants_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(properties_router)
api_router.include_router(tenants_router)
