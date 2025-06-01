# File: backend/services/review_insertion_service.py

from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncpg
from backend.database.connection import get_db_connection
import json
import logging

logger = logging.getLogger(__name__)

class ReviewInsertionService:
    """Service for inserting review data from different platforms into the database"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def insert_google_reviews(self, reviews: List[Dict[str, Any]], app_id: str) -> Dict[str, Any]:
        """
        Insert Google Play Store reviews
        
        Args:
            reviews: List of Google review dictionaries
            app_id: Application identifier
            
        Returns:
            Dict with insertion statistics
        """
        inserted_count = 0
        failed_count = 0
        failed_reviews = []
        
        async with get_db_connection() as conn:
            for review in reviews:
                try:
                    await self._insert_single_google_review(conn, review, app_id)
                    inserted_count += 1
                except Exception as e:
                    failed_count += 1
                    failed_reviews.append({
                        'review_id': review.get('reviewId'),
                        'error': str(e)
                    })
                    self.logger.error(f"Failed to insert Google review {review.get('reviewId')}: {e}")
        
        return {
            'platform': 'google',
            'app_id': app_id,
            'inserted_count': inserted_count,
            'failed_count': failed_count,
            'failed_reviews': failed_reviews
        }
    
    async def insert_apple_reviews(self, reviews: List[Dict[str, Any]], app_id: str) -> Dict[str, Any]:
        """
        Insert Apple App Store reviews
        
        Args:
            reviews: List of Apple review dictionaries
            app_id: Application identifier
            
        Returns:
            Dict with insertion statistics
        """
        inserted_count = 0
        failed_count = 0
        failed_reviews = []
        
        async with get_db_connection() as conn:
            for review in reviews:
                try:
                    await self._insert_single_apple_review(conn, review, app_id)
                    inserted_count += 1
                except Exception as e:
                    failed_count += 1
                    failed_reviews.append({
                        'review_id': review.get('id'),
                        'error': str(e)
                    })
                    self.logger.error(f"Failed to insert Apple review {review.get('id')}: {e}")
        
        return {
            'platform': 'apple',
            'app_id': app_id,
            'inserted_count': inserted_count,
            'failed_count': failed_count,
            'failed_reviews': failed_reviews
        }
    
    async def _insert_single_google_review(self, conn: asyncpg.Connection, review: Dict[str, Any], app_id: str):
        """Insert a single Google review"""
        # Parse the date - handle both formats
        date_str = review['at']
        if date_str.endswith('Z'):
            date_str = date_str.replace('Z', '+00:00')
        review_date = datetime.fromisoformat(date_str)
        
        # Handle reply data
        reply_content = review.get('replyContent')
        replied_at = None
        if review.get('repliedAt'):
            replied_date_str = review['repliedAt']
            if replied_date_str.endswith('Z'):
                replied_date_str = replied_date_str.replace('Z', '+00:00')
            replied_at = datetime.fromisoformat(replied_date_str)
        
        await conn.execute("""
            INSERT INTO reviews (
                external_review_id, app_id, platform, review_date,
                user_name, user_image, content, rating, app_version,
                review_created_version, thumbs_up_count, reply_content,
                replied_at, raw_data
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT (external_review_id, platform, app_id) DO UPDATE SET
                content = EXCLUDED.content,
                rating = EXCLUDED.rating,
                thumbs_up_count = EXCLUDED.thumbs_up_count,
                reply_content = EXCLUDED.reply_content,
                replied_at = EXCLUDED.replied_at,
                updated_at = NOW(),
                raw_data = EXCLUDED.raw_data
        """, 
            review['reviewId'],  # external_review_id
            app_id,             # app_id
            'google',           # platform
            review_date,        # review_date
            review.get('userName'),  # user_name
            review.get('userImage'), # user_image
            review['content'],  # content
            review['score'],    # rating
            review.get('appVersion'),  # app_version
            review.get('reviewCreatedVersion'),  # review_created_version
            review.get('thumbsUpCount', 0),  # thumbs_up_count
            reply_content,      # reply_content
            replied_at,         # replied_at
            json.dumps(review)  # raw_data
        )
    
    async def _insert_single_apple_review(self, conn: asyncpg.Connection, review: Dict[str, Any], app_id: str):
        """Insert a single Apple review"""
        # Parse the date (Apple uses ISO format with timezone)
        review_date = datetime.fromisoformat(review['date'])
        
        await conn.execute("""
            INSERT INTO reviews (
                external_review_id, app_id, platform, review_date,
                user_name, title, content, rating, app_version, raw_data
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (external_review_id, platform, app_id) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                rating = EXCLUDED.rating,
                app_version = EXCLUDED.app_version,
                updated_at = NOW(),
                raw_data = EXCLUDED.raw_data
        """, 
            str(review['id']),   # external_review_id (convert to string)
            app_id,             # app_id
            'apple',            # platform
            review_date,        # review_date
            review.get('user_name'),  # user_name
            review.get('title'), # title
            review['content'],  # content
            review['rating'],   # rating
            review.get('app_version'),  # app_version
            json.dumps(review)  # raw_data
        )
    
    async def get_latest_review_date(self, app_id: str, platform: str) -> Optional[datetime]:
        """Get the latest review date for incremental scraping"""
        async with get_db_connection() as conn:
            result = await conn.fetchval("""
                SELECT MAX(review_date) FROM reviews 
                WHERE app_id = $1 AND platform = $2
            """, app_id, platform)
            return result
    
    async def get_review_stats(self, app_id: str, platform: str = None) -> Dict[str, Any]:
        """Get review statistics"""
        async with get_db_connection() as conn:
            if platform:
                result = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_reviews,
                        AVG(rating) as avg_rating,
                        MIN(review_date) as earliest_review,
                        MAX(review_date) as latest_review
                    FROM reviews 
                    WHERE app_id = $1 AND platform = $2
                """, app_id, platform)
            else:
                result = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_reviews,
                        AVG(rating) as avg_rating,
                        MIN(review_date) as earliest_review,
                        MAX(review_date) as latest_review
                    FROM reviews 
                    WHERE app_id = $1
                """, app_id)
            
            return dict(result) if result else {}


# Singleton instance for easy import
review_insertion_service = ReviewInsertionService()