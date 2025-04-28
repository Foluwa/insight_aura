from backend.services.base_service import BaseService

class ReviewService(BaseService):
    async def get_reviews_count(self) -> int:
        result = await self.connection.fetchval('SELECT COUNT(*) FROM reviews')
        return result

    async def get_reviews_for_app(self, app_id: str, platform: str) -> list:
        query = """
        SELECT * FROM reviews
        WHERE app_id = $1 AND platform = $2
        ORDER BY created_at DESC
        LIMIT 100
        """
        records = await self.connection.fetch(query, app_id, platform)
        return [dict(record) for record in records]

    async def save_review(self, review_data: dict) -> None:
        query = """
        INSERT INTO reviews (app_id, platform, review_text, sentiment, created_at)
        VALUES ($1, $2, $3, $4, NOW())
        """
        await self.connection.execute(
            query,
            review_data['app_id'],
            review_data['platform'],
            review_data['review_text'],
            review_data['sentiment'],
        )
