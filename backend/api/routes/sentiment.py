import logging

logger = logging.getLogger("sentiment")
logging.basicConfig(level=logging.INFO)

from fastapi import APIRouter, HTTPException
from backend.schemas.sentiment_schema import BatchSentimentRequest, BatchSentimentResponse, SentimentRequest, SentimentResponse
from backend.services.sentiment_service import SentimentService

router = APIRouter(prefix="/predict", tags=["Sentiment"])

@router.post("/", response_model=SentimentResponse)
async def predict_sentiment(payload: SentimentRequest):
    try:
        logger.info(f"📩 Incoming prediction request: {payload.text}")
        result = SentimentService.analyze(payload.text)
        return SentimentResponse(**result)
    except Exception as e:
        logger.error(f"❌ Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    
# @router.post("/", response_model=SentimentResponse)
# async def predict_sentiment(payload: SentimentRequest):
#     try:
#         result = SentimentService.analyze(payload.text)
#         return SentimentResponse(**result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/batch", response_model=BatchSentimentResponse)
async def predict_batch(payload: BatchSentimentRequest):
    try:
        results = [SentimentService.analyze(text) for text in payload.texts]
        return {"results": results}
    except Exception as e:
        logger.error(f"❌ Batch prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")
        
# from fastapi import APIRouter, Depends
# from backend.database.connection import get_db_connection
# from backend.services.review_service import ReviewService
# import asyncpg

# router = APIRouter()

# @router.get("/reviews/count")
# async def get_reviews_count(connection: asyncpg.Connection = Depends(get_db_connection)):
#     service = ReviewService(connection)
#     count = await service.get_reviews_count()
#     return {"reviews_count": count}

# @router.get("/reviews/{app_id}/{platform}")
# async def get_app_reviews(app_id: str, platform: str, connection: asyncpg.Connection = Depends(get_db_connection)):
#     service = ReviewService(connection)
#     reviews = await service.get_reviews_for_app(app_id, platform)
#     return {"reviews": reviews}
