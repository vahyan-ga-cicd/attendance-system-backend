from fastapi import APIRouter, HTTPException
from boto3.dynamodb.conditions import Key
from app.models.employee import EmployeeCreate
from app.core.aws import s3, employee_table
from app.core.config import settings
from app.service.face_service import process_onboarding_images
from app.service.recognition_service import train_model
from app.utils.helpers import get_next_employee_id
import cv2
import io
from typing import List

router = APIRouter()

@router.post("/onboard")
async def onboard_employee(data: EmployeeCreate, images: List[str]):
    print(f"DEBUG: Received {len(images)} images for onboarding.")
    
    if len(images) < 1:
        raise HTTPException(status_code=400, detail="At least one image is required for onboarding.")

    # 1. Generate ID if not provided
    emp_id = data.employee_id or get_next_employee_id()

    # 2. Process faces
    faces = process_onboarding_images(images)
    if not faces:
        raise HTTPException(status_code=400, detail="No faces detected in provided images.")
    email_already_exist = employee_table.scan(
        FilterExpression=Key('email').eq(data.email)
    )
    if email_already_exist["Items"]:
        raise HTTPException(status_code=400, detail="Email already exists.")
    # 3. Save to DynamoDB
    employee_table.put_item(
        Item={
            "employee_id": emp_id,
            "name": data.name,
            "department": data.department,
            "email": data.email,
            "created_at": data.created_at
        }
    )

    # 4. Save images to S3 & prepare for training
    processed_faces = []
    for i, face in enumerate(faces):
        _, buffer = cv2.imencode(".jpg", face)
        
        s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=f"employee_records/{emp_id}/photo_{i}.jpg",
            Body=buffer.tobytes()
        )
        processed_faces.append(face)

    # 5. Train and save model
    train_model(emp_id, processed_faces)

    return {
        "message": "Employee onboarded successfully",
        "employee_id": emp_id,
        "photos_saved": len(faces)
    }

@router.get("/{employee_id}")
async def get_employee(employee_id: str):
    response = employee_table.get_item(Key={"employee_id": employee_id})
    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Employee not found")
    return response["Item"]