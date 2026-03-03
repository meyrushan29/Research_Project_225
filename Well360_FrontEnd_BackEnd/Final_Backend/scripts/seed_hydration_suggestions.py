"""
Seed Script: Default Hydration Suggestions
Run this script to populate the database with default personalized suggestions.
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.database import SessionLocal
from core.models import HydrationSuggestion
from datetime import datetime

def seed_suggestions():
    """Create default hydration suggestions"""
    db = SessionLocal()
    
    # Check if suggestions already exist
    existing_count = db.query(HydrationSuggestion).count()
    if existing_count > 0:
        print(f"⚠️  Database already contains {existing_count} suggestions.")
        response = input("Do you want to add more suggestions anyway? (y/n): ")
        if response.lower() != 'y':
            print("Seeding cancelled.")
            return
    
    suggestions = [
        # === FORM PREDICTIONS - HIGH PRIORITY ===
        {
            "title": "🚨 Critical: Immediate Hydration Required",
            "content": "Your dehydration level is critical. Drink 500ml of water immediately, then 250ml every 15 minutes for the next hour. Seek shade, rest, and avoid physical activity.",
            "category": "symptoms",
            "priority": 3,
            "model_type": "form",
            "risk_level": "High Dehydration",
            "is_active": True
        },
        {
            "title": "⚠️ Hot Weather Alert",
            "content": "Temperature is above 30°C. Increase your water intake by 40-50% and avoid outdoor activities during peak heat (12 PM-4 PM). Wear light clothing and stay in air-conditioned spaces when possible.",
            "category": "weather",
            "priority": 3,
            "model_type": "form",
            "temperature_min": 30.0,
            "is_active": True
        },
        {
            "title": "💪 Heavy Exercise Hydration",
            "content": "During intense physical activity, drink 200-300ml of water every 15-20 minutes. Consider electrolyte drinks for sessions longer than 60 minutes.",
            "category": "exercise",
            "priority": 3,
            "model_type": "form",
            "activity_level": "Heavy",
            "is_active": True
        },
        
        # === FORM PREDICTIONS - MEDIUM PRIORITY ===
        {
            "title": "🌡️ Moderate Dehydration Warning",
            "content": "Your body needs rehydration. Drink at least 1 liter of water gradually over the next 2 hours. Monitor your urine color - aim for light yellow.",
            "category": "symptoms",
            "priority": 2,
            "model_type": "form",
            "risk_level": "Mild Dehydration",
            "is_active": True
        },
        {
            "title": "🏃 Pre-Workout Hydration",
            "content": "Before moderate to heavy exercise, drink 400-600ml of water 2-3 hours beforehand, and another 200-300ml 15 minutes before starting.",
            "category": "exercise",
            "priority": 2,
            "model_type": "form",
            "activity_level": "Moderate",
            "time_slots": ["8 AM-12 PM", "4 PM-8 PM"],
            "is_active": True
        },
        {
            "title": "🤕 Symptom Relief",
            "content": "You're experiencing dehydration symptoms. Drink water slowly and consistently. If symptoms persist after 2 hours of hydration, consult a healthcare provider.",
            "category": "symptoms",
            "priority": 2,
            "model_type": "form",
            "has_symptoms": True,
            "is_active": True
        },
        {
            "title": "🌅 Morning Hydration Boost",
            "content": "Start your day right! Drink 500ml of water within 30 minutes of waking up to rehydrate after sleep and kickstart your metabolism.",
            "category": "lifestyle",
            "priority": 2,
            "model_type": "both",
            "time_slots": ["4 AM-8 AM", "8 AM-12 PM"],
            "is_active": True
        },
        
        # === FORM PREDICTIONS - LOW PRIORITY ===
        {
            "title": "✅ Maintain Good Hydration",
            "content": "You're well-hydrated! Keep it up by drinking 200-250ml of water every hour throughout the day.",
            "category": "general",
            "priority": 1,
            "model_type": "form",
            "risk_level": "Low",
            "max_recommended_liters": 1.0,
            "is_active": True
        },
        {
            "title": "🍎 Hydration Through Food",
            "content": "Boost hydration by eating water-rich foods like cucumbers, watermelon, oranges, and strawberries. They contribute to your daily water intake.",
            "category": "diet",
            "priority": 1,
            "model_type": "both",
            "is_active": True
        },
        {
            "title": "☕ Caffeine & Hydration",
            "content": "Coffee and tea have mild diuretic effects. For every cup of caffeinated beverage, drink an extra glass of water to compensate.",
            "category": "diet",
            "priority": 1,
            "model_type": "both",
            "is_active": True
        },
        
        # === LIP ANALYSIS - HIGH PRIORITY ===
        {
            "title": "👄 Lip Dehydration Detected",
            "content": "Your lip analysis shows signs of dehydration. Drink at least 300ml of water immediately. Apply a hydrating lip balm with SPF 15+ if going outdoors.",
            "category": "symptoms",
            "priority": 3,
            "model_type": "lip",
            "lip_prediction": "Dehydrate",
            "max_hydration_score": 40.0,
            "is_active": True
        },
        {
            "title": "💧 Urgent: Severe Lip Dehydration",
            "content": "Your lips show severe dehydration. Drink water frequently (100-200ml every 15 min), use intensive lip repair treatment, and avoid sun exposure until recovered.",
            "category": "symptoms",
            "priority": 3,
            "model_type": "lip",
            "lip_prediction": "Dehydrate",
            "max_hydration_score": 25.0,
            "is_active": True
        },
        
        # === LIP ANALYSIS - MEDIUM PRIORITY ===
        {
            "title": "😊 Good Lip Hydration",
            "content": "Your lips look healthy! Maintain this by drinking water regularly and using lip balm to protect against environmental factors.",
            "category": "general",
            "priority": 2,
            "model_type": "lip",
            "lip_prediction": "Normal",
            "min_hydration_score": 60.0,
            "is_active": True
        },
        {
            "title": "🛡️ Lip Protection Tips",
            "content": "Protect your lips from environmental damage: use SPF lip balm outdoors, avoid licking lips, and stay hydrated in air-conditioned spaces.",
            "category": "lifestyle",
            "priority": 1,
            "model_type": "lip",
            "is_active": True
        },
        
        # === BOTH MODELS - GENERAL ===
        {
            "title": "🌙 Evening Hydration Reminder",
            "content": "Wind down your day with proper hydration. Drink 200ml of water 1-2 hours before bed (not right before to avoid nighttime bathroom trips).",
            "category": "lifestyle",
            "priority": 1,
            "model_type": "both",
            "time_slots": ["8 PM-Midnight"],
            "is_active": True
        },
        {
            "title": "🏖️ Summer Hydration Strategy",
            "content": "In warm weather, carry a reusable water bottle everywhere. Aim for 3-4 liters per day, more if exercising. Set hourly reminders.",
            "category": "weather",
            "priority": 2,
            "model_type": "both",
            "temperature_min": 25.0,
            "is_active": True
        },
        {
            "title": "❄️ Winter Hydration",
            "content": "Cold weather can mask dehydration. Indoor heating and less sweating don't mean you need less water. Maintain regular intake even in winter.",
            "category": "weather",
            "priority": 1,
            "model_type": "both",
            "temperature_max": 15.0,
            "is_active": True
        },
        {
            "title": "🍽️ Timing Matters",
            "content": "Drink water 30 minutes before meals to aid digestion and prevent overeating. Avoid drinking large amounts during meals.",
            "category": "diet",
            "priority": 1,
            "model_type": "both",
            "time_slots": ["8 AM-12 PM", "12 PM-4 PM", "4 PM-8 PM"],
            "is_active": True
        },
        {
            "title": "🎯 Hydration Tracking Tip",
            "content": "Use the Well360 app to log your water intake throughout the day. Consistent tracking helps you understand your hydration patterns and improve habits.",
            "category": "lifestyle",
            "priority": 1,
            "model_type": "both",
            "is_active": True
        },
        {
            "title": "⚡ Energy & Hydration",
            "content": "Feeling tired? It might be dehydration. Before reaching for coffee, try drinking 300-500ml of water first - dehydration is a common cause of fatigue.",
            "category": "symptoms",
            "priority": 2,
            "model_type": "both",
            "has_symptoms": True,
            "is_active": True
        }
    ]
    
    print(f"\n🌊 Seeding {len(suggestions)} hydration suggestions...\n")
    
    created_count = 0
    for idx, suggestion_data in enumerate(suggestions, 1):
        try:
            suggestion = HydrationSuggestion(**suggestion_data)
            db.add(suggestion)
            db.commit()
            db.refresh(suggestion)
            
            print(f"✅ [{idx}/{len(suggestions)}] Created: {suggestion.title}")
            created_count += 1
            
        except Exception as e:
            print(f"❌ [{idx}/{len(suggestions)}] Failed: {suggestion_data['title']}")
            print(f"   Error: {str(e)}")
            db.rollback()
    
    db.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Seeding Complete!")
    print(f"{'='*60}")
    print(f"📊 Created: {created_count}/{len(suggestions)} suggestions")
    print(f"📍 Database: hydration_app.db")
    print(f"\n💡 Next Steps:")
    print(f"   1. Start the backend server: python main.py")
    print(f"   2. Login to get auth token")
    print(f"   3. View suggestions: GET /admin/hydration/suggestions")
    print(f"   4. Test predictions to see personalized suggestions!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌊 WELL360 - HYDRATION SUGGESTIONS SEEDER")
    print("="*60)
    seed_suggestions()
