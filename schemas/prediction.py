from pydantic import BaseModel
from datetime import datetime


class PredictionResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    detections: str
    created_at: datetime

    class Config:
        from_attributes = True