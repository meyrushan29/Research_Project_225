
import sys
import os
from datetime import datetime

# Mock the path to allow imports
sys.path.append(os.getcwd())

from hydration.predict_Regression import get_current_time_slot

def test_time_slot():
    print("Testing Time Slot Automation...")
    slot = get_current_time_slot()
    hour = datetime.now().hour
    
    print(f"Current Hour: {hour}")
    print(f"Generated Slot: {slot}")
    
    # Basic validation
    valid_slots = [
        "Midnight-4 AM", "4 AM-8 AM", "8 AM-12 PM",
        "12 PM-4 PM", "4 PM-8 PM", "8 PM-Midnight"
    ]
    
    if slot in valid_slots:
        print("✅ SUCCESS: Slot is valid.")
    else:
        print(f"❌ FAILURE: Slot '{slot}' is invalid.")

if __name__ == "__main__":
    test_time_slot()
