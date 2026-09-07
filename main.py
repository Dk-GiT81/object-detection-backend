from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
import shutil
from fastapi.middleware.cors import CORSMiddleware
from database.connection import engine, Base
from database import models
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.predictions import router as predictions_router
import json
from sqlalchemy.orm import Session
from fastapi import Depends

from database.connection import get_db
from database.models import Prediction
from utils.dependencies import get_current_user
from routers.dashboard import router as dashboard_router

app = FastAPI(title="Object Detection API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(predictions_router)
Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(dashboard_router)

model = YOLO("yolo11n.pt")

@app.get("/")
def root():
    return {"message": "Object Detection API is running"}


@app.post("/detect")
async def detect(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_path = "temp_image.jpg"

    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    results = model(image_path)

    detections = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            detections.append({
                "class": model.names[class_id],
                "confidence": confidence
            })

    prediction = Prediction(
        user_id=current_user.id,
        filename=file.filename,
        detections=json.dumps(detections)
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return {
        "id": prediction.id,
        "filename": file.filename,
        "detections": detections
    }