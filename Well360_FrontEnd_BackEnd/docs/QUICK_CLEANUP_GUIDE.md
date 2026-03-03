# 🧹 Quick Cleanup Guide

**Last Updated:** February 12, 2026

---

## ⚡ FASTEST METHOD (Recommended)

### Option 1: Automated Script (Safest)

```powershell
# Navigate to project root
cd d:\PP2\Research_Project_225\Well360_FrontEnd_BackEnd

# Run the cleanup script
python cleanup_project.py
```

**What it does:**
- ✅ Removes Python cache files (__pycache__, *.pyc)
- ✅ Removes log files (*.log)
- ✅ Removes temporary test images
- ✅ Runs `flutter clean`
- ✅ Removes analysis output files
- ✅ Cleans temp directories
- ✅ Shows summary of freed space

**Safe:** Asks for confirmation before deleting

---

### Option 2: Manual Commands (Faster, No Confirmation)

```powershell
# Navigate to project root
cd d:\PP2\Research_Project_225\Well360_FrontEnd_BackEnd

# Delete Python cache
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Filter *.pyc | Remove-Item -Force

# Delete logs
Get-ChildItem -Path . -Recurse -Filter *.log | Remove-Item -Force

# Delete test images
Remove-Item Final_Backend\img\result_*.png -Force -ErrorAction SilentlyContinue
Remove-Item Final_Backend\img\rejected_*.png -Force -ErrorAction SilentlyContinue

# Delete analysis files
Remove-Item flutter_application_1\analysis_full.txt -Force -ErrorAction SilentlyContinue
Remove-Item flutter_application_1\analyze_output.txt -Force -ErrorAction SilentlyContinue

# Clean Flutter
cd flutter_application_1
flutter clean
cd ..

Write-Host "`n✅ Cleanup complete!" -ForegroundColor Green
```

---

## 📋 VERIFICATION

After cleanup, verify everything still works:

### 1. Check Backend
```powershell
cd Final_Backend
python run.py
# Should start without errors
# Press Ctrl+C to stop
```

### 2. Check Flutter
```powershell
cd flutter_application_1
flutter pub get
flutter build apk --debug
# Should build successfully
```

### 3. Check Git Status
```powershell
git status
# Should NOT show __pycache__, *.pyc, *.log, build/, etc.
```

---

## 🎯 WHAT GETS DELETED

| Category | Files | Size Impact |
|----------|-------|-------------|
| Python cache | `__pycache__/`, `*.pyc` | ~50-100 MB |
| Logs | `*.log` | ~1-5 MB |
| Test images | `result_*.png`, `rejected_*.png` | ~15-20 MB |
| Flutter build | `build/`, `.dart_tool/` | ~1+ GB |
| Analysis files | `analysis_*.txt` | ~15 KB |
| **TOTAL** | | **~1.5+ GB** |

---

## 🔒 WHAT STAYS SAFE

✅ **Source code** (all `.py`, `.dart` files)  
✅ **Dependencies** (`venv/`, `node_modules/`)  
✅ **Database** (`app.db`)  
✅ **Models** (`.h5`, `.pkl` files)  
✅ **Configuration** (`.yaml`, `.json` files)  
✅ **Documentation** (`.md` files)  

---

## ⚠️ TROUBLESHOOTING

### "Access Denied" errors
**Solution:** Close all IDEs and terminals, run PowerShell as Administrator

### "Flutter command not found"
**Solution:** Skip flutter clean or run manually:
```powershell
cd flutter_application_1
flutter clean
```

### Backend won't start after cleanup
**Solution:** Reinstall dependencies:
```powershell
cd Final_Backend
pip install -r requirements.txt
```

### Flutter won't build after cleanup
**Solution:** Get dependencies again:
```powershell
cd flutter_application_1
flutter pub get
flutter clean
flutter pub get
```

---

## 📅 MAINTENANCE SCHEDULE

### Daily (During Active Development)
```powershell
# Quick clean before major builds
cd flutter_application_1
flutter clean
```

### Weekly
```powershell
# Full cleanup
python cleanup_project.py
```

### Before Commits
```powershell
# Check what will be committed
git status

# Should NOT see:
# - __pycache__/
# - *.pyc
# - *.log
# - build/
# - analysis_*.txt
```

---

## 🚀 NEXT STEPS

After cleanup:

1. ✅ **Commit .gitignore files**
   ```powershell
   git add .gitignore Final_Backend/.gitignore
   git commit -m "Add .gitignore files to prevent unwanted file commits"
   ```

2. ✅ **Test everything**
   - Run backend
   - Build Flutter app
   - Test on device

3. ✅ **Review full analysis**
   - See `PROJECT_CLEANUP_ANALYSIS.md` for detailed restructuring plan

---

## 💡 PRO TIPS

1. **Before cleanup:** Commit your current work
2. **During cleanup:** Close all IDEs and editors
3. **After cleanup:** Run tests to verify
4. **Regular maintenance:** Run cleanup script weekly

---

**Need help?** See `PROJECT_CLEANUP_ANALYSIS.md` for detailed information.
