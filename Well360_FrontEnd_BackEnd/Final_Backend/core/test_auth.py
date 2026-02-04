from auth import get_password_hash, verify_password

try:
    print("Testing Hash...")
    pwd = "test_password"
    h = get_password_hash(pwd)
    print(f"Hash success: {h}")
    
    print("Testing Verify...")
    v = verify_password(pwd, h)
    print(f"Verify success: {v}")
    
    print("Testing Long Password...")
    long_pwd = "a" * 100
    h_long = get_password_hash(long_pwd)
    print(f"Long Hash success: {h_long}")

except Exception as e:
    print(f"CRASH: {e}")
