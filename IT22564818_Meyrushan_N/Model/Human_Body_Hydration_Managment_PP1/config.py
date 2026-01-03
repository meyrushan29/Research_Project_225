import warnings
from pathlib import Path
import torch
import random

warnings.filterwarnings("ignore")

# ======================================================
# BASE PATHS
# ======================================================
BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
DATA_PATH = DATA_DIR / "dataset.csv"

MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ======================================================
# MODEL SAVE PATHS (TABULAR ML)
# ======================================================
MODEL_REG_PATH = MODEL_DIR / "hydration_regressor.pkl"
MODEL_CLF_PATH = MODEL_DIR / "hydration_classifier.pkl"

PREPROCESSOR_PATH = MODEL_DIR / "preprocessor.pkl"
ENCODER_PATH = MODEL_DIR / "hydration_label_encoder.pkl"

# (Optional / future)
MODEL_DISEASE_PATH = MODEL_DIR / "disease_classifier.pkl"
DISEASE_ENCODER_PATH = MODEL_DIR / "disease_encoder.pkl"

# ======================================================
# TRAINING PARAMETERS
# ======================================================
RANDOM_STATE = 42
TEST_SIZE = 0.2

# ======================================================
# FEATURE COLUMNS (MODEL INPUTS)
# ======================================================
NUMERIC_COLS = [
    "Age",
    "Weight",
    "Height",
    "Exercise Time (minutes) in Last 4 Hours",
    "Water_Intake_Last_4_Hours",
    "Urine Color (Most Recent Urination)",
    "Temperature_C",
    "Humidity_%",

    # ---- TIME WINDOW (SINGLE SOURCE OF TRUTH) ----
    "Time_Slot_Encoded",

    # ---- ENGINEERED NUMERIC FEATURES ----
    "BMI",
    "Hydration_Index",
    "Activity_Factor",
    "Sweating_Factor",
    "Urine_Health_Score",
    "Urination_Score",
    "Total_Symptom_Score",
    "Heat_Index",
    "Water_Deficit",
    "Composite_Hydration_Score"
]

CATEGORICAL_COLS = [
    "Gender",
    "Physical_Activity_Level",
    "Urinated (Last 4 Hours)",
    "Thirsty (Right Now)",
    "Dizziness (Right Now)",
    "Fatigue / Tiredness (Right Now)",
    "Headache (Right Now)",
    "Sweating Level (Last 4 Hours)",

    # Output-only indicators (NOT targets)
    "Heat_Stress_Risk",
    "Kidney_Stress_Risk",
    "Electrolyte_Imbalance_Risk"
]

DROP_COLS = ["UserID", "Date"]

# ======================================================
# TARGETS (SAFE & FINAL)
# ======================================================
TARGET_REG = "Recommended_Water_Next_4_Hours"
TARGET_CLF = "Hydration_Risk_Level"

TARGET_COLS = [TARGET_REG, TARGET_CLF]

# ======================================================
# RANDOM FOREST PARAMETERS
# ======================================================
RF_REGRESSOR_PARAMS = {
    "n_estimators": 300,
    "max_depth": 15,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "random_state": RANDOM_STATE
}

RF_CLASSIFIER_PARAMS = {
    "n_estimators": 300,
    "max_depth": 15,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "random_state": RANDOM_STATE,
    "class_weight": "balanced"
}

# ======================================================
# CATEGORY MAPPINGS
# ======================================================
TIME_SLOT_MAPPING = {
    "Midnight-4 AM": 0,
    "4 AM-8 AM": 1,
    "8 AM-12 PM": 2,
    "12 PM-4 PM": 3,
    "4 PM-8 PM": 4,
    "8 PM-Midnight": 5
}

ACTIVITY_MAPPING = {
    "Sedentary": 1.0,
    "Light": 1.2,
    "Moderate": 1.5,
    "Heavy": 2.0,
    "Very Heavy": 2.5
}

SWEATING_MAPPING = {
    "None": 0,
    "Light": 1,
    "Moderate": 2,
    "Heavy": 3,
    "Very Heavy": 4
}

HYDRATION_RISK_CATEGORIES = [
    "Very Low",
    "Low",
    "Moderate",
    "High"
]

# ======================================================
# OPTIONAL CNN (LIP IMAGE MODEL – ISOLATED)
# ======================================================
MODEL_OUT = MODEL_DIR / "LipModel.pth"

BATCH_SIZE = 8
EPOCHS = 10
LR = 0.001
IMG_SIZE = 224

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

torch.manual_seed(RANDOM_STATE)
random.seed(RANDOM_STATE)
