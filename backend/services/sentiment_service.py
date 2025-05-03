# from backend.models.sentiment_bert.inference import predict_sentiment

# class SentimentService:
#     @staticmethod
#     def analyze(text: str):
#         return predict_sentiment(text)

from backend.models.sentiment_bert.inference import predict_sentiment
from backend.database.connection import get_db_connection
import datetime

class SentimentService:
    @staticmethod
    def analyze(text: str):
        result = predict_sentiment(text)

        async def save():
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO ml_outputs (comment_id, model_name, model_type, prediction, prediction_score, full_output, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    None,
                    "nlptown/bert-base-multilingual-uncased-sentiment",
                    "sentiment",
                    result["rating"],
                    result["confidence"],
                    result["probabilities"],
                    datetime.datetime.utcnow()
                )

        import asyncio
    
        asyncio.create_task(save())
        return result
    
    # @staticmethod
    # def analyze(text: str):
    #     result = predict_sentiment(text)
    #     # Save to DB
    #     async def save():
    #         conn = await get_db_connection()
    #         await conn.execute(
    #             """
    #             INSERT INTO ml_outputs (comment_id, model_name, model_type, prediction, prediction_score, full_output, created_at)
    #             VALUES ($1, $2, $3, $4, $5, $6, $7)
    #             """,
    #             None,  # no comment_id (anonymous input)
    #             "nlptown/bert-base-multilingual-uncased-sentiment",
    #             "sentiment",
    #             result["rating"],
    #             result["confidence"],
    #             result["probabilities"],
    #             datetime.datetime.utcnow()
    #         )
    #     import asyncio
    #     asyncio.create_task(save())
    #     return result