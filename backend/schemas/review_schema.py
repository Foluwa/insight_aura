from pydantic import BaseModel
from typing import Literal

class PredictRequest(BaseModel):
    text: str
    platform: Literal["google", "apple"]
    app_id: str