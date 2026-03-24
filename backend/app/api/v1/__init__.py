"""
API v1 routes.
"""
from fastapi import APIRouter

from app.api.v1 import auth, datasets, draft_pool, evaluation, leaderboard, reports, router, seeds, skills, standards, synthesis, users

api_router = APIRouter(prefix="/v1")

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(seeds.router, prefix="/seeds", tags=["Seeds"])
api_router.include_router(standards.router, prefix="/standards", tags=["Standards"])
api_router.include_router(skills.router, prefix="/skills", tags=["Skills"])
api_router.include_router(synthesis.router, prefix="/synthesis", tags=["Synthesis"])
api_router.include_router(draft_pool.router, prefix="/draft-pool", tags=["Draft Pool"])
api_router.include_router(router.router, prefix="/router", tags=["Data Router"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(evaluation.router, prefix="/evaluations", tags=["Evaluations"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
