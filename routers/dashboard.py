from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from utils.dependencies import get_current_user
from database.connection import get_db
from database.models import User, Prediction
from utils.dependencies import require_roles

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/stats",
    dependencies=[Depends(require_roles("admin", "super_admin"))]
)
def get_dashboard_stats(db: Session = Depends(get_db)):

    total_users = db.query(User).filter(
        User.role == "user"
    ).count()

    total_admins = db.query(User).filter(
        User.role == "admin"
    ).count()

    total_predictions = db.query(Prediction).count()

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_predictions": total_predictions
    }
    
    
@router.get(
    "/recent-predictions",
    dependencies=[Depends(require_roles("admin", "super_admin"))]
)
def get_recent_predictions(db: Session = Depends(get_db)):
    predictions = (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .limit(5)
        .all()
    )

    return [
        {
            "id": prediction.id,
            "user_id": prediction.user_id,
            "filename": prediction.filename,
            "detections": prediction.detections,
            "created_at": prediction.created_at
        }
        for prediction in predictions
    ]
    
@router.get("/user-stats")
def get_user_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    predictions = (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user.id)
        .all()
    )

    total_predictions = len(predictions)

    total_objects = 0

    for prediction in predictions:
        detections = json.loads(prediction.detections)
        total_objects += len(detections)

    return {
        "total_predictions": total_predictions,
        "total_objects": total_objects
    }