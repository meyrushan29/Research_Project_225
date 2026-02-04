import joblib
from pathlib import Path

try:
    path = Path("Final_Backend/fitness/Models/training_features.pkl")
    features = joblib.load(path)
    print(f"--- COUNT: {len(features)} ---")
except Exception as e:
    print(e)
