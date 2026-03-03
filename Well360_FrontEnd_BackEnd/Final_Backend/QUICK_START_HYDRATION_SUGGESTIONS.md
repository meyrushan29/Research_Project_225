# Quick Start: Hydration Personalized Suggestions

**Get up and running in 5 minutes!**

---

## 🚀 Step 1: Seed Default Suggestions (1 minute)

```bash
cd Final_Backend
python scripts/seed_hydration_suggestions.py
```

**Output:**
```
🌊 Seeding 20 hydration suggestions...
✅ [1/20] Created: 🚨 Critical: Immediate Hydration Required
✅ [2/20] Created: ⚠️ Hot Weather Alert
...
✅ [20/20] Created: ⚡ Energy & Hydration

📊 Created: 20/20 suggestions
```

---

## 🔧 Step 2: Start Backend (1 minute)

```bash
python main.py
```

**Server starts at:** `http://localhost:8000`

---

## 🔑 Step 3: Login & Get Token (1 minute)

**Request:**
```http
POST http://localhost:8000/auth/login
Content-Type: application/json

{
  "email": "your_email@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the token!** You'll need it for authenticated requests.

---

## 👁️ Step 4: View Suggestions (Admin) (1 minute)

**Request:**
```http
GET http://localhost:8000/admin/hydration/suggestions
Authorization: Bearer {your_token}
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "🚨 Critical: Immediate Hydration Required",
    "content": "Your dehydration level is critical...",
    "category": "symptoms",
    "priority": 3,
    "model_type": "form",
    "risk_level": "High Dehydration",
    "is_active": true
  },
  ...
]
```

---

## 🧪 Step 5: Test Form Prediction (1 minute)

**Request:**
```http
POST http://localhost:8000/predict/form
Authorization: Bearer {your_token}
Content-Type: application/json

{
  "Age": 25,
  "Gender": "Male",
  "Weight": 70,
  "Height": 175,
  "Water_Intake_Last_4_Hours": 0.3,
  "Exercise_Time_Last_4_Hours": 60,
  "Physical_Activity_Level": "Heavy",
  "Urinated_Last_4_Hours": "Yes",
  "Urine_Color": 6,
  "Thirsty": "Yes",
  "Dizziness": "No",
  "Fatigue": "Yes",
  "Headache": "No",
  "Sweating_Level": "Heavy",
  "Latitude": 40.7128,
  "Longitude": -74.0060
}
```

**Response (with suggestions!):**
```json
{
  "success": true,
  "recommended_total_water_liters": 2.5,
  "hydration_score": 40,
  "personalized_suggestions": [
    {
      "id": 1,
      "title": "🚨 Critical: Immediate Hydration Required",
      "content": "Your dehydration level is critical. Drink 500ml...",
      "category": "symptoms",
      "priority": 3
    },
    {
      "id": 3,
      "title": "💪 Heavy Exercise Hydration",
      "content": "During intense physical activity, drink 200-300ml...",
      "category": "exercise",
      "priority": 3
    },
    {
      "id": 6,
      "title": "🤕 Symptom Relief",
      "content": "You're experiencing dehydration symptoms...",
      "category": "symptoms",
      "priority": 2
    }
  ],
  "recommendations": [
    "Increase water intake gradually over the next 4 hours.",
    "Maintain electrolyte balance if sweating increases.",
    "Avoid excessive caffeine and sugary drinks."
  ]
}
```

---

## 🎨 Step 6: Create Custom Suggestion (Bonus)

**Request:**
```http
POST http://localhost:8000/admin/hydration/suggestions
Authorization: Bearer {your_token}
Content-Type: application/json

{
  "title": "🏊 Swimming Hydration Tip",
  "content": "Swimming in a pool? You still sweat! Drink 250ml every 20 minutes during swim sessions.",
  "category": "exercise",
  "priority": 2,
  "model_type": "form",
  "activity_level": "Moderate",
  "is_active": true
}
```

**Response:**
```json
{
  "id": 21,
  "title": "🏊 Swimming Hydration Tip",
  "content": "Swimming in a pool? You still sweat!...",
  "category": "exercise",
  "priority": 2,
  "is_active": true,
  "created_at": "2026-02-13T10:30:00Z"
}
```

---

## ✅ You're Done!

Your hydration system now provides personalized, context-aware suggestions!

### What You Can Do Now:

1. **Test Different Scenarios:**
   - High dehydration + hot weather
   - Normal hydration + exercise
   - Morning vs evening predictions
   - Lip analysis with dehydrated state

2. **Manage Suggestions:**
   - Create custom suggestions
   - Update existing ones
   - Toggle active/inactive
   - View statistics

3. **Monitor Usage:**
   - Check which suggestions match most often
   - Refine content based on user needs
   - Add seasonal suggestions

---

## 📚 Next Steps

- Read full documentation: `HYDRATION_PERSONALIZED_SUGGESTIONS.md`
- Review implementation: `HYDRATION_IMPROVEMENTS_SUMMARY.md`
- Explore admin endpoints: Test all CRUD operations
- Customize suggestions: Add your own based on user feedback

---

## 🆘 Need Help?

**Issue:** No suggestions returned  
**Fix:** Check if suggestions are active: `GET /admin/hydration/suggestions?is_active=true`

**Issue:** Wrong suggestions appearing  
**Fix:** Review conditions: `GET /admin/hydration/suggestions/{id}`

**Issue:** Database error  
**Fix:** Restart backend to auto-create tables: `python main.py`

---

**Congratulations!** 🎉 You've successfully set up personalized hydration suggestions!

**Last Updated:** 2026-02-13
