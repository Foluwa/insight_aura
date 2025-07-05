from pydantic import BaseModel

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    rating: int
    confidence: float
    probabilities: list[float]

class BatchSentimentRequest(BaseModel):
    texts: list[str]

class BatchSentimentResponse(BaseModel):
    results: list[SentimentResponse]