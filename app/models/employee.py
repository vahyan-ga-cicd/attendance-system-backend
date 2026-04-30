from pydantic import BaseModel

from typing import Optional
from datetime import datetime

class EmployeeCreate(BaseModel):
    name: str
    department: str
    email: Optional[str] = None
    employee_id: Optional[str] = None # Auto-generated if not provided
    created_at: Optional[str] = datetime.now().isoformat()