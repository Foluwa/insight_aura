from backend.models.sentiment_bert.inference import predict_sentiment
from backend.database.connection import get_db_connection
import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class SentimentService:
    @staticmethod
    def analyze(text: str, review_id: int):
        result = predict_sentiment(text)

        async def save():
            try:
                async with get_db_connection() as conn:
                    await conn.execute(
                        """
                        INSERT INTO ml_outputs (
                            review_id, model_name, model_task,
                            sentiment, sentiment_score, sentiment_analysis, summary, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        review_id,
                        "nlptown/bert-base-multilingual-uncased-sentiment",
                        "sentiment",
                        result["rating"],
                        result["confidence"],
                        result["probabilities"],
                        None,
                        datetime.datetime.utcnow()
                    )
            except Exception as e:
                logger.exception("❌ [ML_OUTPUT ERROR] Failed to save prediction")

        asyncio.create_task(save())
        return result
    
    # @staticmethod
    # def analyze(text: str):
    #     result = predict_sentiment(text)

    #     async def save():
    #         try:
    #             async with get_db_connection() as conn:
    #                 await conn.execute(
    #                     """
    #                     INSERT INTO ml_outputs (
    #                         review_id, model_name, model_type,
    #                         prediction, prediction_score, full_output, created_at
    #                     ) VALUES ($1, $2, $3, $4, $5, $6, $7)
    #                     """,
    #                     None,
    #                     "nlptown/bert-base-multilingual-uncased-sentiment",
    #                     "sentiment",
    #                     result["rating"],
    #                     result["confidence"],
    #                     result["probabilities"],
    #                     datetime.datetime.utcnow()
    #                 )
    #         except Exception as e:
    #             logger.exception("❌ [ML_OUTPUT ERROR] Failed to save prediction")

    #     asyncio.create_task(save())
    #     return result