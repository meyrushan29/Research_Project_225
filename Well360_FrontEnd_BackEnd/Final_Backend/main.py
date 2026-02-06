from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List
import base64
from io import BytesIO
from PIL import Image
import os
import uuid
import json
import datetime
from datetime import timedelta

from hydration.predict_Regression import AdvancedPredictor, get_current_weather, get_current_time_slot
from core.database import engine, get_db, Base
from core.models import User, HydrationData, LipAnalysis
import core.auth as auth

# =====================================================
# APP INITIALIZATION & DB SETUP
# =====================================================

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hydration Prediction API (Final Product)",
    version="2.0.0"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# CORS SETUP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = AdvancedPredictor()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# =====================================================
# AUTHENTICATION HELPERS
# =====================================================

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except auth.JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# =====================================================
# REQUEST MODELS
# =====================================================

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class FormPredictionRequest(BaseModel):
    Age: int
    Gender: str
    Weight: float
    Height: float
    Water_Intake_Last_4_Hours: float
    Exercise_Time_Last_4_Hours: float
    Physical_Activity_Level: str
    Urinated_Last_4_Hours: str
    Urine_Color: int
    Thirsty: str
    Dizziness: str
    Fatigue: str
    Headache: str
    Sweating_Level: str
    Time_Slot: str = None  # Optional: User selected slot
    Latitude: float
    Longitude: float

class ImageBase64Request(BaseModel):
    image_base64: str

# =====================================================
# ROUTES: AUTHENTICATION
# =====================================================

@app.post("/auth/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.get_password_hash(request.password)
    new_user = User(email=request.email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Compatible with Swagger UI
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Custom JSON Login for App
@app.post("/auth/login-json")
def login_json(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not auth.verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "email": user.email}

@app.get("/auth/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "age": current_user.age,
        "gender": current_user.gender,
        "weight": current_user.weight,
        "height": current_user.height
    }

# =====================================================
# ROUTES: PREDICTION & HISTORY (PROTECTED)
# =====================================================

@app.get("/weather/current")
def get_weather(lat: float, lon: float, current_user: User = Depends(get_current_user)):
    try:
        temp, hum = get_current_weather(lat, lon)
        return {
            "temperature_c": temp,
            "humidity_percent": hum,
            "location": {"lat": lat, "lon": lon}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {e}")

@app.post("/predict/form")
def predict_form(
    data: FormPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        print(f"Prediction for User: {current_user.email}")

        user_input = data.dict()
        user_input["Existing Diseases / Medical Conditions"] = "None"

        # Get Weather
        temp, hum = get_current_weather(data.Latitude, data.Longitude)
        user_input["Temperature_C"] = temp
        user_input["Humidity_%"] = hum

        # Map Pydantic Keys to ML Model Keys (EXACT MATCH with config.py)
        mapped_input = {
            "Age": user_input["Age"],
            "Gender": user_input["Gender"],
            "Weight": user_input["Weight"],  # REQUIRED: Simple "Weight"
            "Height": user_input["Height"],  # REQUIRED: Simple "Height"
            "Water_Intake_Last_4_Hours": user_input["Water_Intake_Last_4_Hours"], # REQUIRED: Snake case
            "Exercise Time (minutes) in Last 4 Hours": user_input["Exercise_Time_Last_4_Hours"], # REQUIRED: Human readable
            "Physical_Activity_Level": user_input["Physical_Activity_Level"], # REQUIRED: Snake case
            "Urinated (Last 4 Hours)": user_input["Urinated_Last_4_Hours"], # REQUIRED: Human readable
            "Urine Color (Most Recent Urination)": user_input["Urine_Color"], # REQUIRED: Human readable
            "Thirsty (Right Now)": user_input["Thirsty"], # REQUIRED: Human readable
            "Dizziness (Right Now)": user_input["Dizziness"], # REQUIRED: Human readable
            "Fatigue / Tiredness (Right Now)": user_input["Fatigue"], # REQUIRED: Human readable
            "Headache (Right Now)": user_input["Headache"], # REQUIRED: Human readable
            "Sweating Level (Last 4 Hours)": user_input["Sweating_Level"], # REQUIRED: Human readable
            "Time Slot (Select Your Current 4-Hour Window)": user_input.get("Time_Slot") or get_current_time_slot(), # Use provided or auto
            "Existing Diseases / Medical Conditions": "None",
            "Temperature_C": temp,
            "Humidity_%": hum
        }

        # Run Prediction
        print(f"DEBUG: Mapped Input being sent to Model:")
        print(json.dumps(mapped_input, indent=2, default=str))

        try:
             result = predictor.predict(mapped_input)
             print(f"DEBUG: Prediction Result: {result['hydration_prediction']}")
        except Exception as pred_err:
             import traceback
             traceback.print_exc()
             print(f"CRITICAL MODEL ERROR: {pred_err}")
             raise pred_err

        recs = result["recommendations"]

        # Risk Level Logic
        rec_water = result["hydration_prediction"]["recommended_water_liters_next_4h"]
        risk = "Normal"
        if rec_water > 2.0: risk = "High Dehydration"
        elif rec_water > 1.0: risk = "Mild Dehydration"

        # DELETE OLD ENTRIES FOR SAME TIME SLOT TODAY
        # This implements Option A: Replace old entry completely instead of keeping duplicates
        now_local = datetime.datetime.now()
        today_date_local = now_local.date()
        
        # Get the time slot from mapped input
        time_slot = mapped_input.get("Time Slot (Select Your Current 4-Hour Window)", "Unknown")
        
        # Query entries from last 30 hours (safe buffer to cover timezone edge cases)
        start_query = datetime.datetime.utcnow() - timedelta(hours=30)
        
        existing_entries = db.query(HydrationData).filter(
            HydrationData.user_id == current_user.id,
            HydrationData.timestamp >= start_query
        ).all()
        
        # Filter for today's entries with same time slot
        deleted_count = 0
        for entry in existing_entries:
            # Convert to local time
            entry_local_dt = entry.timestamp.replace(tzinfo=datetime.timezone.utc).astimezone() if entry.timestamp.tzinfo is None else entry.timestamp.astimezone()
            entry_date_local = entry_local_dt.date()
            
            # Only delete if it's TODAY and SAME TIME SLOT
            if entry_date_local == today_date_local and entry.input_data:
                entry_slot = entry.input_data.get("Time Slot (Select Your Current 4-Hour Window)", "")
                if entry_slot == time_slot:
                    db.delete(entry)
                    deleted_count += 1
        
        if deleted_count > 0:
            print(f"Deleted {deleted_count} old entry(ies) for slot '{time_slot}' on {today_date_local}")
        
        # SAVE NEW ENTRY TO DATABASE
        db_entry = HydrationData(
            user_id=current_user.id,
            input_data=user_input,
            recommended_liters=rec_water,
            risk_level=risk
        )
        
        # AUTO-UPDATE PROFILE
        current_user.age = mapped_input["Age"]
        current_user.gender = mapped_input["Gender"]
        current_user.weight = mapped_input["Weight"]
        current_user.height = mapped_input["Height"]
        
        db.add(db_entry)
        db.commit()

        return {
            "success": True,
            "recommended_total_water_liters": rec_water,
            "hydration_score": result["hydration_prediction"]["hydration_score"],
            "predicted_medical_conditions": result["disease_risk_profile"],
            "temperature_c": temp,
            "humidity_percent": hum,
            "ai_reasoning": result["hydration_prediction"].get("ai_reasoning", []),
            "recommendations": recs
        }
    except Exception as e:
        print(f"PREDICT ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/lip")
def predict_lip(
    data: ImageBase64Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Lazy import so backend can boot without torch/torchvision installed
        from hydration.imagePredict_mobilenet import predict_single

        # Decode and Save Temp
        os.makedirs("temp", exist_ok=True)
        temp_filename = f"temp/{uuid.uuid4()}.png"
        
        # Handle Data URI prefix if present
        img_str = data.image_base64
        if "," in img_str:
            img_str = img_str.split(",")[1]
            
        with open(temp_filename, "wb") as f:
            f.write(base64.b64decode(img_str))
            
        # Predict
        result = predict_single(temp_filename)

        if "error" in result:
             raise HTTPException(status_code=400, detail=result["error"])
        
        # Save to DB
        db_entry = LipAnalysis(
            user_id=current_user.id,
            image_path=result["saved_image_path"],
            prediction=result["prediction"],
            hydration_score=result["hydration_score"],
            confidence=result["confidence"]
        )
        db.add(db_entry)
        db.commit()
        
        # Convert paths to URLs for frontend
        if result.get("saved_image_path"):
            result["image_url"] = f"/uploads/{os.path.basename(result['saved_image_path'])}"
        if result.get("xai_heatmap_path"):
            result["xai_url"] = f"/uploads/{os.path.basename(result['xai_heatmap_path'])}"

        return result
        
    except Exception as e:
        print(f"LIP PREDICT ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup Temp (Always)
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.post("/predict/fitness/video")
def predict_fitness_video(
    video: UploadFile = File(...),
    enable_heatmap: bool = Form(True),
    current_user: User = Depends(get_current_user)
):
    try:
        # Lazy import so backend can boot even if MediaPipe stack is unavailable.
        # If fitness dependencies are missing/broken, we fail this endpoint only.
        try:
            from fitness.api_handler import get_processor
        except Exception as imp_err:
            raise HTTPException(
                status_code=503,
                detail=f"Fitness processor unavailable: {imp_err}"
            )

        # Create temp file
        os.makedirs("temp", exist_ok=True)
        temp_filename = f"temp/{uuid.uuid4()}_{video.filename}"
        
        with open(temp_filename, "wb") as f:
            f.write(video.file.read())
            
        # Process Video
        # Save output to img/fitness_processed (which is mounted)
        output_dir = "img/fitness_processed"
        processor = get_processor()
        result = processor.process_video(temp_filename, output_dir=output_dir, enable_heatmap=enable_heatmap)
        
        if "error" in result:
             if "No human detected" in result["error"]:
                 raise HTTPException(status_code=400, detail=result["error"])
             raise HTTPException(status_code=500, detail=result["error"])
        
        # Add URL to result
        result["video_url"] = f"/fitness_videos/{result['processed_video_filename']}"
        
        if "video_filename_normal" in result:
             result["video_url_normal"] = f"/fitness_videos/{result['video_filename_normal']}"
        if "video_filename_heatmap" in result:
             result["video_url_heatmap"] = f"/fitness_videos/{result['video_filename_heatmap']}"
        
        return result
        
    except Exception as e:
        print(f"FITNESS PREDICT ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup input temp file
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.get("/history/hydration")
def get_hydration_history(
    start_time: str = None,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(HydrationData).filter(HydrationData.user_id == current_user.id)
    
    if start_time:
        try:
            # Expect ISO format from frontend
            # FIX: Convert to naive UTC to match database storage (datetime.utcnow)
            import dateutil.parser
            start_dt = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            start_dt = start_dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            
            query = query.filter(HydrationData.timestamp >= start_dt)
        except Exception as e:
            print(f"Date parse error: {e}")
            pass # Ignore invalid dates and return all

    entries = query.order_by(HydrationData.timestamp).all()
    return [{
        "date": e.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "liters": e.recommended_liters,
        "risk": e.risk_level
    } for e in entries]

@app.get("/history/lip")
def get_lip_history(
    start_time: str = None,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(LipAnalysis).filter(LipAnalysis.user_id == current_user.id)
    
    if start_time:
        try:
            start_dt = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            start_dt = start_dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            query = query.filter(LipAnalysis.timestamp >= start_dt)
        except Exception as e:
            print(f"Date parse error: {e}")
            pass

    entries = query.order_by(LipAnalysis.timestamp).all()
    # Serve from the new mounted /uploads route
    return [{
        "date": e.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prediction": e.prediction,
        "hydration_score": e.hydration_score,
        "image_url": f"/uploads/{os.path.basename(e.image_path)}" if e.image_path else None
    } for e in entries]

@app.delete("/history/clear")
def clear_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Clear Hydration Data
    db.query(HydrationData).filter(HydrationData.user_id == current_user.id).delete()
    
    # 2. Clear Lip Analysis Data & Files
    lip_entries = db.query(LipAnalysis).filter(LipAnalysis.user_id == current_user.id).all()
    for entry in lip_entries:
        # Check if path exists and is a file before removing
        if entry.image_path and os.path.exists(entry.image_path):
            try:
                os.remove(entry.image_path)
            except Exception as e:
                print(f"Warning: Could not delete file {entry.image_path}: {e}")
    
    # Delete records from DB
    db.query(LipAnalysis).filter(LipAnalysis.user_id == current_user.id).delete()
    
    db.commit()
    return {"message": "History and Scan data cleared successfully"}

# Helper: Convert UTC (Naive from DB) to Local System Time
def to_system_local(dt_utc):
    if dt_utc is None: return None
    # Assume stored as Naive UTC
    utc_aware = dt_utc.replace(tzinfo=datetime.timezone.utc)
    return utc_aware.astimezone() # Converts to System Local Time

@app.get("/history/trends")
def get_hydration_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Use Local Date for "Today"
        now_local = datetime.datetime.now()
        today_date_local = now_local.date()
        
        # Monthly Range (Last 30 days)
        start_date_local = today_date_local - timedelta(days=29)
        
        # We need to fetch enough UTC data to cover the Local start date.
        # Safest is to fetch (Start Date - 1 Day) in UTC.
        # But for simplicity, let's just fetch everything reasonably recent (e.g. 31 days)
        start_dt_query = datetime.datetime.utcnow() - timedelta(days=32)
        
        entries = db.query(HydrationData).filter(
            HydrationData.user_id == current_user.id,
            HydrationData.timestamp >= start_dt_query
        ).all()
        
        # Aggregate using LOCAL Time
        daily_map = {}
        # Pre-fill last 30 days
        for i in range(30):
            d = start_date_local + timedelta(days=i)
            daily_map[d.isoformat()] = 0.0

        hourly_map = {h: 0.0 for h in range(24)}
        today_iso = today_date_local.isoformat()
        
        # Helper to parse slot to hours
        def parse_slot_hours(slot_name):
            slot_name = slot_name.lower().strip()
            # "Midnight-4 AM", "4 AM-8 AM", "8 AM-12 PM", "12 PM-4 PM", "4 PM-8 PM", "8 PM-Midnight"
            if "midnight-4 am" in slot_name: return [0, 1, 2, 3]
            if "4 am-8 am" in slot_name: return [4, 5, 6, 7]
            if "8 am-12 pm" in slot_name: return [8, 9, 10, 11]
            if "12 pm-4 pm" in slot_name: return [12, 13, 14, 15]
            if "4 pm-8 pm" in slot_name: return [16, 17, 18, 19]
            if "8 pm-midnight" in slot_name: return [20, 21, 22, 23]
            return []
        
        for e in entries:
            # CONVERT TO LOCAL
            local_dt = to_system_local(e.timestamp)
            entry_date = local_dt.date()
            
            # Filter out if older than our start window
            if entry_date < start_date_local: continue
            
            date_str = entry_date.isoformat()
            
            # Extract Slot
            slot = "Unknown"
            if e.input_data:
                slot = e.input_data.get("Time Slot (Select Your Current 4-Hour Window)", "Unknown")
            
            # Extract Value
            val = 0.0
            if e.input_data and "Water_Intake_Last_4_Hours" in e.input_data:
                try:
                    val = float(e.input_data["Water_Intake_Last_4_Hours"])
                except: pass
            
            # Add to daily total
            if date_str in daily_map:
                daily_map[date_str] += val
            
            # Hourly breakdown (Today Local)
            if date_str == today_iso:
                hours = parse_slot_hours(slot)
                if not hours:
                    # Fallback to submission hour if slot unknown
                    hours = [local_dt.hour]
                
                # Distribute value evenly across the slot hours
                # This ensures "Missed Intake" logic (checking if > 0) sees activity for ALL hours in the slot
                per_hour_val = val / len(hours) if len(hours) > 0 else 0
                for h in hours:
                    # Only update if valid hour (0-23)
                    if 0 <= h < 24:
                        hourly_map[h] += per_hour_val
        
        # ... logic continues same ...
        sorted_dates = sorted(daily_map.keys())
        full_data = [{"date": d, "liters": round(daily_map[d], 2)} for d in sorted_dates]
        
        hourly_data = [{"hour": f"{h:02d}:00", "liters": round(hourly_map[h], 2)} for h in range(24)]
        today_total = sum(hourly_map.values())

        weekly_data = full_data[-7:]
        weekly_total = sum(x["liters"] for x in weekly_data)
        monthly_total = sum(x["liters"] for x in full_data)
        
        return {
            "hourly": hourly_data,
            "weekly": weekly_data,
            "monthly": full_data,
            "today_total_liters": round(today_total, 2),
            "weekly_total_liters": round(weekly_total, 2),
            "monthly_total_liters": round(monthly_total, 2),
            "weekly_avg": round(weekly_total / 7, 2)
        }
        
    except Exception as e:
        print(f"TRENDS ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tracker/dashboard")
def get_daily_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        now_local = datetime.datetime.now()
        today_date_local = now_local.date()
        
        # Fetch entries from last 24h UTC (safe buffer)
        start_query = datetime.datetime.utcnow() - timedelta(days=1, hours=6)
        
        recent_entries = db.query(HydrationData).filter(
            HydrationData.user_id == current_user.id,
            HydrationData.timestamp >= start_query
        ).all()
        
        # Filter for TODAY LOCAL and sum intake
        total_intake = 0.0
        for entry in recent_entries:
            local_dt = to_system_local(entry.timestamp)
            if local_dt.date() != today_date_local:
                 continue
                 
            if not entry.input_data: continue
            
            # Extract water intake value
            if "Water_Intake_Last_4_Hours" in entry.input_data:
                try: 
                    val = float(entry.input_data["Water_Intake_Last_4_Hours"])
                    total_intake += val
                except: 
                    continue
                    
        # 2. Get Next 4 Hours Goal (Latest Recommendation)
        latest_hydration = db.query(HydrationData).filter(
            HydrationData.user_id == current_user.id
        ).order_by(HydrationData.timestamp.desc()).first()
        
        next_goal = latest_hydration.recommended_liters if latest_hydration else 0.0
        
        # 3. Get Current Lip Status
        latest_lip = db.query(LipAnalysis).filter(
             LipAnalysis.user_id == current_user.id
        ).order_by(LipAnalysis.timestamp.desc()).first()
        
        lip_status = {
            "status": latest_lip.prediction if latest_lip else "Unknown",
            "score": latest_lip.hydration_score if latest_lip else 0,
            "last_updated": to_system_local(latest_lip.timestamp).strftime("%Y-%m-%dT%H:%M:%SZ") if latest_lip else None
        }
        
        # 4. Calculate PERSONALIZED DAILY GOAL
        weight = float(current_user.weight) if current_user.weight else 60.0
        height = float(current_user.height) if current_user.height else 170.0
        gender = str(current_user.gender) if current_user.gender else "Male"
        age = int(current_user.age) if current_user.age else 25
        
        base_goal = weight * 0.033
        
        height_add = 0.0
        if height > 185: height_add = 0.3
        elif height > 175: height_add = 0.1
        
        gender_add = 0.0
        if gender.lower() in ["male", "m", "man"]:
             gender_add = 0.5
        
        age_add = 0.0
        if age < 30: age_add = 0.2
        elif age > 55: age_add = -0.1

        # Weather Adjustment
        weather_add = 0.0
        if latest_hydration and latest_hydration.input_data:
             try:
                 last_temp = float(latest_hydration.input_data.get("Temperature_C", 25.0))
                 if last_temp > 30: weather_add = 0.5
                 elif last_temp > 25: weather_add = 0.2
             except: pass
        
        daily_goal = base_goal + height_add + gender_add + age_add + weather_add
        daily_goal = round(daily_goal, 2)
        
        # 5. Progress Stats
        percent = 0.0
        if daily_goal > 0:
            percent = (total_intake / daily_goal) * 100
            
        if percent >= 100: status_msg = "Goal Met! Great job!"
        elif percent >= 75: status_msg = "Almost there!"
        elif percent >= 50: status_msg = "Halfway there."
        else: status_msg = "Keep drinking water."
        
        return {
            "date": today_date_local.isoformat(),
            "total_water_intake_today_liters": round(total_intake, 2),
            "next_4_hours_water_need_liters": round(next_goal, 2),
            "daily_goal_liters": daily_goal,
            "percentage_completed": round(percent, 1),
            "goal_status": status_msg,
            "current_lip_status": lip_status
        }
        
    except Exception as e:
        print(f"TRACKER ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api-status")
def api_status():
    return {"status": "Final Product API Running", "auth": "Enabled"}

# =====================================================
# STATIC FILES & UPLOADS
# =====================================================
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount user uploads (SAFE persistence, outside static build folder)
os.makedirs("img/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="img/uploads"), name="uploads")

# Mount fitness processed videos
os.makedirs("img/fitness_processed", exist_ok=True)
app.mount("/fitness_videos", StaticFiles(directory="img/fitness_processed"), name="fitness_videos")

# Mount the 'static' directory (Flutter Web Build)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Catch-all for SPA routing
@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return FileResponse("static/index.html")