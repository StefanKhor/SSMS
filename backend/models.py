from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from database import Base
from typing import List

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    position = Column(String)
    is_active = Column(Boolean, default=True)
    
    shifts: Mapped[List["Shift"]] = relationship(back_populates="staff")

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"))
    shift_date = Column(Date, index=True)
    shift_type = Column(String) 
    
    staff = relationship("Staff", back_populates="shifts")