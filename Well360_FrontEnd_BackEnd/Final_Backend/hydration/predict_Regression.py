import pandas as pd
import numpy as np
import requests
from typing import Dict, Any, Tuple, List

from core.config import MODEL_REG_PATH, MODEL_CLF_PATH, PREPROCESSOR_PATH, ENCODER_PATH
from core.utils import setup_logging, load_pickle, calculate_unified_score
from hydration.feature_eng import apply_feature_engineering
from sklearn.impute import SimpleImputer
import numpy as np


LOG = setup_logging()

# =====================================================
# REQUIRED RAW INPUTS (USER-LEVEL ONLY)
# =====================================================
RAW_REQUIRED_FIELDS = [
    "Age", "Gender", "Weight", "Height",
    "Water_Intake_Last_4_Hours",
    "Exercise Time (minutes) in Last 4 Hours",
    "Physical_Activity_Level",
    "Urinated (Last 4 Hours)",
    "Urine Color (Most Recent Urination)",
    "Thirsty (Right Now)",
    "Dizziness (Right Now)",
    "Fatigue / Tiredness (Right Now)",
    "Headache (Right Now)",
    "Sweating Level (Last 4 Hours)",
    "Temperature_C", "Humidity_%",
    "Time Slot (Select Your Current 4-Hour Window)" # REQUIRED (Automated upstream)
]

# =====================================================
# TIME SLOT AUTOMATION
# =====================================================
def get_current_time_slot():
    """Returns the current 4-hour window based on system time."""
    from datetime import datetime
    hour = datetime.now().hour
    
    if 0 <= hour < 4: return "Midnight-4 AM"
    elif 4 <= hour < 8: return "4 AM-8 AM"
    elif 8 <= hour < 12: return "8 AM-12 PM"
    elif 12 <= hour < 16: return "12 PM-4 PM"
    elif 16 <= hour < 20: return "4 PM-8 PM"
    else: return "8 PM-Midnight"

# =====================================================
# MODEL PREDICTOR
# =====================================================
class AdvancedPredictor:

    def __init__(self):
        self.regressor = None
        self.classifier = None
        self.preprocessor = None
        self.label_encoder = None
        self.is_loaded = False

    def load_models(self):
        LOG.info("Loading trained hydration models...")
        self.regressor = load_pickle(MODEL_REG_PATH)
        self.classifier = load_pickle(MODEL_CLF_PATH)
        self.preprocessor = load_pickle(PREPROCESSOR_PATH)
        self.label_encoder = load_pickle(ENCODER_PATH)
        
        # -------------------------------------------------------------------------
        # SURGICAL FIX: Patch loaded imputers for compatibility
        # (Resolves both '_fill_dtype' missing error AND string-to-float error)
        # -------------------------------------------------------------------------
        try:
            # 1. Patch Numeric Imputer (Expects Float)
            num_imputer = self.preprocessor.preprocessor.named_transformers_['num'].named_steps['imputer']
            if not hasattr(num_imputer, "_fill_dtype"):
                 setattr(num_imputer, "_fill_dtype", np.float64)

            # 2. Patch Categorical Imputer (Expects Object/String)
            cat_imputer = self.preprocessor.preprocessor.named_transformers_['cat'].named_steps['imputer']
            if not hasattr(cat_imputer, "_fill_dtype"):
                 setattr(cat_imputer, "_fill_dtype", object)
                 
            LOG.info("Successfully patched SimpleImputer compatibility.")
        except Exception as e:
            LOG.warning(f"Could not patch imputers (might not be needed): {e}")

        # -------------------------------------------------------------------------
        # SKLEARN VERSION FIX (monotonic_cst missing in older models)
        # -------------------------------------------------------------------------
        self._patch_sklearn_object(self.regressor)
        self._patch_sklearn_object(self.classifier)

        self.is_loaded = True

    def _patch_sklearn_object(self, model):
        """Recursively inject monotonic_cst=None for Sklearn 1.4+ compatibility."""
        try:
            # Patch the main model if it's a tree-based model
            if not hasattr(model, "monotonic_cst"):
                setattr(model, "monotonic_cst", None)

            # Patch sub-estimators (e.g., Random Forest, Gradient Boosting)
            if hasattr(model, "estimators_"):
                for estimator in model.estimators_:
                    if not hasattr(estimator, "monotonic_cst"):
                        setattr(estimator, "monotonic_cst", None)
            
            LOG.info(f"Patched {type(model).__name__} for potential version mismatch.")
        except Exception as e:
            LOG.warning(f"Failed to patch {type(model).__name__}: {e}")

    def validate_input(self, user_input: Dict[str, Any]):
        missing = [f for f in RAW_REQUIRED_FIELDS if f not in user_input]
        if missing:
            raise ValueError(f"Missing inputs: {missing}")

    def preprocess_input(self, user_input: Dict[str, Any]) -> np.ndarray:
        df = pd.DataFrame([user_input])
        df = apply_feature_engineering(df)
        return self.preprocessor.transform(df)

    def predict(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_loaded:
            self.load_models()

        self.validate_input(user_input)
        X = self.preprocess_input(user_input)

        water = float(self.regressor.predict(X)[0])
        risk_code = self.classifier.predict(X)[0]
        hydration_risk = self.label_encoder.inverse_transform([risk_code])[0]

        # -------- Novel Rule-Based Preventive Risks --------
        temp = user_input["Temperature_C"]
        humidity = user_input["Humidity_%"]
        urine = user_input["Urine Color (Most Recent Urination)"]
        sweat = user_input["Sweating Level (Last 4 Hours)"]

        disease_risk_profile = {
            "heat_exhaustion": "High" if temp >= 32 else "Moderate" if temp >= 28 else "Low",
            "kidney_stress": "High" if urine >= 7 else "Moderate" if urine >= 5 else "Low",
            "migraine": "Moderate" if humidity >= 70 else "Low",
            "electrolyte_imbalance": "Moderate" if sweat in ["Heavy", "Very Heavy"] else "Low"
        }

        # Calculate Unified Score
        h_score = calculate_unified_score('form', water)

        return {
            "hydration_prediction": {
                "recommended_water_liters_next_4h": round(water, 2),
                "hydration_risk_level": hydration_risk,
                "hydration_score": h_score
            },
            "disease_risk_profile": disease_risk_profile,
            "environmental_context": {
                "temperature_celsius": temp,
                "humidity_percent": humidity,
                "time_window": user_input["Time Slot (Select Your Current 4-Hour Window)"]
            },
            "recommendations": self.generate_recommendations(
                hydration_risk, disease_risk_profile
            )
        }

    @staticmethod
    def generate_recommendations(risk, disease_risk) -> List[str]:
        recs = []
        if risk in ["High", "Moderate"]:
            recs.append("Increase water intake gradually over the next 4 hours.")
        if disease_risk["heat_exhaustion"] == "High":
            recs.append("High temperature detected – risk of heat exhaustion.")
        if disease_risk["electrolyte_imbalance"] != "Low":
            recs.append("Maintain electrolyte balance if sweating increases.")
        recs.append("Avoid excessive caffeine and sugary drinks.")
        recs.append("This guidance is preventive and not a medical diagnosis.")
        return recs

# =====================================================
# WEATHER API
# =====================================================
def get_current_weather(lat: float, lon: float) -> Tuple[float, float]:
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        c = r.json()["current"]
        return float(c["temperature_2m"]), float(c["relative_humidity_2m"])
    except Exception:
        return 25.0, 50.0

# =====================================================
# USER-FRIENDLY TERMINAL INPUT (FIXED LOGIC)
# =====================================================
def get_input_from_terminal() -> Tuple[Dict[str, Any], float, float]:
    print("\n========== USER DETAILS ==========\n")

    u = {}
    u["Age"] = int(input("Age: "))
    u["Gender"] = input("Gender (Male/Female): ")
    u["Weight"] = float(input("Weight (kg): "))
    u["Height"] = float(input("Height (cm): "))
    u["Water_Intake_Last_4_Hours"] = float(input("Water intake last 4 hours (L): "))
    u["Exercise Time (minutes) in Last 4 Hours"] = float(input("Exercise time (minutes): "))

    print("\nSelect Physical Activity Level:")
    print("1. Sedentary  2. Light  3. Moderate  4. Heavy  5. Very Heavy")
    activity_map = {
        "1": "Sedentary", "2": "Light", "3": "Moderate",
        "4": "Heavy", "5": "Very Heavy"
    }
    u["Physical_Activity_Level"] = activity_map.get(input("Enter option (1–5): "), "Light")

    print("\nSelect Sweating Level:")
    print("1. None  2. Light  3. Moderate  4. Heavy  5. Very Heavy")
    sweat_map = {
        "1": "None", "2": "Light", "3": "Moderate",
        "4": "Heavy", "5": "Very Heavy"
    }
    u["Sweating Level (Last 4 Hours)"] = sweat_map.get(input("Enter option (1–5): "), "Light")

    # Time Slot is now AUTOMATED
    u["Time Slot (Select Your Current 4-Hour Window)"] = get_current_time_slot()
    print(f"Time Slot Detected: {u['Time Slot (Select Your Current 4-Hour Window)']}")

    # -------- REALISTIC URINATION LOGIC --------
    u["Urinated (Last 4 Hours)"] = input(
        "Urinated in last 4 hours? (Yes/No): "
    ).strip().title()

    if u["Urinated (Last 4 Hours)"] == "Yes":
        u["Urine Color (Most Recent Urination)"] = int(
            input("Urine color (1 = clear, 8 = dark): ")
        )
    else:
        # ✔️ Skip asking urine color
        # ✔️ Assign safe neutral value
        u["Urine Color (Most Recent Urination)"] = 4

    u["Thirsty (Right Now)"] = input("Thirsty? (Yes/No): ")
    u["Dizziness (Right Now)"] = input("Dizziness? (Yes/No): ")
    u["Fatigue / Tiredness (Right Now)"] = input("Fatigue? (Yes/No): ")
    u["Headache (Right Now)"] = input("Headache? (Yes/No): ")

    print("\n========== LOCATION ==========")
    lat = float(input("Latitude: "))
    lon = float(input("Longitude: "))

    return u, lat, lon

# =====================================================
# MAIN OUTPUT
# =====================================================
if __name__ == "__main__":

    user_input, lat, lon = get_input_from_terminal()
    temp, hum = get_current_weather(lat, lon)

    user_input["Temperature_C"] = temp
    user_input["Humidity_%"] = hum

    predictor = AdvancedPredictor()
    result = predictor.predict(user_input)

    print("\n" + "=" * 70)
    print(" HUMAN BODY HYDRATION & HEALTH ANALYSIS ".center(70))
    print("=" * 70)

    # ---------------- Hydration ----------------
    hp = result["hydration_prediction"]
    print("\n[ Hydration Prediction ]")
    print("-" * 30)
    print(f"Recommended Water (Next 4h) : {hp['recommended_water_liters_next_4h']} L")
    print(f"Hydration Risk Level        : {hp['hydration_risk_level']}")

    # ---------------- Environment ----------------
    env = result["environmental_context"]
    print("\n[ Environmental Conditions ]")
    print("-" * 30)
    print(f"Temperature                : {env['temperature_celsius']} °C")
    print(f"Humidity                   : {env['humidity_percent']} %")

    # ---------------- Disease Risk ----------------
    print("\n[ Preventive Health Risks ]")
    print("-" * 30)
    for k, v in result["disease_risk_profile"].items():
        print(f"{k.replace('_', ' ').title():25}: {v}")

    # ---------------- Recommendations ----------------
    print("\n[ Personalized Recommendations ]")
    print("-" * 30)
    for i, r in enumerate(result["recommendations"], 1):
        print(f"{i}. {r}")

    print("\nNOTE: Preventive guidance only – not a medical diagnosis.")
    print("=" * 70)

