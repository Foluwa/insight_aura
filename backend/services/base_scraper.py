import logging
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import time
import random

class BaseScraper(ABC):
    """
    Abstract base class for review scrapers.
    Provides common functionality like proxy support, rate limiting, and error handling.
    """
    
    def __init__(self, 
                 proxy_config: Optional[Dict[str, str]] = None,
                 rate_limit_delay: float = 1.0,
                 max_retries: int = 3,
                 timeout: int = 30):
        """
        Initialize the base scraper.
        
        Args:
            proxy_config: Dictionary with proxy configuration {'http': 'proxy_url', 'https': 'proxy_url'}
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.proxy_config = proxy_config
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Session for connection pooling and proxy support
        self._session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
    
    async def _create_session(self):
        """Create aiohttp session with proxy configuration"""
        connector_kwargs = {}
        
        if self.proxy_config:
            connector_kwargs['trust_env'] = True
        
        connector = aiohttp.TCPConnector(**connector_kwargs)
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        self.logger.info(f"Created session with proxy: {bool(self.proxy_config)}")
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self._session:
            await self._session.close()
            self.logger.info("Session closed")
    
    async def _make_request_with_retry(self, *args, **kwargs):
        """
        Make HTTP request with retry logic and rate limiting.
        
        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                if attempt > 0:
                    delay = self.rate_limit_delay * (2 ** attempt) + random.uniform(0, 1)
                    self.logger.info(f"Waiting {delay:.2f}s before retry {attempt}")
                    await asyncio.sleep(delay)
                
                # Apply proxy to kwargs if configured
                if self.proxy_config:
                    kwargs.setdefault('proxy', self.proxy_config.get('http'))
                
                async with self._session.request(*args, **kwargs) as response:
                    if response.status == 200:
                        return response
                    else:
                        self.logger.warning(f"Request failed with status {response.status}")
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Request timeout on attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                self.logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            # Wait before next attempt (except on last attempt)
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.rate_limit_delay)
        
        self.logger.error(f"All {self.max_retries} attempts failed")
        return None
    
    def _handle_scraping_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """
        Handle and format scraping errors.
        
        Args:
            error: The exception that occurred
            context: Context information about where the error occurred
            
        Returns:
            Formatted error dictionary
        """
        error_info = {
            'success': False,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.error(f"Scraping error in {context}: {error}")
        return error_info
    
    def _format_review_data(self, raw_review: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format raw review data into standardized format.
        Must be implemented by subclasses.
        
        Args:
            raw_review: Raw review data from the platform
            
        Returns:
            Standardized review dictionary
        """
        pass
    
    @abstractmethod
    async def scrape_reviews(self, 
                           app_identifier: str, 
                           count: int = 100,
                           **kwargs) -> Dict[str, Any]:
        """
        Scrape reviews for a given app.
        Must be implemented by subclasses.
        
        Args:
            app_identifier: App ID or package name
            count: Number of reviews to scrape
            **kwargs: Additional platform-specific parameters
            
        Returns:
            Dictionary containing reviews and metadata
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name (e.g., 'google', 'apple')"""
        pass