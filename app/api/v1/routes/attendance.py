from fastapi import APIRouter, HTTPException
from app.models.attendance import AttendanceCheckIn, AttendanceCheckOut
from app.core.aws import attendance_table, employee_table
from app.service.face_service import base64_to_image, detect_face, detect_eye_blink
from app.service.recognition_service import identify_face
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import time

router = APIRouter()

@router.post("/check-in")
async def check_in(data: AttendanceCheckIn):
    image = base64_to_image(data.image_base64)
    face, _ = detect_face(image)
    if face is None:
        raise HTTPException(status_code=400, detail="Face not detected. Please adjust your position.")
    
    is_blink = detect_eye_blink(image)
    if not is_blink:
        raise HTTPException(status_code=400, detail="Blink not detected! Please blink to verify liveness.")

    label, confidence = identify_face(face)
    if label is None:
        raise HTTPException(status_code=401, detail=f"Face not recognized (Confidence: {confidence:.2f})")

    employee_id = f"VAH{label:03d}"
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # 1. Check if already checked in TODAY
    response = attendance_table.query(
        KeyConditionExpression=Key('employee_id').eq(employee_id),
        ScanIndexForward=False # Latest first
    )
    
    for item in response.get("Items", []):
        if item.get("date") == date_str:
            # Get email from employee table since it might not be in attendance table
            emp_resp = employee_table.get_item(Key={"employee_id": employee_id})
            email = emp_resp.get("Item", {}).get("email", "N/A")
            
            if item.get("check_out"):
                return {
                    "status": "ALREADY_COMPLETED",
                    "name": item["name"],
                    "email": email,
                    "check_in": item["check_in"],
                    "check_out": item["check_out"],
                    "duration": item.get("spent_time", 0)
                }
            else:
                return {
                    "status": "ALREADY_CHECKED_IN",
                    "name": item["name"],
                    "email": email,
                    "check_in": item["check_in"],
                    "employee_id": employee_id
                }
    
    # 2. Get employee details
    emp_resp = employee_table.get_item(Key={"employee_id": employee_id})
    if "Item" not in emp_resp:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    employee = emp_resp["Item"]

    # 3. Save new check-in
    attendance_table.put_item(
        Item={
            "employee_id": employee_id,
            "timestamp": datetime.now().isoformat(),
            "date": date_str,
            "check_in": time_str,
            "check_out": None,
            "name": employee["name"]
        }
    )

    return {
        "status": "SUCCESS",
        "message": "Check-in successful",
        "employee_id": employee_id,
        "name": employee["name"],
        "email": employee.get("email", ""),
        "check_in_time": time_str
    }

@router.post("/check-out")
async def check_out(data: AttendanceCheckOut):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    response = attendance_table.query(
        KeyConditionExpression=Key('employee_id').eq(data.employee_id),
        ScanIndexForward=False,
        Limit=1
    )
    
    if not response.get("Items"):
        raise HTTPException(status_code=404, detail="No check-in record found")
    
    record = response["Items"][0]
    if record.get("check_out"):
        raise HTTPException(status_code=400, detail="Already checked out")

    check_in_time = datetime.strptime(record["check_in"], "%H:%M:%S")
    check_out_time = datetime.strptime(time_str, "%H:%M:%S")
    duration = check_out_time - check_in_time
    spent_hours = duration.total_seconds() / 3600

    attendance_table.update_item(
        Key={
            "employee_id": record["employee_id"],
            "timestamp": record["timestamp"]
        },
        UpdateExpression="SET check_out = :co, spent_time = :st",
        ExpressionAttributeValues={
            ":co": time_str,
            ":st": Decimal(str(round(spent_hours, 2)))
        }
    )

    return {
        "message": "Check-out successful",
        "check_out_time": time_str,
        "spent_hours": round(spent_hours, 2),
        "check_in_time": record["check_in"]
    }
@router.get("/status/{employee_id}")
async def get_status(employee_id: str):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    response = attendance_table.query(
        KeyConditionExpression=Key('employee_id').eq(employee_id),
        ScanIndexForward=False
    )
    
    # Get employee name
    emp_resp = employee_table.get_item(Key={"employee_id": employee_id})
    name = emp_resp.get("Item", {}).get("name", "Unknown")
    email = emp_resp.get("Item", {}).get("email", "N/A")

    for item in response.get("Items", []):
        if item.get("date") == date_str:
            if item.get("check_out"):
                return {
                    "status": "ALREADY_COMPLETED",
                    "name": name,
                    "email": email,
                    "check_in": item["check_in"],
                    "check_out": item["check_out"],
                    "duration": item.get("spent_time", 0)
                }
            else:
                return {
                    "status": "ALREADY_CHECKED_IN",
                    "name": name,
                    "email": email,
                    "check_in": item["check_in"],
                    "employee_id": employee_id
                }
    
    return {"status": "NOT_STARTED", "name": name}
    