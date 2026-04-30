from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AttendanceCheckIn(BaseModel):
    image_base64: str 

class AttendanceCheckOut(BaseModel):
    employee_id: str

class AttendanceRecord(BaseModel):
    employee_id: str
    date: str
    check_in: str
    check_out: Optional[str] = None
    spent_time: Optional[float] = None 
