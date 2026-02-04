import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    from core.config import NUMERIC_COLS
    print("Import core.config SUCCESS")
except Exception as e:
    print(f"Import core.config FAILED: {e}")

try:
    from hydration.feature_eng import apply_feature_engineering
    print("Import hydration.feature_eng SUCCESS")
except Exception as e:
    print(f"Import hydration.feature_eng FAILED: {e}")
