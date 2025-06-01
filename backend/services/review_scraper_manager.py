import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from backend.services.apple_review_scraper import AppleReviewScraper
from backend.services.google_review_scraper import GoogleReviewScraper

class ReviewScraperManager:
    """
    Unified manager for both Apple and Google Play Store review scraping.
    
    This class provides a single interface to scrape reviews from both platforms
    with consistent configuration and error handling.
    """
    
    def __init__(self, 
                 proxy_config: Optional[Dict[str, str]] = None,
                 rate_limit_delay: float = 1.0,
                 max_retries: int = 3,
                 timeout: int = 30):
        """
        Initialize the scraper manager.
        
        Args:
            proxy_config: Proxy configuration for both scrapers
            rate_limit_delay: Delay between requests
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self.proxy_config = proxy_config
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def scrape_apple_reviews(self, 
                                 app_id: Union[str, int],
                                 count: int = 100,
                                 country: str = "us",
                                 **kwargs) -> Dict[str, Any]:
        """
        Scrape Apple App Store reviews.
        
        Args:
            app_id: Apple App Store app ID
            count: Number of reviews to scrape
            country: App Store country code
            **kwargs: Additional Apple scraper parameters
            
        Returns:
            Dictionary with reviews and metadata
        """
        async with AppleReviewScraper(
            proxy_config=self.proxy_config,
            rate_limit_delay=self.rate_limit_delay,
            max_retries=self.max_retries,
            timeout=self.timeout,
            country=country
        ) as scraper:
            return await scraper.scrape_reviews(app_id, count, country)
    
    async def scrape_google_reviews(self, 
                                  package_name: str,
                                  count: int = 100,
                                  sort_order: str = "newest",
                                  filter_score: Optional[int] = None,
                                  language: str = "en",
                                  country: str = "us",
                                  **kwargs) -> Dict[str, Any]:
        """
        Scrape Google Play Store reviews.
        
        Args:
            package_name: Google Play package name
            count: Number of reviews to scrape
            sort_order: Sort order for reviews
            filter_score: Filter by star rating (1-5)
            language: Language code
            country: Country code
            **kwargs: Additional Google scraper parameters
            
        Returns:
            Dictionary with reviews and metadata
        """
        async with GoogleReviewScraper(
            proxy_config=self.proxy_config,
            rate_limit_delay=self.rate_limit_delay,
            max_retries=self.max_retries,
            timeout=self.timeout,
            language=language,
            country=country
        ) as scraper:
            return await scraper.scrape_reviews(
                package_name=package_name,
                count=count,
                sort_order=sort_order,
                filter_score=filter_score,
                **kwargs
            )
    
    async def scrape_both_platforms(self, 
                                  app_identifiers: Dict[str, str],
                                  count: int = 100,
                                  **kwargs) -> Dict[str, Any]:
        """
        Scrape reviews from both platforms simultaneously.
        
        Args:
            app_identifiers: Dict with 'apple' and 'google' keys containing app IDs
                           e.g., {'apple': '479516143', 'google': 'com.slack'}
            count: Number of reviews to scrape from each platform
            **kwargs: Additional parameters for scrapers
            
        Returns:
            Dictionary containing results from both platforms
        """
        results = {
            'apple': None,
            'google': None,
            'summary': {
                'total_reviews': 0,
                'successful_platforms': [],
                'failed_platforms': [],
                'scraped_at': datetime.now().isoformat()
            }
        }
        
        # Prepare tasks for concurrent execution
        tasks = []
        
        if 'apple' in app_identifiers:
            apple_task = asyncio.create_task(
                self.scrape_apple_reviews(
                    app_identifiers['apple'], 
                    count, 
                    **kwargs
                )
            )
            tasks.append(('apple', apple_task))
        
        if 'google' in app_identifiers:
            google_task = asyncio.create_task(
                self.scrape_google_reviews(
                    app_identifiers['google'], 
                    count, 
                    **kwargs
                )
            )
            tasks.append(('google', google_task))
        
        # Execute tasks concurrently
        for platform, task in tasks:
            try:
                result = await task
                results[platform] = result
                
                if result.get('success'):
                    results['summary']['successful_platforms'].append(platform)
                    results['summary']['total_reviews'] += len(result.get('reviews', []))
                else:
                    results['summary']['failed_platforms'].append(platform)
                    
            except Exception as e:
                self.logger.error(f"Failed to scrape {platform}: {e}")
                results[platform] = {
                    'success': False,
                    'error': str(e),
                    'platform': platform
                }
                results['summary']['failed_platforms'].append(platform)
        
        return results
    
    async def scrape_with_auto_insertion(self, 
                                       app_identifiers: Dict[str, str],
                                       app_id: str,
                                       count: int = 100,
                                       **kwargs) -> Dict[str, Any]:
        """
        Scrape reviews and automatically insert them into the database.
        
        Args:
            app_identifiers: Platform-specific app identifiers
            app_id: Your internal app identifier for database
            count: Number of reviews to scrape
            **kwargs: Additional scraper parameters
            
        Returns:
            Dictionary with scraping and insertion results
        """
        try:
            # Import here to avoid circular imports
            from backend.services.review_insertion_service import ReviewInsertionService
            
            # Scrape reviews from both platforms
            scrape_results = await self.scrape_both_platforms(app_identifiers, count, **kwargs)
            
            # Initialize insertion service
            insertion_service = ReviewInsertionService()
            
            insertion_results = {}
            
            # Insert Apple reviews if successful
            if scrape_results['apple'] and scrape_results['apple'].get('success'):
                apple_reviews = scrape_results['apple']['reviews']
                insertion_results['apple'] = await insertion_service.insert_apple_reviews(
                    apple_reviews, app_id
                )
            
            # Insert Google reviews if successful
            if scrape_results['google'] and scrape_results['google'].get('success'):
                google_reviews = scrape_results['google']['reviews']
                insertion_results['google'] = await insertion_service.insert_google_reviews(
                    google_reviews, app_id
                )
            
            return {
                'success': True,
                'scrape_results': scrape_results,
                'insertion_results': insertion_results,
                'summary': {
                    'total_scraped': scrape_results['summary']['total_reviews'],
                    'total_inserted': sum(
                        result.get('inserted_count', 0) 
                        for result in insertion_results.values()
                    ),
                    'platforms_processed': scrape_results['summary']['successful_platforms']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Auto-insertion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'scrape_results': scrape_results if 'scrape_results' in locals() else None
            }


# Convenience functions for direct usage
async def scrape_app_reviews(platform: str,
                           app_identifier: str,
                           count: int = 100,
                           proxy_config: Optional[Dict[str, str]] = None,
                           **kwargs) -> Dict[str, Any]:
    """
    Convenience function to scrape reviews from a specific platform.
    
    Args:
        platform: 'apple' or 'google'
        app_identifier: App ID (Apple) or package name (Google)
        count: Number of reviews to scrape
        proxy_config: Proxy configuration
        **kwargs: Platform-specific parameters
        
    Returns:
        Dictionary with reviews and metadata
    """
    manager = ReviewScraperManager(proxy_config=proxy_config)
    
    if platform.lower() == 'apple':
        return await manager.scrape_apple_reviews(app_identifier, count, **kwargs)
    elif platform.lower() == 'google':
        return await manager.scrape_google_reviews(app_identifier, count, **kwargs)
    else:
        raise ValueError(f"Unsupported platform: {platform}")


async def scrape_and_insert_reviews(app_identifiers: Dict[str, str],
                                  app_id: str,
                                  count: int = 100,
                                  proxy_config: Optional[Dict[str, str]] = None,
                                  **kwargs) -> Dict[str, Any]:
    """
    Convenience function to scrape and automatically insert reviews.
    
    Args:
        app_identifiers: Dict with platform app identifiers
        app_id: Internal app identifier for database
        count: Number of reviews to scrape
        proxy_config: Proxy configuration
        **kwargs: Additional parameters
        
    Returns:
        Complete scraping and insertion results
    """
    manager = ReviewScraperManager(proxy_config=proxy_config)
    return await manager.scrape_with_auto_insertion(app_identifiers, app_id, count, **kwargs)