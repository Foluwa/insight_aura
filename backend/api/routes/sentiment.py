from fastapi import APIRouter, Depends
from backend.database.connection import get_db_connection
from backend.services.review_service import ReviewService
import asyncpg

router = APIRouter()

@router.get("/reviews/count")
async def get_reviews_count(connection: asyncpg.Connection = Depends(get_db_connection)):
    service = ReviewService(connection)
    count = await service.get_reviews_count()
    return {"reviews_count": count}

@router.get("/reviews/{app_id}/{platform}")
async def get_app_reviews(app_id: str, platform: str, connection: asyncpg.Connection = Depends(get_db_connection)):
    service = ReviewService(connection)
    reviews = await service.get_reviews_for_app(app_id, platform)
    return {"reviews": reviews}
