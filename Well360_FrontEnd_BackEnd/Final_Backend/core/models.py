from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
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
    hydration_entries   = relationship("HydrationData",       back_populates="owner")
    lip_entries         = relationship("LipAnalysis",          back_populates="owner")
    mental_health_entries = relationship("MentalHealthAnalysis", back_populates="owner")
    fitness_entries     = relationship("FitnessAnalysis",      back_populates="owner")
    fitness_notifications = relationship("FitnessNotification", back_populates="owner")
    emotion_profile     = relationship("UserEmotionProfile",   back_populates="owner", uselist=False)
    muscle_radar_history = relationship("MuscleRadarHistory",  back_populates="owner")


class ExerciseMetadata(Base):
    __tablename__ = "exercise_metadata"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    body_part = Column(String) # Chest, Back, Legs, Arms, Shoulders, Core
    secondary_body_part = Column(String, nullable=True)
    target_category = Column(String, nullable=True) # Upper Body Push, Upper Body Pull, Lower Body, Core
    correct_tips = Column(JSON, nullable=True)
    wrong_tips = Column(JSON, nullable=True)

class FitnessNotification(Base):
    __tablename__ = "fitness_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    exercises_analyzed = Column(JSON) # e.g. ["bench press", "shoulder press"]
    targeted_parts = Column(JSON) # e.g. ["Chest", "Shoulders"]
    categories = Column(JSON) # e.g. ["Upper Body Push"]
    message = Column(String)
    
    owner = relationship("User", back_populates="fitness_notifications")

class FitnessAnalysis(Base):
    __tablename__ = "fitness_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Core Results
    exercise = Column(String) # e.g., "squat"
    form = Column(String)     # e.g., "correct", "wrong"
    confidence = Column(Float) # 0-100
    
    # Detailed Stats
    reps_total = Column(Integer)
    reps_correct = Column(Integer)
    reps_wrong = Column(Integer)
    hold_time = Column(Float) # in seconds

    # Media Paths
    video_path_input = Column(String, nullable=True) 
    video_path_normal = Column(String, nullable=True) 
    video_path_heatmap = Column(String, nullable=True)
    
    # Advanced Metrics (JSON)
    # Stores: breakdown of reps, ROM, stability score, specific recommendations
    details = Column(JSON, nullable=True)

    owner = relationship("User", back_populates="fitness_entries")

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

class MentalHealthAnalysis(Base):
    __tablename__ = "mental_health_analysis"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    emotion    = Column(String)
    confidence = Column(Float)
    source     = Column(String)   # "video" | "audio"

    # Audio-specific (optional)
    tone   = Column(String, nullable=True)
    energy = Column(String, nullable=True)

    # Video-specific (optional)
    faces_detected = Column(Integer, nullable=True)

    # Recommendation audit — which rotation index was shown this session
    rec_shown_index = Column(Integer, nullable=True, default=0)

    owner = relationship("User", back_populates="mental_health_entries")


class UserEmotionProfile(Base):
    """
    Per-user emotion pattern tracker.

    Updated every time an emotion analysis is saved.  Powers:
      - Personalised recommendation selection
      - Chronic-stress detection
      - Improving-trend detection
      - Per-user, per-emotion recommendation rotation (no repeats)
    """
    __tablename__ = "user_emotion_profiles"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # ── Lifetime emotion frequency counts ──────────────────────────────────
    happy_count   = Column(Integer, default=0)
    sad_count     = Column(Integer, default=0)
    angry_count   = Column(Integer, default=0)
    fear_count    = Column(Integer, default=0)
    disgust_count = Column(Integer, default=0)
    surprise_count = Column(Integer, default=0)
    neutral_count  = Column(Integer, default=0)
    total_analyses = Column(Integer, default=0)

    # ── Derived behavioural flags (recomputed on each update) ───────────────
    is_chronic_stress = Column(Boolean, default=False)  # ≥60 % negative in last 10 sessions
    is_improving      = Column(Boolean, default=False)  # positive ratio higher in recent 5 vs older 5
    is_first_time     = Column(Boolean, default=True)   # cleared after first analysis

    # ── Recommendation rotation state ──────────────────────────────────────
    # JSON map: {"happy": 2, "sad": 5, ...}  — offset into the candidate list
    rec_rotation = Column(JSON, default={})

    owner = relationship("User", back_populates="emotion_profile")

class HydrationSuggestion(Base):
    """
    Personalized suggestions for hydration based on various conditions.
    Supports both Form Prediction and Lip Image Analysis.
    """
    __tablename__ = "hydration_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Suggestion Metadata
    title = Column(String, nullable=False)  # Short title (e.g., "Stay Hydrated in Hot Weather")
    content = Column(Text, nullable=False)  # Detailed suggestion text
    category = Column(String, nullable=False)  # "general", "exercise", "weather", "symptoms", "diet", "lifestyle"
    priority = Column(Integer, default=1)  # 1=Low, 2=Medium, 3=High
    is_active = Column(Boolean, default=True)  # Enable/disable suggestions
    
    # Condition Matching (NULL means applies to all)
    # Form Prediction Conditions
    risk_level = Column(String, nullable=True)  # "Low", "Mild Dehydration", "High Dehydration", NULL=all
    min_recommended_liters = Column(Float, nullable=True)  # Minimum recommended water
    max_recommended_liters = Column(Float, nullable=True)  # Maximum recommended water
    activity_level = Column(String, nullable=True)  # "Sedentary", "Light", "Moderate", "Heavy", "Very Heavy"
    temperature_min = Column(Float, nullable=True)  # Minimum temperature (Celsius)
    temperature_max = Column(Float, nullable=True)  # Maximum temperature (Celsius)
    has_symptoms = Column(Boolean, nullable=True)  # If user has any symptoms (thirsty, dizzy, fatigue, headache)
    
    # Lip Analysis Conditions
    lip_prediction = Column(String, nullable=True)  # "Dehydrate", "Normal", NULL=all
    min_hydration_score = Column(Float, nullable=True)  # Minimum hydration score (0-100)
    max_hydration_score = Column(Float, nullable=True)  # Maximum hydration score (0-100)
    
    # Time-based conditions
    time_slots = Column(JSON, nullable=True)  # List of time slots, e.g., ["8 AM-12 PM", "12 PM-4 PM"]
    
    # Target Model
    model_type = Column(String, nullable=False)  # "form", "lip", "both"


class MuscleRadarHistory(Base):
    """
    Stores a completed 30-session Muscle Focus Radar snapshot.

    Every time a user completes 30 workout sessions (a 'cycle'), the current
    radar data is saved here and the live radar resets to zero.
    Users can browse these snapshots as a history of their training cycles.
    """
    __tablename__ = "muscle_radar_history"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), index=True)
    completed_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Which 30-session cycle this snapshot represents (1, 2, 3 …)
    cycle_number   = Column(Integer, nullable=False)
    # Global session index range that make up this cycle
    session_start  = Column(Integer, nullable=False)   # e.g. 1
    session_end    = Column(Integer, nullable=False)   # e.g. 30

    # Radar scores as percentages (0-100) for the 6 muscle groups
    # {"Arms": 80.0, "Chest": 60.0, "Back": 45.0, …}
    radar_data     = Column(JSON, nullable=False, default={})
    total_sessions = Column(Integer, default=30)

    owner = relationship("User", back_populates="muscle_radar_history")

