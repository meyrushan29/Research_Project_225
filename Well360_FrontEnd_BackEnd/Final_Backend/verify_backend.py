import requests
import json

url = "http://127.0.0.1:8000/predict/form"

# Use dummy token mechanism or mock dependency if needed.
# Since auth is enabled, we might need a token.
# Assuming we can skip auth for local test or login first.
# Let's try to register/login first.

base_url = "http://127.0.0.1:8000"

def get_token():
    # Register/Login
    email = "test@example.com"
    password = "password123"
    
    try:
        requests.post(f"{base_url}/auth/register", json={"email": email, "password": password})
    except:
        pass # maybe already exists

    resp = requests.post(f"{base_url}/auth/login", data={"username": email, "password": password})
    if resp.status_code != 200:
        print("Login Failed:", resp.text)
        return None
    return resp.json()["access_token"]

def test_prediction():
    token = get_token()
    if not token: return

    headers = {"Authorization": f"Bearer {token}"}
    
    # Test Case: Dark Urine (Should have low health score impact)
    data = {
        "Age": 25,
        "Gender": "Male",
        "Weight": 70,
        "Height": 175,
        "Water_Intake_Last_4_Hours": 0.5,
        "Exercise_Time_Last_4_Hours": 30,
        "Physical_Activity_Level": "Moderate",
        "Urinated_Last_4_Hours": "Yes",
        "Urine_Color": 8, # Dark
        "Thirsty": "Yes",
        "Dizziness": "No",
        "Fatigue": "No",
        "Headache": "No",
        "Sweating_Level": "Moderate",
        "Time_Slot": "12 PM-4 PM",
        "Latitude": 0,
        "Longitude": 0
    }

    print("Sending Prediction Request (Dark Urine)...")
    resp = requests.post(url, json=data, headers=headers)
    
    if resp.status_code == 200:
        res = resp.json()
        print("\nPrediction Success!")
        print(f"Recommended Water: {res['recommended_total_water_liters']} L")
        print(f"Hydration Score: {res['hydration_score']}")
        print(f"Risk: {res['predicted_medical_conditions']}")
        print("-" * 20)
    else:
        print("Prediction Failed:", resp.text)

if __name__ == "__main__":
    try:
        test_prediction()
    except Exception as e:
        print(f"Connection failed: {e}")
