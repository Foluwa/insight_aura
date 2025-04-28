import pytest
import asyncpg
from backend.services.review_service import ReviewService

DATABASE_URL = ""

@pytest.fixture(scope="function")
async def db_connection():
    connection = await asyncpg.connect(DATABASE_URL)
    try:
        yield connection
    finally:
        await connection.close()

@pytest.mark.asyncio
async def test_get_reviews_count(db_connection):
    service = ReviewService(db_connection)
    count = await service.get_reviews_count()
    assert isinstance(count, int)
    assert count >= 0

@pytest.mark.asyncio
async def test_save_and_get_reviews(db_connection):
    service = ReviewService(db_connection)

    dummy_review = {
        "app_id": "com.test.app",
        "platform": "google",
        "review_text": "This app is awesome!",
        "sentiment": "positive"
    }
    await service.save_review(dummy_review)

    reviews = await service.get_reviews_for_app("com.test.app", "google")
    
    assert len(reviews) >= 1
    assert any(review["review_text"] == "This app is awesome!" for review in reviews)
