"""
auth_service/app/api/router.py

Агрегатор роутеров. Удобен при росте: добавляешь новые модули здесь,
main.py остаётся неизменным.

При масштабировании: api_router.include_router(routes_users.router)
                                 api_router.include_router(routes_admin.router)
"""
from fastapi import APIRouter

from app.api.routes_auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
