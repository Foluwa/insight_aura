import asyncio
import asyncpg
import logging
from typing import Optional
from app_store_web_scraper import AppStoreEntry
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppleAppStoreScraper:
    def __init__(self, app_id: int, country: str = "us", db_connection: Optional[asyncpg.Connection] = None):
        self.app_id = app_id
        self.country = country
        self.db_connection = db_connection
        self.executor = ThreadPoolExecutor(max_workers=5)  # You can adjust the number of threads

    async def run(self):
        """Run the scraper asynchronously using a thread executor."""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(self.executor, self.scrape_and_save_reviews)
        except Exception as e:
            logger.error(f"🚨 Scraper failed for app_id={self.app_id}: {e}")

    def scrape_and_save_reviews(self):
        """Main scraping and saving function (runs in a separate thread)."""
        try:
            app = AppStoreEntry(app_id=self.app_id, country=self.country)
            logger.info(f"🔹 Fetching reviews for App ID: {self.app_id} in country: {self.country}")

            # Fetch reviews lazily
            for review in app.reviews():
                asyncio.run(self.save_review(review))
        except Exception as e:
            logger.error(f"🚨 Error scraping app_id={self.app_id}: {e}")

    async def save_review(self, review):
        """Save review into database with deduplication based on review id."""
        try:
            # Check if review ID already exists
            exists_query = "SELECT 1 FROM reviews WHERE id = $1 LIMIT 1;"
            exists = await self.db_connection.fetchval(exists_query, int(review.id))

            if exists:
                logger.info(f"⚡ Review {review.id} already exists. Skipping...")
                return

            insert_query = """
                INSERT INTO reviews (id, app_id, platform, date, user_name, user_image, content, rating, app_version, replies, likes_count, language, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW());
            """

            await self.db_connection.execute(
                insert_query,
                int(review.id),
                str(self.app_id),
                "apple",
                review.date or datetime.utcnow(),
                review.user_name,
                review.user_image,
                review.content,
                review.rating,
                review.app_version,
                [],  # No replies field from Apple
                0,   # No likes count available
                "en"  # Assume English, can enhance with language detection
            )

            logger.info(f"✅ Saved review {review.id}")

        except Exception as e:
            logger.error(f"🚨 Error saving review {review.id}: {e}")

