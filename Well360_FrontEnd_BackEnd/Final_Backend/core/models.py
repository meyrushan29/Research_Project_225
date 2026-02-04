from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Profile Data (Persisted)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    # Relationships
    hydration_entries = relationship("HydrationData", back_populates="owner")
    lip_entries = relationship("LipAnalysis", back_populates="owner")

class HydrationData(Base):
    __tablename__ = "hydration_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Inputs stored as JSON for flexibility
    input_data = Column(JSON)
    
    # Key Results
    recommended_liters = Column(Float)
    risk_level = Column(String)
    
    owner = relationship("User", back_populates="hydration_entries")

class LipAnalysis(Base):
    __tablename__ = "lip_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    image_path = Column(String)
    prediction = Column(String)
    hydration_score = Column(Float)
    confidence = Column(Float)
    
    owner = relationship("User", back_populates="lip_entries")
