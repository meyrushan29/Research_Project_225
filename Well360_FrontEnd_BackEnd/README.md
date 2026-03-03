# Well360 - AI Health Analyzer 🌟

**Well360** (also known as Uniq) is a comprehensive AI-powered mobile application designed to track, analyze, and improve your overall well-being. It leverages advanced Machine Learning (ML) models and Computer Vision techniques to provide real-time, personalized insights across three core pillars of health: **Fitness**, **Hydration**, and **Mental Health**.

---

## 🚀 Key Features

### 🏋️‍♂️ Fitness Tracking & Form Analysis
- **AI Form Correction:** Uses MediaPipe to track 33 body landmarks and evaluate exercise form in real-time.
- **Repetition Counting:** Accurately counts reps and tracks exercise history.
- **Heatmap Generation:** Visualizes areas of incorrect form to help users improve their technique.
- **Supported Exercises:** Pull-ups, Lat Pulldowns, Bicep Curls, Squats, and more.

### 💧 Hydration Monitoring
- **Lip Image Analysis:** Uses a custom-trained MobileNetV2 model (94.7% accuracy) to detect dehydration from lip images.
- **Automatic Cropping:** Employs MediaPipe Face Mesh for precise lip isolation.
- **Personalized Suggestions:** Provides smart, category-based hydration tips (e.g., Increase water intake, Monitor symptoms).
- **Physical Form Prediction:** Advanced regression models predict required water intake based on user biometrics and activity levels.

### 🧠 Mental Health Analysis
- **Emotion Detection:** Analyzes facial expressions from video or camera feeds using FER (Facial Expression Recognition) and MTCNN.
- **Mood Tracking:** Tracks daily mental well-being and provides actionable feedback.

---

## 🛠️ Technology Stack

**Frontend (Mobile App):**
- **Framework:** [Flutter](https://flutter.dev/) (Dart)
- **UI/UX:** Custom animated widgets, dynamic category-based icons, and health dashboards.
- **Core Packages:** `camera`, `fl_chart`, `google_mlkit_face_detection`, `shared_preferences`, `dio`, `http`.

**Backend (API & Machine Learning):**
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Machine Learning:** `TensorFlow`, `PyTorch`, `Scikit-learn`, `XGBoost`.
- **Computer Vision:** `OpenCV`, `MediaPipe`.
- **Explainable AI (XAI):** `SHAP`, `Captum` (for generating heatmaps).
- **Database:** SQLite (Development) / PostgreSQL (Production) using `SQLAlchemy`.
- **Server:** `Uvicorn` & `Gunicorn`.

---

## 📂 Project Structure

```text
Well360_FrontEnd_BackEnd/
├── flutter_application_1/    # Flutter Mobile Application
│   ├── lib/                  # Dart source code (UI, State, API integration)
│   ├── android/              # Android-specific build files
│   ├── ios/                  # iOS-specific build files
│   └── pubspec.yaml          # Frontend dependencies
├── Final_Backend/            # FastAPI Python Server
│   ├── fitness/              # ML models and logic for exercise form
│   ├── hydration/            # ML models and logic for dehydration detection
│   ├── Mental-H/             # ML models for emotion recognition
│   ├── routers/              # API endpoints for frontend communication
│   ├── main.py               # Main FastAPI application entry point
│   └── requirements.txt      # Backend Python dependencies
└── docs/                     # Additional project documentation
```

---

## 💻 Getting Started

### 1. Backend Setup
**Prerequisites:** Python 3.9+, pip.
```bash
# Navigate to the backend directory
cd Final_Backend

# Install required Python dependencies
pip install -r requirements.txt

# Seed the database with default hydration suggestions
python scripts/seed_hydration_suggestions.py

# Run the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*The API documentation will be available at `http://localhost:8000/docs`.*

### 2. Frontend Setup
**Prerequisites:** Flutter SDK.
```bash
# Navigate to the frontend directory
cd flutter_application_1

# Get Flutter packages
flutter pub get

# Run the app on your connected device or emulator
flutter run
```

---

## ☁️ Deployment

The backend is fully dockerized and ready to be deployed on platforms like **Render**, **Railway**, or **AWS/GCP**. 

For complete instructions on deploying the backend, connecting the Flutter app to the live server, and setting up persistent storage, please refer to the [Deployment Guide](./DEPLOYMENT_GUIDE.md).

---

## 🤝 Contributing
Feel free to open issues or submit pull requests to help improve the AI models, add new exercises, or enhance the user interface!

---

## 🎓 Project Details

**Project ID:** 25-26J-225

### 👥 Group Members
* **IT22564818** – Meyrushan N (Hydration Management)
* **IT22596802** – Laxshika S (Fitness Optimization)
* **IT22116338** – Kavilakshan V (Mental Health Assessment)

### 👨‍🏫 Supervisors
* **Supervisor:** Dr. Kapila Dissanayaka
* **Co-Supervisor:** Ms. Fathima Fanoon
