# PICKLE ERROR FIX - "Invalid Load Key"

## Problem

You're seeing this error:
```
Error: Exception: Error 500: {'detail': 'Failed to load pickle from ...\xgb_classifier.pkl: invalid load key, '\x06'.'}
```

## Root Cause

The XGBoost classifier pickle file was corrupted or saved with incompatible protocol/library versions. This can happen when:
- Models are saved with joblib but loaded with pickle (or vice versa)
- Different pickle protocols are used between save and load
- File corruption during save operation

## Status Check

✅ **Pickle files exist**: All 4 files are present in `hydration/models/`
✅ **Files can load with joblib**: Tested successfully  
❓ **Backend loading issue**: The backend uses `pickle.load()` but files were saved with `joblib.dump()`

## Solution: Use Joblib Consistently

### Step 1: Update `core/utils.py` to use joblib

The `load_pickle()` function currently uses standard `pickle.load()`, but the training script uses `joblib.dump()`. This mismatch can cause the "invalid load key" error.

**Current code:**
```python
def load_pickle(path: Path) -> Any:
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)  # ❌ Using pickle
    except Exception as e:
        raise IOError(f"Failed to load pickle from {path}: {e}")
```

**Fixed code:**
```python
import joblib  # Add this import at the top

def load_pickle(path: Path) -> Any:
    try:
        return joblib.load(path)  # ✅ Using joblib (matches training)
    except Exception as e:
        raise IOError(f"Failed to load pickle from {path}: {e}")
```

### Step 2: Restart Backend

After updating `core/utils.py`:

1. Stop the backend (Ctrl+C in backend terminal)
2. Restart: `python -m uvicorn main:app --reload`
3. Watch for successful startup: "Application startup complete."

### Step 3: Test

Try making a form prediction request from your Flutter app. The error should be resolved.

## Alternative: Retrain with Proper Protocol

If the above doesn't work, retrain the form models:

```powershell
cd Final_Backend
python TRAIN_ALL_HYDRATION_MODELS.py
# Choose option 2: Form Models Only
```

This will regenerate all 4 pickle files with consistent save/load methods.

## Technical Details

### Library Compatibility

- **joblib**: Optimized for large numpy arrays, scikit-learn objects
- **pickle**: Python's standard serialization, more general purpose
- **Mixing them**: Can cause "invalid load key" errors due to different file formats

### Best Practice

Always use the same library for save and load:

```python
# GOOD: Consistent usage
import joblib
joblib.dump(model, 'model.pkl')
model = joblib.load('model.pkl')

# BAD: Mixed usage (causes errors)
import joblib, pickle
joblib.dump(model, 'model.pkl')
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)  # ❌ ERROR!
```

## Files Affected

1. `hydration/models/xgb_regressor.pkl` - XGBoost regressor model
2. `hydration/models/xgb_classifier.pkl` - XGBoost classifier model (ERROR HERE)
3. `hydration/models/preprocessor.pkl` - Sklearn preprocessor
4. `hydration/models/hydration_label_encoder.pkl` - Label encoder

All 4 must be loaded with the same method used to save them.

## Quick Fix Command

Update `core/utils.py` manually (see Step 1 above), then:

```powershell
# Stop backend (Ctrl+C)
# Start backend
cd Final_Backend
python -m uvicorn main:app --reload
```

## Verification

After the fix, you should see in backend logs:
```
INFO: Loading trained hydration models...
INFO: Successfully patched SimpleImputer compatibility.
INFO: Application startup complete.
```

No errors about pickle/loading should appear.

---

**Status**: Ready to implement
**Impact**: Critical - blocks form prediction feature
**Time**: 2 minutes to fix
