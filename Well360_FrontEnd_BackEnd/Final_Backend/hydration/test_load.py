
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from hydration.predict_Regression import AdvancedPredictor

def test_load():
    try:
        predictor = AdvancedPredictor()
        predictor.load_models()
        print("✅ Models loaded successfully!")
    except Exception as e:
        print(f"❌ Model load failed: {e}")

if __name__ == "__main__":
    test_load()
