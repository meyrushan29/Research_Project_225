import joblib
import pandas as pd
from pathlib import Path

try:
    path = Path("Final_Backend/fitness/Models/training_features.pkl")
    features = joblib.load(path)
    print("--- EXPECTED FEATURES ---")
    print(features[:10])
    print("-------------------------")
except Exception as e:
    print(e)
