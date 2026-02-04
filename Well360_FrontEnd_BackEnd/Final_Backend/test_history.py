import requests
import json

BASE_URL = "http://localhost:8000"

def test_backend():
    # 1. Login
    print("Logging in...")
    try:
        res = requests.post(f"{BASE_URL}/auth/login-json", json={
            "email": "test@example.com", 
            "password": "password123" 
        })
        if res.status_code != 200:
            # Try registering if login fails (first run?)
            print("Login failed, trying register...")
            res_reg = requests.post(f"{BASE_URL}/auth/register", json={
                "email": "test@example.com", 
                "password": "password123" 
            })
            print(f"Register: {res_reg.status_code}")
            
            res = requests.post(f"{BASE_URL}/auth/login-json", json={
                "email": "test@example.com", 
                "password": "password123" 
            })
            
        if res.status_code != 200:
            print(f"Login failed: {res.text}")
            return
            
        token = res.json()["access_token"]
        print("Login Success. Token received.")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get Hydration History
        print("\nFetching Hydration History...")
        res_hist = requests.get(f"{BASE_URL}/history/hydration", headers=headers)
        print(f"Status: {res_hist.status_code}")
        print(f"Data: {res_hist.text[:100]}...")
        
        # 3. Get Trends
        print("\nFetching Trends...")
        res_trends = requests.get(f"{BASE_URL}/history/trends", headers=headers)
        print(f"Status: {res_trends.status_code}")
        if res_trends.status_code == 200:
            trends = res_trends.json()
            print(f"Keys: {trends.keys()}")
            print(f"Weekly Data Count: {len(trends.get('weekly', []))}")
        else:
            print(f"Error: {res_trends.text}")
            
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_backend()
