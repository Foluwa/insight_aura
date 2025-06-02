# File: backend/services/apple_review_scraper.py

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

try:
    from app_store_web_scraper import AppStoreEntry
except ImportError:
    AppStoreEntry = None

from backend.services.base_scraper import BaseScraper

class AppleReviewScraper(BaseScraper):
    """
    Apple App Store review scraper with proxy support and error handling.
    
    This scraper uses the app-store-web-scraper library to fetch reviews
    from the Apple App Store with proper error handling and rate limiting.
    """
    
    def __init__(self, 
                 proxy_config: Optional[Dict[str, str]] = None,
                 rate_limit_delay: float = 1.0,
                 max_retries: int = 3,
                 timeout: int = 30,
                 country: str = "us"):
        """
        Initialize Apple scraper.
        
        Args:
            proxy_config: Proxy configuration dictionary
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            country: App Store country code (us, gb, etc.)
        """
        super().__init__(proxy_config, rate_limit_delay, max_retries, timeout)
        self.country = country
        
        # Check if required library is installed
        if AppStoreEntry is None:
            raise ImportError(
                "app-store-web-scraper is required for Apple scraping. "
                "Install with: pip install app-store-web-scraper"
            )
    
    def get_platform_name(self) -> str:
        """Return platform name"""
        return "apple"
    
    async def scrape_reviews(self, 
                           app_id: Union[str, int], 
                           count: int = 100,
                           country: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape reviews from Apple App Store.
        
        Args:
            app_id: Apple App Store app ID (numeric)
            count: Maximum number of reviews to fetch
            country: Override default country code
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating if scraping was successful
            - reviews: List of review dictionaries
            - metadata: Scraping metadata (count, app_id, etc.)
            - error_info: Error details if scraping failed
        """
        start_time = datetime.now()
        
        try:
            # Validate app_id
            app_id = int(app_id)  # Ensure it's an integer
            
            # Use provided country or default
            country_code = country or self.country
            
            self.logger.info(f"Starting Apple scrape for app {app_id}, country: {country_code}")
            
            # Initialize app store entry
            app = AppStoreEntry(app_id=app_id, country=country_code)
            
            # Fetch reviews with error handling
            reviews_data = await self._fetch_reviews_with_limit(app, count)
            
            # Get app metadata
            app_metadata = await self._get_app_metadata(app)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'reviews': reviews_data,
                'metadata': {
                    'app_id': str(app_id),
                    'platform': self.get_platform_name(),
                    'country': country_code,
                    'requested_count': count,
                    'actual_count': len(reviews_data),
                    'scrape_duration_seconds': duration,
                    'scraped_at': start_time.isoformat(),
                    'app_info': app_metadata
                }
            }
            
            self.logger.info(f"Successfully scraped {len(reviews_data)} Apple reviews")
            return result
            
        except ValueError as e:
            return self._handle_scraping_error(
                e, f"Invalid app_id format: {app_id}"
            )
        except Exception as e:
            return self._handle_scraping_error(
                e, f"Apple scraping for app {app_id}"
            )
    
    async def _fetch_reviews_with_limit(self, app: AppStoreEntry, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch reviews with count limit and rate limiting.
        
        Args:
            app: AppStoreEntry instance
            limit: Maximum number of reviews to fetch
            
        Returns:
            List of formatted review dictionaries
        """
        reviews_data = []
        
        try:
            # Use asyncio to run the synchronous review iteration
            reviews_iter = await asyncio.get_event_loop().run_in_executor(
                None, lambda: app.reviews()
            )
            
            count = 0
            for review in reviews_iter:
                if count >= limit:
                    break
                
                # Format review data
                formatted_review = self._format_review_data(review)
                reviews_data.append(formatted_review)
                
                count += 1
                
                # Rate limiting
                if count % 10 == 0:  # Every 10 reviews
                    await asyncio.sleep(self.rate_limit_delay)
                    self.logger.debug(f"Fetched {count} reviews so far...")
            
        except Exception as e:
            self.logger.error(f"Error fetching reviews: {e}")
            raise
        
        return reviews_data
    
    def _format_review_data(self, review) -> Dict[str, Any]:
        """
        Format Apple review data into standardized format.
        
        Args:
            review: Raw review object from app-store-web-scraper
            
        Returns:
            Standardized review dictionary
        """
        try:
            return {
                'id': review.id,
                'date': review.date.isoformat() if review.date else None,
                'user_name': getattr(review, 'user_name', None) or getattr(review, 'username', None),
                'title': getattr(review, 'title', None),
                'content': review.content or '',
                'rating': review.rating,
                'app_version': getattr(review, 'app_version', None) or getattr(review, 'version', None),
                # Platform-specific fields
                'platform': 'apple',
                'raw_data': {
                    'id': review.id,
                    'rating': review.rating,
                    'content': review.content,
                    'date': review.date.isoformat() if review.date else None,
                    'title': getattr(review, 'title', None),
                    'user_name': getattr(review, 'user_name', None) or getattr(review, 'username', None),
                    'app_version': getattr(review, 'app_version', None) or getattr(review, 'version', None)
                }
            }
        except Exception as e:
            self.logger.error(f"Error formatting review data: {e}")
            # Return minimal data to avoid complete failure
            return {
                'id': getattr(review, 'id', None),
                'content': getattr(review, 'content', ''),
                'rating': getattr(review, 'rating', None),
                'platform': 'apple',
                'error': f"Formatting error: {str(e)}"
            }
    
    async def _get_app_metadata(self, app: AppStoreEntry) -> Dict[str, Any]:
        """
        Get app metadata from App Store.
        
        Args:
            app: AppStoreEntry instance
            
        Returns:
            App metadata dictionary
        """
        try:
            # Run synchronous operations in executor
            app_name = await asyncio.get_event_loop().run_in_executor(
                None, lambda: getattr(app, 'name', None)
            )
            
            return {
                'name': app_name,
                'app_id': app.app_id,
                'country': app.country
            }
        except Exception as e:
            self.logger.warning(f"Could not fetch app metadata: {e}")
            return {
                'app_id': app.app_id,
                'country': app.country,
                'metadata_error': str(e)
            }
    
    async def get_app_info(self, app_id: Union[str, int], country: Optional[str] = None) -> Dict[str, Any]:
        """
        Get basic app information without reviews.
        
        Args:
            app_id: Apple App Store app ID
            country: App Store country code
            
        Returns:
            App information dictionary
        """
        try:
            app_id = int(app_id)
            country_code = country or self.country
            
            app = AppStoreEntry(app_id=app_id, country=country_code)
            metadata = await self._get_app_metadata(app)
            
            return {
                'success': True,
                'app_info': metadata
            }
            
        except Exception as e:
            return self._handle_scraping_error(
                e, f"Getting Apple app info for {app_id}"
            )


# Convenience function for direct usage
async def scrape_apple_reviews(app_id: Union[str, int], 
                             count: int = 100,
                             country: str = "us",
                             proxy_config: Optional[Dict[str, str]] = None,
                             **kwargs) -> Dict[str, Any]:
    """
    Convenience function to scrape Apple App Store reviews.
    
    Args:
        app_id: Apple App Store app ID
        count: Number of reviews to scrape
        country: App Store country code
        proxy_config: Proxy configuration
        **kwargs: Additional scraper configuration
        
    Returns:
        Dictionary with reviews and metadata
    """
    async with AppleReviewScraper(
        proxy_config=proxy_config, 
        country=country,
        **kwargs
    ) as scraper:
        return await scraper.scrape_reviews(app_id, count, country)
    

# import asyncio
# import asyncpg
# import logging
# from typing import Optional
# from app_store_web_scraper import AppStoreEntry
# from concurrent.futures import ThreadPoolExecutor
# from datetime import datetime

# # Setup basic logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class AppleAppStoreScraper:
#     def __init__(self, app_id: int, country: str = "us", db_connection: Optional[asyncpg.Connection] = None):
#         self.app_id = app_id
#         self.country = country
#         self.db_connection = db_connection
#         self.executor = ThreadPoolExecutor(max_workers=5)  # You can adjust the number of threads

#     async def run(self):
#         """Run the scraper asynchronously using a thread executor."""
#         loop = asyncio.get_event_loop()
#         try:
#             await loop.run_in_executor(self.executor, self.scrape_and_save_reviews)
#         except Exception as e:
#             logger.error(f"🚨 Scraper failed for app_id={self.app_id}: {e}")

#     def scrape_and_save_reviews(self):
#         """Main scraping and saving function (runs in a separate thread)."""
#         try:
#             app = AppStoreEntry(app_id=self.app_id, country=self.country)
#             logger.info(f"🔹 Fetching reviews for App ID: {self.app_id} in country: {self.country}")

#             # Fetch reviews lazily
#             for review in app.reviews():
#                 asyncio.run(self.save_review(review))
#         except Exception as e:
#             logger.error(f"🚨 Error scraping app_id={self.app_id}: {e}")

#     async def save_review(self, review):
#         """Save review into database with deduplication based on review id."""
#         try:
#             # Check if review ID already exists
#             exists_query = "SELECT 1 FROM reviews WHERE id = $1 LIMIT 1;"
#             exists = await self.db_connection.fetchval(exists_query, int(review.id))

#             if exists:
#                 logger.info(f"⚡ Review {review.id} already exists. Skipping...")
#                 return

#             insert_query = """
#                 INSERT INTO reviews (id, app_id, platform, date, user_name, user_image, content, rating, app_version, replies, likes_count, language, created_at, updated_at)
#                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW());
#             """

#             await self.db_connection.execute(
#                 insert_query,
#                 int(review.id),
#                 str(self.app_id),
#                 "apple",
#                 review.date or datetime.utcnow(),
#                 review.user_name,
#                 review.user_image,
#                 review.content,
#                 review.rating,
#                 review.app_version,
#                 [],  # No replies field from Apple
#                 0,   # No likes count available
#                 "en"  # Assume English, can enhance with language detection
#             )

#             logger.info(f"✅ Saved review {review.id}")

#         except Exception as e:
#             logger.error(f"🚨 Error saving review {review.id}: {e}")

