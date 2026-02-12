#!/usr/bin/env python3
"""
Hydration Component Health Check Script
Verifies all critical components are working correctly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def check_dependencies():
    """Check all required packages"""
    print("🔍 Checking Dependencies...")
    try:
        import torch
        import torchvision
        import mediapipe
        import numpy
        import shap
        import numba
        import fastapi
        import sqlalchemy
        
        print(f"  ✅ PyTorch: {torch.__version__}")
        print(f"  ✅ MediaPipe: {mediapipe.__version__}")
        print(f"  ✅ NumPy: {numpy.__version__}")
        print(f"  ✅ Numba: {numba.__version__}")
        print(f"  ✅ SHAP: {shap.__version__}")
        print(f"  ✅ FastAPI: {fastapi.__version__}")
        
        # Check NumPy compatibility
        np_version = tuple(map(int, numpy.__version__.split('.')[:2]))
        if np_version >= (2, 4):
            print(f"  ⚠️  WARNING: NumPy {numpy.__version__} may cause issues with numba!")
            print("     Run: pip install 'numpy<2.4' --force-reinstall")
            return False
        
        return True
    except ImportError as e:
        print(f"  ❌ Missing dependency: {e}")
        return False

def check_models():
    """Check if models exist"""
    print("\n🤖 Checking Models...")
    models_dir = "hydration/models"
    required_models = {
        "LipModel_MobileNetV2.pth": "Lip Detection Model",
        "xgb_regressor.pkl": "Hydration Regressor",
        "xgb_classifier.pkl": "Risk Classifier",
        "preprocessor.pkl": "Feature Preprocessor",
        "face_landmarker.task": "MediaPipe FaceLandmarker"
    }
    
    all_good = True
    for model_file, description in required_models.items():
        path = os.path.join(models_dir, model_file)
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  ✅ {description}: {size_mb:.2f} MB")
        else:
            print(f"  ❌ Missing: {description}")
            all_good = False
    
    return all_good

def check_model_loading():
    """Test model loading"""
    print("\n💾 Testing Model Loading...")
    try:
        # Test lip model
        from hydration.imagePredict_mobilenet import load_model
        model = load_model(["Dehydrate", "Normal"])
        print(f"  ✅ Lip model loaded successfully")
        
        # Test predictor
        from hydration.predict_Regression import AdvancedPredictor
        predictor = AdvancedPredictor()
        print(f"  ✅ Hydration predictor loaded successfully")
        
        return True
    except Exception as e:
        print(f"  ❌ Model loading failed: {e}")
        return False

def check_database():
    """Check database connectivity"""
    print("\n🗄️  Checking Database...")
    try:
        from core.database import engine, Base
        from core.models import User, HydrationData, LipAnalysis
        from sqlalchemy import text
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"  ✅ Database connection successful")
        
        # Check tables
        inspector = sqlalchemy.inspect(engine)
        tables = inspector.get_table_names()
        required_tables = ['users', 'hydration_data', 'lip_analyses']
        
        for table in required_tables:
            if table in tables:
                print(f"  ✅ Table exists: {table}")
            else:
                print(f"  ⚠️  Table missing: {table}")
        
        return True
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
        return False

def check_api_health():
    """Check if API can be imported"""
    print("\n🌐 Checking API Health...")
    try:
        from main import app
        print(f"  ✅ FastAPI app imported successfully")
        print(f"  ✅ Title: {app.title}")
        print(f"  ✅ Version: {app.version}")
        
        # Count routes
        route_count = len(app.routes)
        print(f"  ✅ Registered routes: {route_count}")
        
        return True
    except Exception as e:
        print(f"  ❌ API import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("  HYDRATION COMPONENT HEALTH CHECK")
    print("=" * 60)
    
    results = {
        "Dependencies": check_dependencies(),
        "Models": check_models(),
        "Model Loading": check_model_loading(),
        "Database": check_database(),
        "API": check_api_health()
    }
    
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for component, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {component}: {'PASS' if status else 'FAIL'}")
        if not status:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED! System is ready for deployment.")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED. Please review the errors above.")
        return 1

if __name__ == "__main__":
    import sqlalchemy
    sys.exit(main())
