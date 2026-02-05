
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from hydration.imagePredict_mobilenet import load_model

def test_load_lip():
    try:
        model = load_model(["Dehydrate", "Normal"])
        print("✅ Lip model loaded successfully!")
    except Exception as e:
        print(f"❌ Lip model load failed: {e}")

if __name__ == "__main__":
    test_load_lip()
