# 📁 File Reorganization Plan

**Date:** February 12, 2026  
**Status:** Ready for Execution

---

## 🎯 OBJECTIVE

Reorganize project files into a clean, logical structure that separates:
1. **Documentation** → `docs/`
2. **Utility Scripts** → `scripts/`
3. **Backend Tests** → `Final_Backend/tests/`
4. **Hydration Scripts** → `Final_Backend/hydration/scripts/`

---

## 📊 CURRENT FILE LOCATIONS (Root Level)

### Documentation Files (Move to `docs/`)
```
✓ CODE_CHANGES_FOR_PLAY_STORE.md
✓ LIP_ANALYSIS_IMPROVEMENTS.md
✓ PLAY_STORE_LAUNCH_ANALYSIS.md
✓ PLAY_STORE_QUICK_CHECKLIST.md
✓ QUICK_START_LIP_IMPROVEMENTS.md
✓ PROJECT_ANALYSIS_SUMMARY.md
✓ PROJECT_CLEANUP_ANALYSIS.md
✓ QUICK_CLEANUP_GUIDE.md
```

### Dataset Utility Scripts (Move to `scripts/dataset/`)
```
❌ auto_crop_dataset.py          → scripts/dataset/
❌ check_dataset_quality.py      → scripts/dataset/
❌ cleanup_data.py               → scripts/dataset/
```

### Model Training Scripts (Move to `scripts/model/`)
```
❌ retrain_lip_model.py          → scripts/model/
❌ test_lip_improvements.py      → scripts/model/
```

### Maintenance Scripts (Move to `scripts/maintenance/`)
```
❌ cleanup_project.py            → scripts/maintenance/
```

---

## 📊 BACKEND FILE LOCATIONS

### Backend Test Scripts (Move to `Final_Backend/tests/`)
```
❌ Final_Backend/test_retrained_model.py      → Final_Backend/tests/
❌ Final_Backend/check_hydration_health.py    → Final_Backend/tests/
```

### Backend Documentation (Move to `docs/backend/`)
```
❌ Final_Backend/HYDRATION_FINAL_STATUS.md           → docs/backend/
❌ Final_Backend/HYDRATION_INTEGRATION_ANALYSIS.md   → docs/backend/
❌ Final_Backend/HYDRATION_MODEL_RETRAIN_SUMMARY.md  → docs/backend/
```

---

## 📊 HYDRATION COMPONENT FILES

### Hydration Scripts (Move to `Final_Backend/hydration/scripts/`)
```
❌ Final_Backend/hydration/improve_lip_model.py      → hydration/scripts/
❌ Final_Backend/hydration/preprocess_all_lips.py    → hydration/scripts/
❌ Final_Backend/hydration/train_all_improved.py     → hydration/scripts/
```

### Hydration Training Logs (Move to `Final_Backend/hydration/logs/`)
```
❌ Final_Backend/hydration/training_log.txt          → hydration/logs/
❌ Final_Backend/hydration/training_log_2.txt        → hydration/logs/
❌ Final_Backend/hydration/training_log_3.txt        → hydration/logs/
```

---

## 🏗️ TARGET DIRECTORY STRUCTURE

```
Well360_FrontEnd_BackEnd/
│
├── .gitignore                          # Root gitignore
├── README.md                           # Project overview
│
├── docs/                               # 📚 All documentation
│   ├── backend/                        # Backend-specific docs
│   │   ├── HYDRATION_FINAL_STATUS.md
│   │   ├── HYDRATION_INTEGRATION_ANALYSIS.md
│   │   └── HYDRATION_MODEL_RETRAIN_SUMMARY.md
│   ├── CODE_CHANGES_FOR_PLAY_STORE.md
│   ├── LIP_ANALYSIS_IMPROVEMENTS.md
│   ├── PLAY_STORE_LAUNCH_ANALYSIS.md
│   ├── PLAY_STORE_QUICK_CHECKLIST.md
│   ├── QUICK_START_LIP_IMPROVEMENTS.md
│   ├── PROJECT_ANALYSIS_SUMMARY.md
│   ├── PROJECT_CLEANUP_ANALYSIS.md
│   ├── QUICK_CLEANUP_GUIDE.md
│   ├── HYDRATION_COMPONENT_OVERVIEW.md
│   └── FILE_REORGANIZATION_PLAN.md
│
├── scripts/                            # 🛠️ Utility scripts
│   ├── dataset/                        # Dataset processing
│   │   ├── auto_crop_dataset.py
│   │   ├── check_dataset_quality.py
│   │   └── cleanup_data.py
│   ├── model/                          # Model training
│   │   ├── retrain_lip_model.py
│   │   └── test_lip_improvements.py
│   └── maintenance/                    # Project maintenance
│       └── cleanup_project.py
│
├── Final_Backend/                      # 🔧 Backend application
│   ├── .gitignore
│   ├── main.py
│   ├── run.py
│   ├── requirements.txt
│   ├── app.db
│   │
│   ├── core/                           # Core utilities
│   ├── fitness/                        # Fitness module
│   ├── mental_health/                  # Mental health module
│   ├── static/                         # Static files
│   ├── img/                            # Image uploads
│   │
│   ├── hydration/                      # 🌊 Hydration module
│   │   ├── __init__.py
│   │   ├── predict_Regression.py       # Main prediction engine
│   │   ├── feature_eng.py              # Feature engineering
│   │   ├── imagePredict_mobilenet.py   # Lip image analysis
│   │   ├── lip_feature_extractor.py    # Lip features
│   │   ├── mediapipe_utils.py          # MediaPipe utilities
│   │   ├── dataLoad.py                 # Data loading
│   │   ├── dataLoad_images.py          # Image data loading
│   │   ├── preprocess.py               # Preprocessing
│   │   ├── preprocess_images.py        # Image preprocessing
│   │   ├── accumulate_data.py          # Data accumulation
│   │   ├── hydration_app.db            # Hydration database
│   │   │
│   │   ├── models/                     # Trained models
│   │   │   ├── xgb_regressor.pkl
│   │   │   ├── xgb_classifier.pkl
│   │   │   ├── preprocessor.pkl
│   │   │   ├── hydration_label_encoder.pkl
│   │   │   ├── LipModel_MobileNetV2.pth
│   │   │   ├── face_landmarker.task
│   │   │   ├── improved_training_history.json
│   │   │   ├── improved_training_metrics.json
│   │   │   └── training_metrics.json
│   │   │
│   │   ├── scripts/                    # Hydration-specific scripts
│   │   │   ├── improve_lip_model.py
│   │   │   ├── preprocess_all_lips.py
│   │   │   └── train_all_improved.py
│   │   │
│   │   └── logs/                       # Training logs
│   │       ├── training_log.txt
│   │       ├── training_log_2.txt
│   │       └── training_log_3.txt
│   │
│   ├── data/                           # Training data
│   ├── data_processed/                 # Processed data
│   ├── logs/                           # Application logs
│   ├── temp/                           # Temporary files
│   │
│   ├── tests/                          # 🧪 Backend tests
│   │   ├── test_retrained_model.py
│   │   └── check_hydration_health.py
│   │
│   └── venv/                           # Virtual environment
│
└── flutter_application_1/              # 📱 Flutter frontend
    ├── .gitignore
    ├── pubspec.yaml
    ├── lib/
    ├── android/
    ├── ios/
    └── test/
```

---

## 🔄 MIGRATION COMMANDS

### Phase 1: Create Directory Structure
```powershell
# Create new directories
New-Item -ItemType Directory -Path "docs\backend" -Force
New-Item -ItemType Directory -Path "scripts\dataset" -Force
New-Item -ItemType Directory -Path "scripts\model" -Force
New-Item -ItemType Directory -Path "scripts\maintenance" -Force
New-Item -ItemType Directory -Path "Final_Backend\tests" -Force
New-Item -ItemType Directory -Path "Final_Backend\hydration\scripts" -Force
New-Item -ItemType Directory -Path "Final_Backend\hydration\logs" -Force
```

### Phase 2: Move Documentation Files
```powershell
# Move root documentation to docs/
Move-Item "CODE_CHANGES_FOR_PLAY_STORE.md" "docs\"
Move-Item "LIP_ANALYSIS_IMPROVEMENTS.md" "docs\"
Move-Item "PLAY_STORE_LAUNCH_ANALYSIS.md" "docs\"
Move-Item "PLAY_STORE_QUICK_CHECKLIST.md" "docs\"
Move-Item "QUICK_START_LIP_IMPROVEMENTS.md" "docs\"
Move-Item "PROJECT_ANALYSIS_SUMMARY.md" "docs\"
Move-Item "PROJECT_CLEANUP_ANALYSIS.md" "docs\"
Move-Item "QUICK_CLEANUP_GUIDE.md" "docs\"

# Move backend documentation to docs/backend/
Move-Item "Final_Backend\HYDRATION_FINAL_STATUS.md" "docs\backend\"
Move-Item "Final_Backend\HYDRATION_INTEGRATION_ANALYSIS.md" "docs\backend\"
Move-Item "Final_Backend\HYDRATION_MODEL_RETRAIN_SUMMARY.md" "docs\backend\"
```

### Phase 3: Move Utility Scripts
```powershell
# Move dataset scripts
Move-Item "auto_crop_dataset.py" "scripts\dataset\"
Move-Item "check_dataset_quality.py" "scripts\dataset\"
Move-Item "cleanup_data.py" "scripts\dataset\"

# Move model scripts
Move-Item "retrain_lip_model.py" "scripts\model\"
Move-Item "test_lip_improvements.py" "scripts\model\"

# Move maintenance scripts
Move-Item "cleanup_project.py" "scripts\maintenance\"
```

### Phase 4: Move Backend Files
```powershell
# Move backend test files
Move-Item "Final_Backend\test_retrained_model.py" "Final_Backend\tests\"
Move-Item "Final_Backend\check_hydration_health.py" "Final_Backend\tests\"

# Move hydration scripts
Move-Item "Final_Backend\hydration\improve_lip_model.py" "Final_Backend\hydration\scripts\"
Move-Item "Final_Backend\hydration\preprocess_all_lips.py" "Final_Backend\hydration\scripts\"
Move-Item "Final_Backend\hydration\train_all_improved.py" "Final_Backend\hydration\scripts\"

# Move hydration logs
Move-Item "Final_Backend\hydration\training_log.txt" "Final_Backend\hydration\logs\"
Move-Item "Final_Backend\hydration\training_log_2.txt" "Final_Backend\hydration\logs\"
Move-Item "Final_Backend\hydration\training_log_3.txt" "Final_Backend\hydration\logs\"
```

---

## ⚠️ FILES TO DELETE

### Flutter One-Time Scripts
```powershell
Remove-Item "flutter_application_1\fix_flutter_issues.py" -Force
```

---

## ✅ VERIFICATION CHECKLIST

After migration:

### Root Directory
- [ ] Only essential files remain (README.md, .gitignore)
- [ ] No loose Python scripts
- [ ] No loose documentation files

### docs/ Directory
- [ ] All documentation organized
- [ ] Backend docs in docs/backend/
- [ ] Play Store docs present

### scripts/ Directory
- [ ] Dataset scripts in scripts/dataset/
- [ ] Model scripts in scripts/model/
- [ ] Maintenance scripts in scripts/maintenance/

### Final_Backend/
- [ ] No loose test files
- [ ] No loose documentation
- [ ] Tests in tests/
- [ ] Hydration scripts in hydration/scripts/
- [ ] Hydration logs in hydration/logs/

### Backend Still Works
- [ ] `python Final_Backend/run.py` starts successfully
- [ ] All imports work correctly
- [ ] API endpoints respond

### Flutter Still Works
- [ ] `flutter pub get` succeeds
- [ ] `flutter build apk --debug` succeeds

---

## 🔧 IMPORT PATH UPDATES NEEDED

After moving files, update import paths in:

### 1. scripts/dataset/auto_crop_dataset.py
No changes needed (standalone script)

### 2. scripts/dataset/check_dataset_quality.py
No changes needed (standalone script)

### 3. scripts/model/retrain_lip_model.py
Update path reference if needed:
```python
# OLD: sys.path.append(r"d:\PP2\...")
# NEW: Use relative imports or update path
```

### 4. Final_Backend/tests/check_hydration_health.py
Update imports:
```python
# OLD: from hydration.predict_Regression import AdvancedPredictor
# NEW: sys.path.append(os.path.dirname(os.path.dirname(__file__)))
#      from hydration.predict_Regression import AdvancedPredictor
```

---

## 📝 NOTES

1. **Backup First**: Create a backup before executing migrations
2. **Test Incrementally**: Test after each phase
3. **Update .gitignore**: Ensure new directories are properly configured
4. **Update README**: Document new structure
5. **Team Communication**: Notify team of structure changes

---

**Status:** Ready for Execution  
**Estimated Time:** 10 minutes  
**Risk Level:** Low (with backup)
