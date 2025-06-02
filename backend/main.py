import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from starlette.responses import JSONResponse

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from backend.api.lifespan import lifespan
from backend.api.routes import sentiment

# Initialize Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
    )

# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="Insight Aura API",
    version="1.0.0",
    description="API for reviews and sentiment analysis.",
    lifespan=lifespan
)

# Register Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Sentry Middleware
if SENTRY_DSN:
    app.add_middleware(SentryAsgiMiddleware)

# Sentient Analysis Router
# app.include_router(sentiment.router, prefix="/api/v1", tags=["Sentiment"])
app.include_router(sentiment.router)

# Health Check Endpoint
@app.get("/health", response_class=JSONResponse)
async def health_check():
    return {"status": "ok", "message": "Service is healthy!"}

app.include_router(sentiment.router)
