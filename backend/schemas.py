from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional

class StaffBase(BaseModel):
    name: str
    age: int = Field(..., ge=18)
    position: str

class StaffCreate(StaffBase):
    pass

class StaffUpdate(StaffBase):
    is_active: bool

class StaffResponse(StaffBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class ShiftBase(BaseModel):
    staff_id: int
    shift_date: date
    shift_type: str

class ShiftResponse(ShiftBase):
    id: int
    staff_name: Optional[str] = None

    class Config:
        from_attributes = True

class AutoScheduleRequest(BaseModel):
    start_date: date
    end_date: date
    shift_types: List[str]