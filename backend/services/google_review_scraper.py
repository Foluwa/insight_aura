import sentry_sdk

try:
    # scraping logic
    raise ValueError("Scraper failed unexpectedly!")
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
