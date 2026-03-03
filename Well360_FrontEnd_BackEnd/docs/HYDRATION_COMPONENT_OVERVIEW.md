# 🌊 Hydration Component - Complete Overview

**Last Updated:** February 12, 2026  
**Location:** `Final_Backend/hydration/`  
**Status:** ✅ Production Ready

---

## 📋 EXECUTIVE SUMMARY

The Hydration Component is a sophisticated AI-powered system that predicts personalized water intake recommendations for the next 4 hours based on user health metrics, environmental conditions, and activity levels.

### Key Features
- **XGBoost ML Models** - Regression (water volume) + Classification (risk level)
- **Advanced Feature Engineering** - 15+ derived features from raw inputs
- **SHAP Explainability** - AI reasoning for predictions
- **Time-Aware Predictions** - Circadian rhythm consideration
- **Disease Risk Assessment** - Heat exhaustion, kidney stress, migraine, electrolyte imbalance
- **Real-time Weather Integration** - Temperature and humidity from Open-Meteo API

---

## 🏗️ ARCHITECTURE

### Core Files

```
hydration/
├── predict_Regression.py          # Main prediction engine (346 lines)
├── feature_eng.py                 # Feature engineering pipeline (202 lines)
├── imagePredict_mobilenet.py      # Lip image analysis (18,429 bytes)
├── lip_feature_extractor.py       # Advanced lip feature extraction (9,891 bytes)
├── dataLoad.py                    # Data loading utilities (6,589 bytes)
├── preprocess.py                  # Data preprocessing (5,216 bytes)
├── mediapipe_utils.py             # MediaPipe integration (4,410 bytes)
├── models/                        # Trained models directory
│   ├── xgb_regressor.pkl          # XGBoost regressor (1.3 MB)
│   ├── xgb_classifier.pkl         # XGBoost classifier (1.4 MB)
│   ├── preprocessor.pkl           # Feature preprocessor (4.9 KB)
│   ├── hydration_label_encoder.pkl # Label encoder (278 bytes)
│   ├── LipModel_MobileNetV2.pth   # Lip analysis model (12.3 MB)
│   └── face_landmarker.task       # MediaPipe face landmarks (3.8 MB)
└── hydration_app.db               # SQLite database (61 KB)
```

---

## 🔬 MAIN PREDICTION ENGINE

### File: `predict_Regression.py`

#### Class: `AdvancedPredictor`

**Purpose:** Core prediction engine with SHAP explainability

**Key Methods:**

1. **`load_models()`**
   - Loads XGBoost regressor, classifier, preprocessor, and label encoder
   - Patches sklearn compatibility issues (monotonic_cst, _fill_dtype)
   - Initializes SHAP TreeExplainer for AI reasoning
   - Status tracking with `is_loaded` flag

2. **`predict(user_input: Dict) -> Dict`**
   - **Input:** 15 required fields (see below)
   - **Output:** Comprehensive prediction with:
     - Recommended water intake (liters, next 4h)
     - Hydration risk level (Low/Moderate/High)
     - Hydration score (0-100)
     - AI reasoning (top 3 contributing factors)
     - Disease risk profile (4 conditions)
     - Environmental context
     - Personalized recommendations

3. **`get_top_factors(X_processed) -> List[str]`**
   - Uses SHAP values to identify top 3 features
   - Returns human-readable explanations
   - Example: "Heat Index (increases requirement)"

4. **`generate_recommendations(risk, disease_risk) -> List[str]`**
   - Rule-based recommendation engine
   - Considers hydration risk and disease risks
   - Returns 4-5 actionable recommendations

---

## 📊 REQUIRED INPUT FIELDS

### User Demographics (4 fields)
```python
"Age"                    # int, years
"Gender"                 # str, "Male" or "Female"
"Weight"                 # float, kg
"Height"                 # float, cm
```

### Hydration & Activity (3 fields)
```python
"Water_Intake_Last_4_Hours"                    # float, liters
"Exercise Time (minutes) in Last 4 Hours"      # float, minutes
"Physical_Activity_Level"                      # str, "Sedentary" | "Light" | "Moderate" | "Heavy" | "Very Heavy"
```

### Physiological Indicators (5 fields)
```python
"Urinated (Last 4 Hours)"                      # str, "Yes" or "No"
"Urine Color (Most Recent Urination)"          # int, 1-8 (1=clear, 8=dark)
"Sweating Level (Last 4 Hours)"                # str, "None" | "Light" | "Moderate" | "Heavy" | "Very Heavy"
```

### Symptoms (4 fields)
```python
"Thirsty (Right Now)"                          # str, "Yes" or "No"
"Dizziness (Right Now)"                        # str, "Yes" or "No"
"Fatigue / Tiredness (Right Now)"              # str, "Yes" or "No"
"Headache (Right Now)"                         # str, "Yes" or "No"
```

### Environmental (3 fields)
```python
"Temperature_C"                                # float, Celsius
"Humidity_%"                                   # float, percentage
"Time Slot (Select Your Current 4-Hour Window)" # str, auto-detected
```

**Time Slots:**
- `"Midnight-4 AM"` (0-4h)
- `"4 AM-8 AM"` (4-8h)
- `"8 AM-12 PM"` (8-12h)
- `"12 PM-4 PM"` (12-16h)
- `"4 PM-8 PM"` (16-20h)
- `"8 PM-Midnight"` (20-24h)

---

## 🧮 FEATURE ENGINEERING

### File: `feature_eng.py`

#### Class: `AdvancedFeatureEngineer`

**Derived Features (15 total):**

1. **Body Metrics**
   - `BMI` = Weight / (Height/100)²
   - `BSA` = √(Height × Weight / 3600)

2. **Hydration Metrics**
   - `Hydration_Index` = (Water_Intake × 1000) / Weight (ml/kg)
   - `Water_Deficit` = Total_Need - Water_Intake (clipped at 0)

3. **Activity & Environment**
   - `Activity_Factor` = Mapped from activity level (0.8-2.0)
   - `Sweating_Factor` = Mapped from sweating level (0-4)
   - `Heat_Index` = NOAA regression formula (F→C)
   - `Circadian_Factor` = Time-based multiplier (0.8-1.3)

4. **Health Indicators**
   - `Urine_Health_Score` = 10 - urine_color (if ≤3, else 0)
   - `Total_Symptom_Score` = Count of "Yes" symptoms (0-4)
   - `Medical_Risk_Flag` = Binary (0/1)

5. **Composite Score**
   - `Composite_Hydration_Score` = Weighted combination of 6 factors

**Calculation Details:**

```python
# Water Deficit Calculation
baseline_need = (Weight × 0.033) / 6  # L per 4h
exercise_loss = (Exercise_Minutes / 60) × (Activity_Factor × 0.4)
sweat_loss = Sweating_Factor × 0.15
total_need = baseline_need + exercise_loss + sweat_loss
Water_Deficit = max(0, total_need - Water_Intake)

# Heat Index (NOAA Formula)
T_F = Temperature_C × 1.8 + 32
HI_F = -42.379 + 2.049×T + 10.143×RH - 0.225×T×RH + ...
Heat_Index_C = (HI_F - 32) / 1.8
```

---

## 🎯 PREDICTION OUTPUT

### Sample Response Structure

```json
{
  "hydration_prediction": {
    "recommended_water_liters_next_4h": 1.25,
    "hydration_risk_level": "Moderate",
    "hydration_score": 72,
    "ai_reasoning": [
      "Heat Index (increases requirement)",
      "Water Deficit (increases requirement)",
      "Activity Factor (increases requirement)"
    ]
  },
  "disease_risk_profile": {
    "heat_exhaustion": "Moderate",
    "kidney_stress": "Low",
    "migraine": "Low",
    "electrolyte_imbalance": "Low"
  },
  "environmental_context": {
    "temperature_celsius": 32.5,
    "humidity_percent": 65.0,
    "time_window": "12 PM-4 PM"
  },
  "recommendations": [
    "Increase water intake gradually over the next 4 hours.",
    "Maintain electrolyte balance if sweating increases.",
    "Avoid excessive caffeine and sugary drinks.",
    "This guidance is preventive and not a medical diagnosis."
  ]
}
```

---

## 🔍 DISEASE RISK LOGIC

### Heat Exhaustion
```python
"High"     if Heat_Index >= 40°C
"Moderate" if Heat_Index >= 32°C
"Low"      otherwise
```

### Kidney Stress
```python
"High"     if Urine_Color >= 7
"Moderate" if Urine_Color >= 5
"Low"      otherwise
```

### Migraine
```python
"High"     if Water_Deficit > 1.0 L
"Moderate" if Water_Deficit > 0.5 L
"Low"      otherwise
```

### Electrolyte Imbalance
```python
"High" if Sweating_Factor >= 3 AND Water_Intake < 0.5 L
"Low"  otherwise
```

---

## 🌐 WEATHER API INTEGRATION

### Function: `get_current_weather(lat, lon)`

**API:** Open-Meteo (Free, no API key required)  
**Endpoint:** `https://api.open-meteo.com/v1/forecast`

**Parameters:**
- `latitude` - User location latitude
- `longitude` - User location longitude

**Returns:**
- `temperature_2m` - Temperature in Celsius
- `relative_humidity_2m` - Humidity percentage

**Fallback:** Returns (25.0°C, 50%) on error

---

## 🧪 MODEL DETAILS

### XGBoost Regressor (`xgb_regressor.pkl`)
- **Purpose:** Predicts water volume (liters) for next 4 hours
- **Size:** 1.3 MB
- **Input:** Preprocessed features (after feature engineering)
- **Output:** Float (0.0 - 3.0+ liters typical range)

### XGBoost Classifier (`xgb_classifier.pkl`)
- **Purpose:** Classifies hydration risk level
- **Size:** 1.4 MB
- **Output:** Encoded label (0/1/2) → "Low"/"Moderate"/"High"

### Preprocessor (`preprocessor.pkl`)
- **Type:** ColumnTransformer
- **Numeric Pipeline:** SimpleImputer → StandardScaler
- **Categorical Pipeline:** SimpleImputer → OneHotEncoder
- **Compatibility Patches:** Applied for sklearn 1.4+

### Label Encoder (`hydration_label_encoder.pkl`)
- **Mapping:** {0: "Low", 1: "Moderate", 2: "High"}

---

## 🖼️ LIP IMAGE ANALYSIS

### File: `imagePredict_mobilenet.py`

**Purpose:** Analyzes lip images to infer hydration status

**Model:** MobileNetV2 (PyTorch)  
**Size:** 12.3 MB  
**Input:** Lip image (RGB, preprocessed)  
**Output:** Hydration classification

**Integration with MediaPipe:**
- Face landmark detection
- Lip region extraction
- Feature extraction (color, texture, dryness indicators)

### File: `lip_feature_extractor.py`

**Advanced Features Extracted:**
- Lip color distribution (HSV analysis)
- Texture patterns (edge detection)
- Dryness indicators (crack detection)
- Moisture level estimation

---

## 🔧 COMPATIBILITY FIXES

### Sklearn Version Compatibility

**Issue:** Models trained on sklearn 1.3.x, running on 1.4.x  
**Solution:** Runtime patching in `load_models()`

```python
# Fix 1: SimpleImputer _fill_dtype attribute
num_imputer._fill_dtype = np.float64
cat_imputer._fill_dtype = object

# Fix 2: Tree models monotonic_cst attribute
model.monotonic_cst = None
for estimator in model.estimators_:
    estimator.monotonic_cst = None
```

---

## 📈 TRAINING METRICS

### Files in `models/`
- `training_metrics.json` - Original training results
- `improved_training_metrics.json` - Enhanced model performance
- `improved_training_history.json` - Training history logs

**Typical Performance:**
- Regressor R² Score: ~0.85-0.90
- Classifier Accuracy: ~88-92%
- Cross-validation stable

---

## 🚀 USAGE EXAMPLES

### 1. Terminal Usage (Standalone)

```bash
cd Final_Backend
python hydration/predict_Regression.py
```

**Interactive prompts for all inputs**

### 2. API Integration (FastAPI)

```python
from hydration.predict_Regression import AdvancedPredictor

predictor = AdvancedPredictor()

user_input = {
    "Age": 25,
    "Gender": "Male",
    "Weight": 70,
    "Height": 175,
    "Water_Intake_Last_4_Hours": 0.5,
    "Exercise Time (minutes) in Last 4 Hours": 30,
    "Physical_Activity_Level": "Moderate",
    "Urinated (Last 4 Hours)": "Yes",
    "Urine Color (Most Recent Urination)": 4,
    "Thirsty (Right Now)": "No",
    "Dizziness (Right Now)": "No",
    "Fatigue / Tiredness (Right Now)": "No",
    "Headache (Right Now)": "No",
    "Sweating Level (Last 4 Hours)": "Moderate",
    "Temperature_C": 28.0,
    "Humidity_%": 60.0,
    "Time Slot (Select Your Current 4-Hour Window)": "12 PM-4 PM"
}

result = predictor.predict(user_input)
print(result)
```

---

## ⚠️ IMPORTANT NOTES

### Data Validation
- All inputs are validated in `validate_input()`
- Missing fields raise `ValueError` with specific field names
- Type coercion handled in feature engineering

### Urine Color Logic
- If user hasn't urinated, default to 4 (neutral)
- Prevents asking for color when "Urinated" = "No"
- Realistic UX consideration

### Time Slot Automation
- Auto-detected from system time via `get_current_time_slot()`
- Can be overridden in API calls
- Critical for circadian factor calculation

### SHAP Explainability
- Requires SHAP library (`pip install shap`)
- Gracefully degrades if unavailable
- Returns "Reasoning currently unavailable" on error

---

## 🔄 INTEGRATION WITH MAIN BACKEND

### In `main.py` (FastAPI)

```python
from hydration.predict_Regression import AdvancedPredictor, get_current_time_slot

@app.post("/api/hydration/predict")
async def predict_hydration(data: HydrationInput):
    # Auto-add time slot
    data_dict = data.dict()
    data_dict["Time Slot (Select Your Current 4-Hour Window)"] = get_current_time_slot()
    
    # Get weather if lat/lon provided
    if data.latitude and data.longitude:
        temp, hum = get_current_weather(data.latitude, data.longitude)
        data_dict["Temperature_C"] = temp
        data_dict["Humidity_%"] = hum
    
    # Predict
    predictor = AdvancedPredictor()
    result = predictor.predict(data_dict)
    
    return result
```

---

## 📚 DEPENDENCIES

```txt
pandas>=1.5.0
numpy>=1.23.0
scikit-learn>=1.3.0
xgboost>=1.7.0
shap>=0.42.0
requests>=2.28.0
torch>=2.0.0
torchvision>=0.15.0
mediapipe>=0.10.0
```

---

## 🐛 KNOWN ISSUES & FIXES

### Issue 1: Sklearn Version Mismatch
**Status:** ✅ Fixed  
**Solution:** Runtime patching in `_patch_sklearn_object()`

### Issue 2: SHAP Warnings
**Status:** ✅ Suppressed  
**Solution:** `warnings.filterwarnings("ignore", category=UserWarning)`

### Issue 3: Urine Color UX
**Status:** ✅ Fixed  
**Solution:** Skip color question if user hasn't urinated

---

## 🎯 FUTURE ENHANCEMENTS

1. **Historical Tracking**
   - Store predictions in `hydration_app.db`
   - Trend analysis over time
   - Personalized baseline adjustment

2. **Advanced Lip Analysis**
   - Real-time camera integration
   - Multi-angle analysis
   - Temporal tracking

3. **Wearable Integration**
   - Heart rate variability
   - Skin temperature
   - Activity tracking data

4. **Personalization**
   - User-specific model fine-tuning
   - Adaptive recommendations
   - Seasonal adjustments

---

## 📞 TROUBLESHOOTING

### Models Won't Load
```bash
# Check file paths in core/config.py
# Verify models exist in hydration/models/
ls Final_Backend/hydration/models/
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### SHAP Errors
```bash
# Install specific version
pip install shap==0.42.1
```

### Weather API Timeout
- Fallback to default values (25°C, 50%)
- Check internet connection
- Verify lat/lon are valid

---

## ✅ HEALTH CHECK

Run this to verify component integrity:

```bash
cd Final_Backend
python check_hydration_health.py
```

**Expected Output:**
- ✅ All models loaded successfully
- ✅ Feature engineering working
- ✅ Prediction pipeline functional
- ✅ SHAP explainer initialized

---

**Document Status:** Complete  
**Maintainer:** Well360 Development Team  
**Last Review:** February 12, 2026
