# File: backend/services/google_review_scraper.py

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

try:
    from google_play_scraper import Sort, reviews as google_reviews
except ImportError:
    google_reviews = None
    Sort = None

from backend.services.base_scraper import BaseScraper

class GoogleReviewScraper(BaseScraper):
    """
    Google Play Store review scraper with proxy support and error handling.
    
    This scraper uses the google-play-scraper library to fetch reviews
    from Google Play Store with proper error handling and rate limiting.
    """
    
    def __init__(self, 
                 proxy_config: Optional[Dict[str, str]] = None,
                 rate_limit_delay: float = 1.0,
                 max_retries: int = 3,
                 timeout: int = 30,
                 language: str = "en",
                 country: str = "us"):
        """
        Initialize Google Play scraper.
        
        Args:
            proxy_config: Proxy configuration dictionary
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            language: Language code for reviews (en, es, etc.)
            country: Country code for reviews (us, gb, etc.)
        """
        super().__init__(proxy_config, rate_limit_delay, max_retries, timeout)
        self.language = language
        self.country = country
        
        # Check if required library is installed
        if google_reviews is None or Sort is None:
            raise ImportError(
                "google-play-scraper is required for Google Play scraping. "
                "Install with: pip install google-play-scraper"
            )
    
    def get_platform_name(self) -> str:
        """Return platform name"""
        return "google"
    
    async def scrape_reviews(self, 
                           package_name: str, 
                           count: int = 100,
                           sort_order: str = "newest",
                           filter_score: Optional[int] = None,
                           language: Optional[str] = None,
                           country: Optional[str] = None,
                           continuation_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape reviews from Google Play Store.
        
        Args:
            package_name: Google Play package name (e.g., 'com.slack')
            count: Maximum number of reviews to fetch
            sort_order: Sort order ('newest', 'oldest', 'most_relevant', 'helpfulness')
            filter_score: Filter by star rating (1-5, None for all)
            language: Override default language
            country: Override default country
            continuation_token: Token for pagination
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating if scraping was successful
            - reviews: List of review dictionaries
            - metadata: Scraping metadata
            - continuation_token: Token for next page
            - error_info: Error details if scraping failed
        """
        start_time = datetime.now()
        
        try:
            # Use provided values or defaults
            lang = language or self.language
            country_code = country or self.country
            
            # Map sort order string to Sort enum
            sort_mapping = {
                'newest': Sort.NEWEST,
                'oldest': Sort.OLDEST,
                'most_relevant': Sort.MOST_RELEVANT,
                'helpfulness': Sort.HELPFULNESS
            }
            sort_enum = sort_mapping.get(sort_order.lower(), Sort.NEWEST)
            
            self.logger.info(f"Starting Google Play scrape for {package_name}")
            
            # Fetch reviews with retry logic
            result_data, next_token = await self._fetch_reviews_with_retry(
                package_name=package_name,
                count=count,
                lang=lang,
                country=country_code,
                sort=sort_enum,
                filter_score_with=filter_score,
                continuation_token=continuation_token
            )
            
            # Format reviews
            formatted_reviews = []
            for review in result_data:
                formatted_review = self._format_review_data(review)
                formatted_reviews.append(formatted_review)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'reviews': formatted_reviews,
                'continuation_token': next_token,
                'metadata': {
                    'package_name': package_name,
                    'platform': self.get_platform_name(),
                    'language': lang,
                    'country': country_code,
                    'sort_order': sort_order,
                    'filter_score': filter_score,
                    'requested_count': count,
                    'actual_count': len(formatted_reviews),
                    'scrape_duration_seconds': duration,
                    'scraped_at': start_time.isoformat(),
                    'has_more': next_token is not None
                }
            }
            
            self.logger.info(f"Successfully scraped {len(formatted_reviews)} Google Play reviews")
            return result
            
        except Exception as e:
            return self._handle_scraping_error(
                e, f"Google Play scraping for {package_name}"
            )
    
    async def _fetch_reviews_with_retry(self, **kwargs) -> tuple:
        """
        Fetch reviews with retry logic and rate limiting.
        
        Args:
            **kwargs: Arguments for google_play_scraper.reviews()
            
        Returns:
            Tuple of (reviews_list, continuation_token)
        """
        for attempt in range(self.max_retries):
            try:
                # Run the synchronous google-play-scraper in executor
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: google_reviews(**kwargs)
                )
                
                # google_reviews returns (reviews_list, continuation_token)
                return result
                
            except Exception as e:
                self.logger.warning(f"Google Play fetch attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.rate_limit_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise e
    
    def _format_review_data(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Google Play review data into standardized format.
        
        Args:
            review: Raw review dictionary from google-play-scraper
            
        Returns:
            Standardized review dictionary
        """
        try:
            return {
                'reviewId': review.get('reviewId'),
                'userName': review.get('userName'),
                'userImage': review.get('userImage'),
                'content': review.get('content', ''),
                'score': review.get('score'),
                'thumbsUpCount': review.get('thumbsUpCount', 0),
                'reviewCreatedVersion': review.get('reviewCreatedVersion'),
                'at': review.get('at').isoformat() if review.get('at') else None,
                'replyContent': review.get('replyContent'),
                'repliedAt': review.get('repliedAt').isoformat() if review.get('repliedAt') else None,
                'appVersion': review.get('appVersion'),
                # Platform identifier
                'platform': 'google',
                # Store original data for debugging
                'raw_data': review
            }
        except Exception as e:
            self.logger.error(f"Error formatting Google review data: {e}")
            # Return minimal data to avoid complete failure
            return {
                'reviewId': review.get('reviewId'),
                'content': review.get('content', ''),
                'score': review.get('score'),
                'platform': 'google',
                'error': f"Formatting error: {str(e)}",
                'raw_data': review
            }
    
    async def scrape_all_reviews(self, 
                                package_name: str,
                                max_reviews: int = 1000,
                                **kwargs) -> Dict[str, Any]:
        """
        Scrape all available reviews using pagination.
        
        Args:
            package_name: Google Play package name
            max_reviews: Maximum total reviews to fetch
            **kwargs: Additional scraping parameters
            
        Returns:
            Dictionary with all reviews and metadata
        """
        all_reviews = []
        continuation_token = None
        total_scraped = 0
        page = 1
        
        try:
            while total_scraped < max_reviews:
                # Calculate remaining reviews needed
                remaining = max_reviews - total_scraped
                batch_size = min(100, remaining)  # Google Play scraper max is usually 200
                
                self.logger.info(f"Fetching page {page}, batch size: {batch_size}")
                
                # Scrape current batch
                result = await self.scrape_reviews(
                    package_name=package_name,
                    count=batch_size,
                    continuation_token=continuation_token,
                    **kwargs
                )
                
                if not result['success']:
                    self.logger.error(f"Failed to scrape page {page}")
                    break
                
                # Add reviews to collection
                batch_reviews = result['reviews']
                all_reviews.extend(batch_reviews)
                total_scraped += len(batch_reviews)
                
                # Check for more pages
                continuation_token = result.get('continuation_token')
                if not continuation_token or len(batch_reviews) == 0:
                    self.logger.info("No more reviews available")
                    break
                
                page += 1
                
                # Rate limiting between pages
                await asyncio.sleep(self.rate_limit_delay)
            
            return {
                'success': True,
                'reviews': all_reviews,
                'metadata': {
                    'package_name': package_name,
                    'platform': self.get_platform_name(),
                    'total_reviews': len(all_reviews),
                    'pages_scraped': page,
                    'max_requested': max_reviews,
                    'scraped_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return self._handle_scraping_error(
                e, f"Google Play pagination scraping for {package_name}"
            )
    
    async def get_app_info(self, package_name: str) -> Dict[str, Any]:
        """
        Get basic app information from Google Play Store.
        
        Args:
            package_name: Google Play package name
            
        Returns:
            App information dictionary
        """
        try:
            # This would require additional google-play-scraper functionality
            # For now, return basic info
            return {
                'success': True,
                'app_info': {
                    'package_name': package_name,
                    'platform': 'google',
                    'note': 'Extended app info requires additional implementation'
                }
            }
            
        except Exception as e:
            return self._handle_scraping_error(
                e, f"Getting Google Play app info for {package_name}"
            )


# Convenience function for direct usage
async def scrape_google_reviews(package_name: str, 
                              count: int = 100,
                              sort_order: str = "newest",
                              filter_score: Optional[int] = None,
                              language: str = "en",
                              country: str = "us",
                              proxy_config: Optional[Dict[str, str]] = None,
                              **kwargs) -> Dict[str, Any]:
    """
    Convenience function to scrape Google Play Store reviews.
    
    Args:
        package_name: Google Play package name
        count: Number of reviews to scrape
        sort_order: Sort order for reviews
        filter_score: Filter by star rating
        language: Language code
        country: Country code
        proxy_config: Proxy configuration
        **kwargs: Additional scraper configuration
        
    Returns:
        Dictionary with reviews and metadata
    """
    async with GoogleReviewScraper(
        proxy_config=proxy_config,
        language=language,
        country=country,
        **kwargs
    ) as scraper:
        return await scraper.scrape_reviews(
            package_name=package_name,
            count=count,
            sort_order=sort_order,
            filter_score=filter_score
        )


# import sentry_sdk

# try:
#     # scraping logic
#     raise ValueError("Scraper failed unexpectedly!")
# except Exception as e:
#     sentry_sdk.capture_exception(e)
#     raise
