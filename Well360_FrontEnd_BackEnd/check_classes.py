import joblib
from pathlib import Path

try:
    path = Path("Final_Backend/fitness/Models/label_encoder.pkl")
    encoder = joblib.load(path)
    print("--- CLASSES ---")
    print(encoder.classes_)
    print("-------------------------")
except Exception as e:
    print(e)
