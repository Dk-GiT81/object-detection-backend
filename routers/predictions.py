import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Prediction
from schemas.prediction import PredictionResponse
from utils.dependencies import get_current_user


router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"]
)


@router.get(
    "/history",
    response_model=list[PredictionResponse]
)
def get_prediction_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )