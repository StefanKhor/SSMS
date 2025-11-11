from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import engine, get_db

import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse

# Create database tables when startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shift Scheduler API")

# CORS middleware to connect Vue frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Staff CRUD API

@app.post("/api/staff/", response_model=schemas.StaffResponse, status_code=status.HTTP_201_CREATED, tags=["Staff"])
def create_staff(staff: schemas.StaffCreate, db: Session = Depends(get_db)):
    """Add new staff member"""
    db_staff = models.Staff(**staff.model_dump())
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

@app.get("/api/staff/", response_model=List[schemas.StaffResponse], tags=["Staff"])
def read_staff_list(db: Session = Depends(get_db)):
    """Retrieve all active staff members"""
    return db.query(models.Staff).filter(models.Staff.is_active == True).all()

@app.put("/api/staff/{staff_id}", response_model=schemas.StaffResponse, tags=["Staff"])
def update_staff(staff_id: int, staff: schemas.StaffCreate, db: Session = Depends(get_db)):
    """Update staff member information"""
    db_staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    for key, value in staff.model_dump().items():
        setattr(db_staff, key, value)
    
    db.commit()
    db.refresh(db_staff)
    return db_staff

@app.delete("/api/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Staff"])
def delete_staff(staff_id: int, db: Session = Depends(get_db)):
    """Delete staff member (soft delete, just mark is_active as False)"""
    db_staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    db_staff.is_active = False
    db.commit()
    return

# Shift CRUD API

@app.post("/api/shifts/", response_model=schemas.ShiftResponse, status_code=status.HTTP_201_CREATED, tags=["Shift"])
def create_shift(shift: schemas.ShiftBase, db: Session = Depends(get_db)):
    """Create a new shift record"""

    # Check for existing shift on the same date for the staff member
    existing_shift = db.query(models.Shift).filter(
        models.Shift.staff_id == shift.staff_id,
        models.Shift.shift_date == shift.shift_date
    ).first()

    if existing_shift:
        staff = db.query(models.Staff).filter(models.Staff.id == shift.staff_id).first()
        staff_name = staff.name if staff else 'Unknown'
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conflict: {staff_name} already has a shift scheduled on {shift.shift_date.strftime('%Y-%m-%d')}."
        )
    
    # Create new shift if no conflict
    db_shift = models.Shift(**shift.model_dump())
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)

    staff = db.query(models.Staff).filter(models.Staff.id == db_shift.staff_id).first()
    staff_name = staff.name if staff else 'Unknown'

    shift_data = schemas.ShiftResponse.model_validate(db_shift).model_dump()
    
    shift_data['staff_name'] = staff_name
    return schemas.ShiftResponse.model_validate(shift_data)

@app.get("/api/shifts/", response_model=List[schemas.ShiftResponse], tags=["Shift"])
def read_shifts(db: Session = Depends(get_db)):
    """Retrieve all shift records with staff names"""

    # Get all shifts
    shifts = db.query(models.Shift).all()

    # Create staff map
    staff_map = {s.id: s.name for s in db.query(models.Staff).all()}

    response_list = []
    for shift in shifts:
        shift_data = schemas.ShiftResponse.model_validate(shift).model_dump()
        
        # Add staff_name
        shift_data['staff_name'] = staff_map.get(shift.staff_id)
        response_list.append(schemas.ShiftResponse.model_validate(shift_data))
        
    return response_list

@app.put("/api/shifts/{shift_id}", response_model=schemas.ShiftResponse, tags=["Shift"])
def update_shift(shift_id: int, shift: schemas.ShiftBase, db: Session = Depends(get_db)):
    """Update Shift Info"""
    db_shift = db.query(models.Shift).filter(models.Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift record not found")
    
    # Update shift fields
    for key, value in shift.model_dump().items():
        setattr(db_shift, key, value)
    
    db.commit()
    db.refresh(db_shift)

    staff = db.query(models.Staff).filter(models.Staff.id == db_shift.staff_id).first()
    staff_name = staff.name if staff else 'Unknown'
    shift_data = schemas.ShiftResponse.model_validate(db_shift).model_dump()
    shift_data['staff_name'] = staff_name
    
    return schemas.ShiftResponse.model_validate(shift_data)

@app.delete("/api/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Shift"])
def delete_shift(shift_id: int, db: Session = Depends(get_db)):
    """Delete Shift"""
    db_shift = db.query(models.Shift).filter(models.Shift.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift record not found")

    db.delete(db_shift)
    db.commit()
    return

# Export Shift Schedule as Excel File

@app.get("/api/schedule/export/", tags=["Schedule"])
def export_schedule(db: Session = Depends(get_db), tags=["Export Data"]):
    """Export Shift Schedule as Excel File"""
    try:
        shifts = db.query(models.Shift).all()
        staff_map = {s.id: s.name for s in db.query(models.Staff).all()}

        if not shifts:
            raise HTTPException(status_code=404, detail="No shift data found to export")

        data = []
        for shift in shifts:
            data.append({
                'Shift ID': shift.id,
                'Shift Date': shift.shift_date.strftime('%Y-%m-%d'),
                'Staff ID': shift.staff_id,
                'Staff Name': staff_map.get(shift.staff_id, 'Unknown'),
                'Shift Type': shift.shift_type,
            })

        # Pandas DataFrame
        df = pd.DataFrame(data)

        output = BytesIO()
        df.to_excel(output, index=False, sheet_name='值班排班表')
        
        output.seek(0)

        filename = f"Shift_Schedule_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate export file: {e}")


from datetime import timedelta
from collections import deque


# Auto Schedule API

@app.post("/api/schedule/auto/", status_code=status.HTTP_201_CREATED, tags=["Auto Schedule"])
def auto_schedule(
    request: schemas.AutoScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Round Robin schedule generation between start_date and end_date
    """
    active_staff = db.query(models.Staff).filter(models.Staff.is_active == True).order_by(models.Staff.id).all()
    if not active_staff:
        raise HTTPException(status_code=400, detail="No active staff available for scheduling.")

    # Use deque for round-robin rotation
    staff_queue = deque(active_staff)
    
    start_dt = request.start_date
    end_dt = request.end_date
    
    # Prepare list of dates to schedule
    dates_to_schedule = []
    current_date = start_dt
    while current_date <= end_dt:
        dates_to_schedule.append(current_date)
        current_date += timedelta(days=1)
    
    # Delete old shifts in the date range
    db.query(models.Shift).filter(
        models.Shift.shift_date >= start_dt,
        models.Shift.shift_date <= end_dt
    ).delete(synchronize_session=False)
    db.commit()

    shifts_created = 0
    new_shift_records = []

    # Generate shifts using Round-Robin
    for day in dates_to_schedule:
        for shift_type in request.shift_types:
            # Get the next staff member from the front of the queue
            staff_member = staff_queue[0] 
            
            # Create a new shift record
            new_shift = models.Shift(
                staff_id=staff_member.id,
                shift_date=day,
                shift_type=shift_type
            )
            db.add(new_shift)
            new_shift_records.append(new_shift)
            
            # Rotate the queue for Round-Robin
            staff_queue.rotate(-1)
            shifts_created += 1

    db.commit()

    return {"message": f"Successfully generated {shifts_created} shifts from {start_dt} to {end_dt}."}