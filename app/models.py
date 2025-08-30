from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import Column, Integer, String, Float
from app.db import Base

from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db import Base

# -------------------------------
# SQLAlchemy ORM Models (Database)
# -------------------------------
class Load(Base):
    __tablename__ = "loads"

    id = Column(Integer, primary_key=True, index=True)
    load_id = Column(String, unique=True, index=True)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    pickup_datetime = Column(String)  # ISO format string
    delivery_datetime = Column(String)  # ISO format string
    equipment_type = Column(String)
    loadboard_rate = Column(Float)
    notes = Column(String, nullable=True)
    weight = Column(Integer, nullable=True)
    commodity_type = Column(String, nullable=True)
    miles = Column(Integer, nullable=True)
    dimensions = Column(String, nullable=True)
    num_of_pieces = Column(Integer, nullable=True)

# -------------------------------
# Pydantic Models (API Requests)
# -------------------------------
class SearchRequest(BaseModel):
    origin: str
    destination: str

class NegotiationRequest(BaseModel):
    load_id: str
    carrier_offer: float
    mc_number: str

class CreateLoadRequest(BaseModel):
    origin: str = Field(..., example="Dallas, TX")
    destination: str = Field(..., example="Atlanta, GA")
    loadboard_rate: float = Field(..., gt=0, example=2500.00)
    commodity: Optional[str] = Field(default="General", example="Electronics")
