# Improving Fitness Exercise Prediction Accuracy

**Created:** 2026-02-13  
**Issue:** Some exercises are being predicted incorrectly  
**Status:** Enhanced with improved configuration

---

## Overview

The fitness AI model supports **19 different exercises** with both correct and wrong form detection:

### Supported Exercises

**Upper Body:**
1. Pull Up
2. Push Up
3. Barbell Biceps Curl
4. Hammer Curl
5. Bench Press
6. Incline Bench Press
7. Lat Pulldown
8. Tricep Dips
9. Tricep Pushdown
10. Shoulder Press
11. Lateral Raise
12. T-Bar Row

**Lower Body:**
13. Squat
14. Deadlift
15. Romanian Deadlift
16. Hip Thrust
17. Leg Extension
18. Leg Raises

**Core:**
19. Russian Twist
20. Plank

---

## Recent Improvements Applied

### ✅ Configuration Enhancements

**File:** `fitness/prediction_config.py`

1. **Increased Minimum Confidence:** 35% → 40%
   - Reduces false positives
   - Only accepts more confident predictions

2. **Extended History Window:** 30 frames → 35 frames
   - More stable predictions
   - Better temporal smoothing

3. **Longer Warm-up Period:** 5 frames → 8 frames
   - Skips initial noisy frames
   - Waits for pose stabilization

4. **Stricter Exercise Locking:** 20 frames → 25 frames
   - Requires 75% agreement (up from 70%)
   - Prevents rapid exercise switching

5. **Higher Quality Thresholds:**
   - High confidence lock break: 80% → 85%
   - Minimum valid frames: 5 → 10
   - Better video quality detection

---

## Common Prediction Issues & Solutions

### Issue 1: Similar Exercises Confused

**Problem:** The AI confuses similar exercises (e.g., barbell curl vs hammer curl)

**Similar Exercise Groups:**
```
- Bicep: Barbell Curl ↔ Hammer Curl
- Push: Push Up ↔ Bench Press ↔ Incline Bench Press
- Deadlifts: Deadlift ↔ Romanian Deadlift
- Triceps: Tricep Dips ↔ Tricep Pushdown
- Shoulders: Shoulder Press ↔ Lateral Raise
- Legs: Squat ↔ Leg Extension
- Back: Pull Up ↔ Lat Pulldown ↔ T-Bar Row
```

**Solutions:**
1. **Exaggerate Key Differences:**
   - Hammer Curl: Keep palms facing each other (neutral grip)
   - Barbell Curl: Keep palms facing up (supinated grip)

2. **Camera Angle Matters:**
   - Side angle for curls (shows arm angle clearly)
   - Front angle for presses (shows body alignment)
   - 45° angle for compound movements (best overall view)

3. **Hold Start/End Positions:**
   - Pause 1-2 seconds at start position
   - Pause 1-2 seconds at end position
   - AI uses these clear poses for better classification

### Issue 2: Low Confidence Predictions

**Problem:** Predictions have low confidence (<45%)

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Poor lighting | Use bright, even lighting |
| Partial body visibility | Ensure full body in frame |
| Fast movements | Perform exercises at moderate speed |
| Blurry video | Use stable camera/phone holder |
| Cluttered background | Use plain background if possible |
| Obstruction | Ensure no objects blocking view of joints |

### Issue 3: Exercise Switching Mid-Video

**Problem:** Exercise prediction changes halfway through video

**Causes:**
- Video contains multiple exercises
- Form breaks down mid-set
- Camera angle changes
- Body rotates out of optimal view

**Solutions:**
1. **One Exercise Per Video:**
   - Record each exercise separately
   - Don't chain multiple exercises

2. **Maintain Consistent Form:**
   - Keep same posture throughout
   - Avoid changing grip or stance mid-set

3. **Fixed Camera Position:**
   - Don't move camera during recording
   - Use tripod or stable surface

### Issue 4: Wrong Form Detection

**Problem:** AI says form is "wrong" when it's actually correct (or vice versa)

**Understanding Form Detection:**
- Form is based on joint angles and body alignment
- Model was trained on specific form standards
- Some variation exists in "correct" form

**Improvement Tips:**
1. **Research Proper Form:**
   - Watch tutorial videos
   - Check joint angle guidelines
   - Understand common mistakes

2. **Exaggerate Good Form:**
   - Keep back straight (deadlifts, squats)
   - Full range of motion
   - Control tempo (no momentum)

3. **Record from Best Angle:**
   - Side view for squats/deadlifts (shows back angle)
   - Front view for presses (shows shoulder position)
   - 45° angle shows most joint angles

---

## Video Recording Best Practices

### 📹 Camera Setup

1. **Position:**
   - 6-10 feet away from exerciser
   - Camera at waist/chest height
   - Capture full body from head to feet

2. **Angle:**
   - Side view (90°): Squats, deadlifts, rows
   - Front view (0°): Presses, lateral raises
   - 45° angle: Curls, most exercises (best compromise)

3. **Stability:**
   - Use tripod or phone stand
   - Avoid handheld recording
   - No camera movement during exercise

### 💡 Lighting

1. **Best Setup:**
   - Natural daylight from front/side
   - Avoid backlighting (bright window behind you)
   - Even lighting across body

2. **Indoor:**
   - Turn on all room lights
   - Face toward light source
   - Avoid shadows on body

### 👕 Clothing & Background

1. **Wear:**
   - Form-fitting athletic wear
   - Contrasting color to background
   - Shorts/short sleeves (shows joint movement)

2. **Background:**
   - Plain wall if possible
   - Remove clutter
   - Avoid mirrors (AI may detect reflection as person)

### ⏱️ Video Quality

1. **Duration:**
   - Minimum 3 seconds
   - Optimal: 10-30 seconds
   - Include 3-5 reps

2. **Frame Rate:**
   - 30 FPS or higher
   - Standard phone camera quality
   - HD resolution (720p+)

3. **Movement:**
   - Moderate speed (not too fast)
   - Controlled reps
   - Pause briefly at start/end positions

---

## Advanced: Adjusting Configuration

For developers or advanced users who want to fine-tune prediction accuracy:

### Configuration File
**Location:** `fitness/prediction_config.py`

### Key Parameters

```python
# Stricter predictions (fewer false positives, may miss some)
MIN_CONFIDENCE = 50.0  # Default: 40.0

# More lenient (catches more exercises, more false positives)
MIN_CONFIDENCE = 30.0  # Default: 40.0

# More stable (slower to adapt to new exercise)
HISTORY_WINDOW = 45  # Default: 35
LOCK_THRESHOLD = 30  # Default: 25

# Faster adaptation (may switch exercises more)
HISTORY_WINDOW = 25  # Default: 35
LOCK_THRESHOLD = 15  # Default: 25
```

### After Changing Configuration
1. Save the file
2. Restart the backend server
3. Test with sample videos

---

## Quality Assessment

The system now provides automatic quality assessment:

### Quality Levels

**High Quality:**
- ✅ >60% valid pose frames
- ✅ >50% average confidence
- ✅ Stable exercise detection
- Result: Most reliable predictions

**Medium Quality:**
- ⚠️ One quality issue detected
- Result: Generally reliable, minor improvements possible

**Low Quality:**
- ❌ Multiple quality issues
- Result: Predictions may be unreliable, follow recommendations

### Quality Recommendations

The system provides specific recommendations based on detected issues:
- "Ensure you're fully visible in the frame"
- "Use better lighting"
- "Hold poses more clearly at start and end of movement"
- "Record from a more stable angle"
- "Ensure clear view of joints"

---

## Testing Recommendations

### Test Each Exercise Type

1. **Start with Clear Examples:**
   - Perfect lighting
   - Optimal angle
   - Exaggerated form
   - Multiple clear reps

2. **Verify Model Behavior:**
   - Check confidence levels
   - Verify exercise detection
   - Check form assessment

3. **Test Edge Cases:**
   - Poor lighting
   - Partial visibility
   - Fast movements
   - Multiple similar exercises

### Compare Results

**Good Prediction:**
```json
{
  "exercise": "squat",
  "form": "correct",
  "confidence": 87.3,
  "confidence_level": "high",
  "quality": "high"
}
```

**Poor Prediction:**
```json
{
  "exercise": "unknown",
  "form": "unknown",
  "confidence": 32.1,
  "confidence_level": "low",
  "quality": "low",
  "quality_issues": ["Low pose detection rate (45.0%)"]
}
```

---

## Model Limitations

### What the Model Can Do
✅ Detect 19 different exercises  
✅ Assess form (correct/wrong)  
✅ Count reps automatically  
✅ Track hold times  
✅ Provide recommendations  

### Current Limitations
❌ May confuse very similar exercises  
❌ Requires clear view of full body  
❌ Sensitive to lighting/angle  
❌ Works best with standard exercise variations  
❌ Can't detect custom/hybrid exercises  

### Future Improvements Possible
- Retrain model with more data
- Add more exercise variations
- Improve similar exercise detection
- Add multi-angle support
- Real-time feedback (currently post-processing only)

---

## Troubleshooting Specific Exercises

### Barbell Biceps Curl vs Hammer Curl
**Issue:** Often confused
**Solution:**
- Hammer curl: Keep thumbs pointing up throughout
- Barbell curl: Keep palms facing ceiling at top
- Record from side angle (45°)

### Push-up vs Bench Press
**Issue:** Both involve similar pushing motion
**Solution:**
- Push-up: Ensure hands visible on ground
- Bench Press: Include bench/equipment in frame
- Different camera heights (low for push-up, high for bench)

### Squat vs Leg Extension
**Issue:** Both are leg exercises
**Solution:**
- Squat: Show full body standing/squatting motion
- Leg Extension: Show seated position and machine
- Very different movement patterns - shouldn't confuse if full body visible

### Deadlift vs Romanian Deadlift
**Issue:** Very similar movements
**Solution:**
- Deadlift: Bar starts on ground, show full descent
- RDL: Slight knee bend maintained, doesn't touch ground
- Record full movement from side

---

## Support & Feedback

If predictions remain inaccurate after following these guidelines:

1. **Check Configuration:** Verify `prediction_config.py` settings
2. **Review Video Quality:** Use quality assessment feedback
3. **Test with Reference Videos:** Use known-good exercise videos
4. **Consider Retraining:** May need more training data for specific exercises

---

**Status: IMPROVEMENTS APPLIED - READY FOR TESTING**

Test with various exercises and record any remaining issues for further refinement.
