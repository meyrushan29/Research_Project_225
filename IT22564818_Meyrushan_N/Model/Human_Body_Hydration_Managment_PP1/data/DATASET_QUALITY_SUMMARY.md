# Dataset Quality Analysis Report
## Lip Hydration Image Dataset

**Analysis Date:** February 11, 2026
**Total Images Analyzed:** 179 images
- Dehydrate: 48 images
- Normal: 131 images

---

## 🚨 CRITICAL FINDINGS

### **149 out of 179 images (83%) have quality issues!**

This is a **MAJOR PROBLEM** that explains why your AI is focusing on the wrong areas (background instead of lips).

---

## 📊 Main Issues Found

### 1. **TOO MUCH BACKGROUND** (Most Critical)
**Affected:** 45+ images

**Problem:** The AI is learning to focus on background areas instead of the lips because many training images have:
- Only 0-30% of important features in the center
- Lips are too small in the frame
- Too much surrounding area (face, neck, background)

**Worst Examples:**
- `Dehydrate_28.jpg` - Only **0.8%** focus in center
- `Dehydrate_33.jpg` - **0.0%** focus in center  
- `Dehydrate_35.jpg` - **0.0%** focus in center
- `Normal_97.jpg` - **0.0%** focus in center
- `Normal_98.jpg` - **0.0%** focus in center
- `Normal_99.jpg` - **0.0%** focus in center
- `Normal_100.jpg` - **0.0%** focus in center

**This is why the AI focuses on background!**

---

### 2. **BLURRY IMAGES**
**Affected:** 130+ images

**Problem:** Blurry images make it hard for the AI to learn proper lip features
- Sharpness scores below 100 (should be 200+)
- Many images have sharpness as low as 5-30

**Examples:**
- `Normal_45.jpg` - Sharpness: **5.7**
- `Normal_97.jpg` - Sharpness: **5.8**
- `Normal_99.jpg` - Sharpness: **7.4**
- `Dehydrate_23.jpg` - Sharpness: **12.0**

---

### 3. **BRIGHTNESS ISSUES**
**Affected:** 10+ images

**Examples:**
- `Normal_26.jpg` - Too bright (203.1)
- `Normal_46.jpg` - Too bright (202.7)

---

### 4. **NON-LIP IMAGES**
**Affected:** 2 images

**Critical:**
- `Normal_45.jpg` - Only **4.4%** skin tone detected - **MAY NOT BE A LIP PHOTO!**
- `Normal_17.jpeg` - Only **2.3KB** file size - corrupted or wrong image

---

## ✅ ACTIONABLE RECOMMENDATIONS

### **PRIORITY 1: FIX BACKGROUND FOCUS (CRITICAL)**

**Action:** Re-crop ALL images to focus ONLY on lips

**How to fix:**
1. Use the camera app's cropping feature
2. Ensure lips fill **at least 60-80%** of the image
3. Remove excessive background, face, and neck areas
4. Keep only the lip region + small surrounding area

**Files to fix immediately (0% center focus):**
```
Dehydrate_28.jpg
Dehydrate_33.jpg
Dehydrate_35.jpg
Normal_85.jpg
Normal_87.jpg
Normal_97.jpg
Normal_98.jpg
Normal_99.jpg
Normal_100.jpg
Normal_104.jpg
```

---

### **PRIORITY 2: REMOVE BLURRY IMAGES (HIGH)**

**Action:** Delete or retake blurry images

**Criteria:** Remove images with sharpness < 100

**Files to remove/retake (very blurry, sharpness < 20):**
```
Dehydrate_20.jpg (16.7)
Dehydrate_23.jpg (12.0)
Dehydrate_24.jpg (13.2)
Dehydrate_31.jpg (19.8)
Dehydrate_33.jpg (11.9)
Dehydrate_36.jpg (14.0)
Normal_02.png (12.2)
Normal_22.jpg (16.1)
Normal_23.jpg (14.0)
Normal_24.jpg (15.7)
Normal_27.jpg (13.5)
Normal_32.jpg (15.3)
Normal_33.jpg (7.6)
Normal_37.jpg (13.0)
Normal_40.jpg (14.4)
Normal_43.jpg (9.5)
Normal_45.jpg (5.7) - ALSO NOT A LIP PHOTO!
Normal_46.jpg (12.4)
Normal_60.jpg (12.1)
Normal_61.jpg (18.9)
Normal_63.jpg (15.3)
Normal_66.jpg (10.9)
Normal_69.jpg (15.6)
Normal_74.jpg (12.2)
Normal_78.jpg (12.2)
Normal_79.jpg (9.5)
Normal_84.jpg (8.1)
Normal_86.jpg (12.2)
Normal_97.jpg (5.8)
Normal_99.jpg (7.4)
```

---

### **PRIORITY 3: REMOVE CORRUPTED/WRONG IMAGES (CRITICAL)**

**Action:** Delete these files immediately

```
Normal_17.jpeg - Only 2.3KB (corrupted)
Normal_45.jpg - Not a lip photo (4.4% skin tone)
```

---

### **PRIORITY 4: FIX BRIGHTNESS (MEDIUM)**

**Action:** Adjust brightness or remove overly bright images

```
Normal_26.jpg - Too bright (203.1)
Normal_46.jpg - Too bright (202.7)
```

---

## 📈 DATASET IMPROVEMENT PLAN

### Step 1: Clean the Dataset (This Week)
1. **Delete** corrupted/wrong images (2 files)
2. **Delete** extremely blurry images (30+ files)
3. **Re-crop** images with too much background (45+ files)
4. **Adjust** brightness for overly bright images (2 files)

### Step 2: Retake Photos (Next Week)
1. Use better lighting
2. Use camera focus/tap to focus on lips
3. Ensure lips fill 60-80% of frame
4. Take multiple shots and keep the sharpest one

### Step 3: Retrain Model (After Cleanup)
1. Use cleaned dataset
2. Add data augmentation (rotation, brightness adjustment)
3. Use proper cropping in preprocessing
4. Monitor XAI heatmaps to ensure focus is on lips

---

## 🎯 EXPECTED IMPROVEMENTS

After fixing these issues:
- ✅ AI will focus on lips instead of background
- ✅ Better accuracy in dehydration detection
- ✅ More consistent predictions
- ✅ XAI heatmaps will highlight lip features correctly

---

## 📁 FILES GENERATED

1. **quality_report.json** - Full detailed analysis with metrics
2. **problematic_files.txt** - List of all problematic files sorted by severity
3. **This summary document** - Action plan and recommendations

---

## ⚠️ IMPORTANT NOTES

1. **DO NOT** train the model with the current dataset - it will learn wrong patterns
2. **PRIORITY:** Fix background focus issues first (this is causing the main problem)
3. **VERIFY:** After fixing, run the quality checker again to confirm improvements
4. **TEST:** After retraining, check XAI heatmaps to ensure proper focus

---

## 🔧 HOW TO RUN THE CHECKER AGAIN

```bash
cd d:\PP2\Research_Project_225\Well360_FrontEnd_BackEnd
python check_dataset_quality.py
```

The script will generate updated reports showing your progress.

---

**Next Steps:**
1. Review the problematic_files.txt
2. Start with PRIORITY 1 (background focus)
3. Re-run the quality checker
4. Retrain the model with cleaned data
