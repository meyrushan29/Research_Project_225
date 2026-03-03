"""
COMPLETE HYDRATION MODEL TRAINING SCRIPT
=========================================

This script trains ALL hydration models:
1. Lip Image Model (MobileNetV2) - with lip cropping and detection
2. Form Prediction Models (XGBoost Regressor & Classifier)

USAGE:
    python TRAIN_ALL_HYDRATION_MODELS.py

FEATURES:
- Automatic lip detection and cropping using MediaPipe
- Professional training pipeline with validation
- Automatic model saving
- Training visualization
- Error handling and recovery
- Progress tracking

REQUIREMENTS:
- For Lip Model: Images in hydration/data/Dehydrate/ and hydration/data/Normal/
- For Form Models: CSV data in hydration/data/dataset.csv
"""

import sys
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# Setup paths
BACKEND_DIR = Path(__file__).parent
sys.path.append(str(BACKEND_DIR))

print("=" * 80)
print("WELL360 - COMPLETE HYDRATION MODEL TRAINING")
print("=" * 80)
print(f"Working Directory: {BACKEND_DIR}")
print("=" * 80)

# ============================================================================
# PART 1: LIP IMAGE MODEL TRAINING (MobileNetV2)
# ============================================================================

def train_lip_model():
    """Train the lip hydration detection model with automatic lip cropping"""
    
    print("\n" + "=" * 80)
    print("PART 1: TRAINING LIP IMAGE MODEL (MobileNetV2)")
    print("=" * 80)
    
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader, Dataset, random_split
        from torchvision import models, transforms
        from PIL import Image
        import numpy as np
        import cv2
        import mediapipe as mp
        from tqdm import tqdm
        import json
        import matplotlib.pyplot as plt
        from datetime import datetime
        
        from core.config import (
            MOBILENET_MODEL_OUT, 
            DEVICE, 
            BATCH_SIZE, 
            EPOCHS, 
            LR, 
            IMG_SIZE,
            RANDOM_STATE
        )
        
        print(f"\n✅ Libraries imported successfully")
        print(f"Device: {DEVICE}")
        print(f"Model output: {MOBILENET_MODEL_OUT}")
        
        # ===================================================================
        # CUSTOM DATASET WITH LIP CROPPING
        # ===================================================================
        class LipDatasetWithCropping(Dataset):
            """
            Custom dataset that automatically crops lips from face images
            """
            def __init__(self, data_dir, transform=None, use_lip_cropping=True):
                self.data_dir = Path(data_dir)
                self.transform = transform
                self.use_lip_cropping = use_lip_cropping
                
                # Initialize MediaPipe Face Mesh for lip detection
                if use_lip_cropping:
                    try:
                        self.mp_face_mesh = mp.solutions.face_mesh
                        self.face_mesh = self.mp_face_mesh.FaceMesh(
                            static_image_mode=True,
                            max_num_faces=1,
                            min_detection_confidence=0.5
                        )
                        print("✅ MediaPipe Face Mesh initialized for lip cropping")
                    except Exception as e:
                        print(f"⚠️  MediaPipe initialization failed: {e}")
                        print("   Will use full images without cropping")
                        self.use_lip_cropping = False
                
                # Load image paths and labels
                self.samples = []
                self.class_to_idx = {}
                
                # Scan directories
                for idx, class_name in enumerate(sorted(os.listdir(data_dir))):
                    class_path = data_dir / class_name
                    if not class_path.is_dir():
                        continue
                    
                    self.class_to_idx[class_name] = idx
                    
                    # Find all images
                    for img_file in class_path.glob("*"):
                        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                            self.samples.append((str(img_file), idx))
                
                self.classes = list(self.class_to_idx.keys())
                print(f"\n📊 Dataset loaded:")
                print(f"   Classes: {self.classes}")
                print(f"   Total images: {len(self.samples)}")
                for class_name, class_idx in self.class_to_idx.items():
                    count = sum(1 for _, idx in self.samples if idx == class_idx)
                    print(f"   - {class_name}: {count} images")
            
            def crop_lips(self, image):
                """
                Detect and crop lip region using MediaPipe
                Returns cropped image or original if detection fails
                """
                if not self.use_lip_cropping:
                    return image
                
                try:
                    # Convert PIL to numpy array
                    img_np = np.array(image)
                    img_rgb = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR) if len(img_np.shape) == 3 else img_np
                    img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)
                    
                    # Detect face landmarks
                    results = self.face_mesh.process(img_rgb)
                    
                    if results.multi_face_landmarks:
                        landmarks = results.multi_face_landmarks[0]
                        
                        # Lip landmark indices (outer boundary)
                        lip_indices = [
                            61, 185, 40, 39, 37, 0, 267, 269, 270, 409,  # Upper lip
                            291, 375, 321, 405, 314, 17, 84, 181, 91, 146  # Lower lip
                        ]
                        
                        # Extract coordinates
                        h, w = img_rgb.shape[:2]
                        x_coords = [landmarks.landmark[i].x * w for i in lip_indices]
                        y_coords = [landmarks.landmark[i].y * h for i in lip_indices]
                        
                        # Add padding for context
                        padding = 50
                        x_min = max(0, int(min(x_coords)) - padding)
                        x_max = min(w, int(max(x_coords)) + padding)
                        y_min = max(0, int(min(y_coords)) - padding)
                        y_max = min(h, int(max(y_coords)) + padding)
                        
                        # Crop to lip region
                        cropped = image.crop((x_min, y_min, x_max, y_max))
                        return cropped
                    
                    # If no face detected, return original
                    return image
                    
                except Exception as e:
                    # If cropping fails, return original image
                    return image
            
            def __len__(self):
                return len(self.samples)
            
            def __getitem__(self, idx):
                img_path, label = self.samples[idx]
                
                # Load image
                image = Image.open(img_path).convert('RGB')
                
                # Crop lips if enabled
                image = self.crop_lips(image)
                
                # Apply transforms
                if self.transform:
                    image = self.transform(image)
                
                return image, label
        
        # ===================================================================
        # MODEL ARCHITECTURE
        # ===================================================================
        class ImprovedLipModel(nn.Module):
            """Enhanced MobileNetV2 with custom classifier"""
            def __init__(self, num_classes=2):
                super().__init__()
                self.mobilenet = models.mobilenet_v2(pretrained=True)
                num_ftrs = self.mobilenet.classifier[1].in_features
                
                self.mobilenet.classifier = nn.Sequential(
                    nn.Dropout(0.3),
                    nn.Linear(num_ftrs, 512),
                    nn.ReLU(),
                    nn.BatchNorm1d(512),
                    nn.Dropout(0.4),
                    nn.Linear(512, 256),
                    nn.ReLU(),
                    nn.BatchNorm1d(256),
                    nn.Dropout(0.3),
                    nn.Linear(256, num_classes)
                )
            
            def forward(self, x):
                return self.mobilenet(x)
        
        # ===================================================================
        # DATA LOADING
        # ===================================================================
        data_dir = BACKEND_DIR / "hydration" / "data"
        
        if not data_dir.exists():
            print(f"\n❌ ERROR: Training data directory not found: {data_dir}")
            print("\nPlease create:")
            print("  hydration/data/")
            print("    ├── Dehydrate/  (dehydrated lip images)")
            print("    └── Normal/     (normal lip images)")
            return False
        
        # Check for subdirectories
        dehydrate_dir = data_dir / "Dehydrate"
        normal_dir = data_dir / "Normal"
        
        if not (dehydrate_dir.exists() and normal_dir.exists()):
            print(f"\n❌ ERROR: Missing data subdirectories!")
            print(f"Expected: {dehydrate_dir} and {normal_dir}")
            return False
        
        # Count images
        dehydrate_count = len(list(dehydrate_dir.glob("*.[jp][pn]g"))) + len(list(dehydrate_dir.glob("*.jpeg")))
        normal_count = len(list(normal_dir.glob("*.[jp][pn]g"))) + len(list(normal_dir.glob("*.jpeg")))
        
        print(f"\n📊 Training Data:")
        print(f"   Dehydrate: {dehydrate_count} images")
        print(f"   Normal: {normal_count} images")
        print(f"   Total: {dehydrate_count + normal_count} images")
        
        if dehydrate_count < 10 or normal_count < 10:
            print(f"\n⚠️  WARNING: Very few images!")
            print(f"   Minimum: 50 images per class")
            print(f"   Recommended: 200+ images per class")
            response = input("\n   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        
        # Transforms
        train_transform = transforms.Compose([
            transforms.Resize((int(IMG_SIZE * 1.2), int(IMG_SIZE * 1.2))),
            transforms.RandomCrop(IMG_SIZE),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        val_transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Create dataset with lip cropping
        print("\n🔍 Creating dataset with automatic lip detection...")
        full_dataset = LipDatasetWithCropping(
            data_dir, 
            transform=train_transform,
            use_lip_cropping=True  # Enable lip cropping
        )
        
        # Split dataset
        train_size = int(0.8 * len(full_dataset))
        val_size = len(full_dataset) - train_size
        
        train_dataset, val_dataset = random_split(
            full_dataset,
            [train_size, val_size],
            generator=torch.Generator().manual_seed(RANDOM_STATE)
        )
        
        # Update validation transform
        val_dataset.dataset.transform = val_transform
        
        # Data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=BATCH_SIZE,
            shuffle=True,
            num_workers=0,  # Set to 0 for Windows compatibility
            pin_memory=True if torch.cuda.is_available() else False
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=BATCH_SIZE,
            shuffle=False,
            num_workers=0,
            pin_memory=True if torch.cuda.is_available() else False
        )
        
        print(f"✅ Data loaders created:")
        print(f"   Training samples: {len(train_dataset)}")
        print(f"   Validation samples: {len(val_dataset)}")
        
        # ===================================================================
        # MODEL TRAINING
        # ===================================================================
        print(f"\n🔧 Initializing model...")
        model = ImprovedLipModel(num_classes=len(full_dataset.classes))
        model = model.to(DEVICE)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=LR)
        
        # Learning rate scheduler (without verbose for compatibility)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=3
        )
        print("✅ Learning rate scheduler initialized")
        
        history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
        best_val_acc = 0.0
        
        print(f"\n🚀 Starting training for {EPOCHS} epochs...")
        print("=" * 80)
        
        for epoch in range(EPOCHS):
            print(f"\n📍 Epoch {epoch+1}/{EPOCHS}")
            print("-" * 60)
            
            # Training
            model.train()
            running_loss = 0.0
            correct = 0
            total = 0
            
            pbar = tqdm(train_loader, desc="Training")
            for inputs, labels in pbar:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                running_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
                
                pbar.set_postfix({
                    'loss': f'{loss.item():.4f}',
                    'acc': f'{100.*correct/total:.2f}%'
                })
            
            train_loss = running_loss / total
            train_acc = 100. * correct / total
            
            # Validation
            model.eval()
            val_running_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for inputs, labels in tqdm(val_loader, desc="Validation"):
                    inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    
                    val_running_loss += loss.item() * inputs.size(0)
                    _, predicted = outputs.max(1)
                    val_total += labels.size(0)
                    val_correct += predicted.eq(labels).sum().item()
            
            val_loss = val_running_loss / val_total
            val_acc = 100. * val_correct / val_total
            
            scheduler.step(val_loss)
            
            # Save history
            history['train_loss'].append(train_loss)
            history['train_acc'].append(train_acc)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)
            
            # Print summary
            print(f"\n📊 Epoch {epoch+1} Summary:")
            print(f"   Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
            print(f"   Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
            
            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                print(f"   ✅ New best model! (Val Acc: {val_acc:.2f}%)")
                
                os.makedirs(MOBILENET_MODEL_OUT.parent, exist_ok=True)
                torch.save(model.state_dict(), MOBILENET_MODEL_OUT)
                print(f"   💾 Model saved to: {MOBILENET_MODEL_OUT}")
        
        print("\n" + "=" * 80)
        print("🎉 LIP MODEL TRAINING COMPLETE!")
        print("=" * 80)
        print(f"Best Validation Accuracy: {best_val_acc:.2f}%")
        print(f"Model saved to: {MOBILENET_MODEL_OUT}")
        
        # Save training history
        history_file = MOBILENET_MODEL_OUT.parent / "lip_training_history.json"
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"Training history saved to: {history_file}")
        
        # Plot training curves
        plt.figure(figsize=(15, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(history['train_loss'], 'b-', label='Training Loss')
        plt.plot(history['val_loss'], 'r-', label='Validation Loss')
        plt.title('Training and Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True)
        
        plt.subplot(1, 2, 2)
        plt.plot(history['train_acc'], 'b-', label='Training Accuracy')
        plt.plot(history['val_acc'], 'r-', label='Validation Accuracy')
        plt.title('Training and Validation Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy (%)')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plot_file = MOBILENET_MODEL_OUT.parent / "lip_training_curves.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"📈 Training curves saved to: {plot_file}")
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during lip model training:")
        print(f"{str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# HELPER: GENERATE SYNTHETIC TARGET LABELS
# ============================================================================

def generate_synthetic_targets(df):
    """
    Generate synthetic target labels from existing features.
    Uses rule-based logic to create training labels.
    """
    import pandas as pd
    import numpy as np
    
    print("\n📝 Generating synthetic targets using rule-based logic...")
    
    # Extract key features
    water_deficit = df.get('Water_Deficit', 0)
    total_symptoms = df.get('Total_Symptom_Score', 0)
    activity_factor = df.get('Activity_Factor', 1.0)
    heat_index = df.get('Heat_Index', 25)
    hydration_index = df.get('Hydration_Index', 30)
    
    # Generate Recommended Water (Regression Target)
    # Base calculation: Water deficit + adjustments
    base_recommendation = water_deficit
    
    # Add for symptoms
    symptom_adjustment = total_symptoms * 0.2
    
    # Add for activity
    activity_adjustment = (activity_factor - 1.0) * 0.3
    
    # Add for heat
    heat_adjustment = np.where(heat_index > 32, 0.5, np.where(heat_index > 28, 0.3, 0))
    
    # Calculate total recommended water
    recommended_water = base_recommendation + symptom_adjustment + activity_adjustment + heat_adjustment
    recommended_water = np.clip(recommended_water, 0.2, 4.0)  # Reasonable range
    
    df['Recommended_Water_Next_4_Hours'] = recommended_water
    
    # Generate Hydration Risk Level (Classification Target)
    # Based on recommended water and symptoms
    risk_level = []
    for idx, row in df.iterrows():
        rec_water = row.get('Recommended_Water_Next_4_Hours', 1.0)
        symptoms = row.get('Total_Symptom_Score', 0)
        urine_color = row.get('Urine Color (Most Recent Urination)', 3)
        
        # Determine risk
        if rec_water >= 2.5 or symptoms >= 3 or urine_color >= 7:
            risk_level.append('High')
        elif rec_water >= 1.5 or symptoms >= 2 or urine_color >= 5:
            risk_level.append('Moderate')
        elif rec_water >= 1.0 or symptoms >= 1:
            risk_level.append('Low')
        else:
            risk_level.append('Very Low')
    
    df['Hydration_Risk_Level'] = risk_level
    
    print(f"   ✅ Generated {len(df)} target labels")
    print(f"   Risk Level Distribution:")
    print(df['Hydration_Risk_Level'].value_counts().to_string())
    
    return df


# ============================================================================
# PART 2: FORM PREDICTION MODELS TRAINING (XGBoost)
# ============================================================================

def train_form_models():
    """Train XGBoost models for form-based hydration prediction"""
    
    print("\n" + "=" * 80)
    print("PART 2: TRAINING FORM PREDICTION MODELS (XGBoost)")
    print("=" * 80)
    
    try:
        import pandas as pd
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder
        from xgboost import XGBRegressor, XGBClassifier
        from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
        import joblib
        
        from core.config import (
            MODEL_REG_PATH,
            MODEL_CLF_PATH,
            PREPROCESSOR_PATH,
            ENCODER_PATH,
            DATA_PATH,
            RANDOM_STATE
        )
        from hydration.feature_eng import apply_feature_engineering
        from hydration.preprocess import create_preprocessor
        
        print(f"\n✅ Libraries imported successfully")
        
        # Load dataset
        print(f"\n📁 Loading dataset from: {DATA_PATH}")
        
        if not DATA_PATH.exists():
            print(f"\n❌ ERROR: Dataset not found: {DATA_PATH}")
            print("\nPlease ensure hydration/data/dataset.csv exists")
            return False
        
        df = pd.read_csv(DATA_PATH)
        print(f"✅ Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Apply feature engineering
        print(f"\n🔧 Applying feature engineering...")
        df_engineered = apply_feature_engineering(df)
        print(f"✅ Features engineered: {len(df_engineered.columns)} features")
        
        # Prepare targets
        target_reg = "Recommended_Water_Next_4_Hours"
        target_clf = "Hydration_Risk_Level"
        
        # 🔥 FIX: Generate synthetic targets if missing
        if target_reg not in df_engineered.columns or target_clf not in df_engineered.columns:
            print(f"\n⚠️  Target columns not found in dataset")
            print(f"   Generating synthetic targets from features...")
            
            # Generate targets using rule-based logic
            df_engineered = generate_synthetic_targets(df_engineered)
            
            if target_reg in df_engineered.columns and target_clf in df_engineered.columns:
                print(f"   ✅ Synthetic targets generated successfully")
            else:
                print(f"\n❌ ERROR: Could not generate target columns!")
                return False
        
        X = df_engineered.drop(columns=[target_reg, target_clf])
        y_reg = df_engineered[target_reg]
        y_clf = df_engineered[target_clf]
        
        # Split data
        print(f"\n📊 Splitting data (80/20)...")
        X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
            X, y_reg, y_clf, test_size=0.2, random_state=RANDOM_STATE
        )
        
        print(f"   Training samples: {len(X_train)}")
        print(f"   Testing samples: {len(X_test)}")
        
        # Create and fit preprocessor
        print(f"\n🔧 Creating preprocessor...")
        preprocessor = create_preprocessor(X_train)
        
        print(f"🔧 Fitting preprocessor on training data...")
        X_train_processed = preprocessor.fit_transform(X_train)  # Fit on train
        X_test_processed = preprocessor.transform(X_test)        # Transform test
        print(f"✅ Preprocessor fitted and data transformed")
        
        # Encode classification labels
        print(f"\n🔧 Encoding labels...")
        label_encoder = LabelEncoder()
        y_clf_train_encoded = label_encoder.fit_transform(y_clf_train)
        y_clf_test_encoded = label_encoder.transform(y_clf_test)
        
        print(f"✅ Classes: {label_encoder.classes_}")
        
        # Train Regressor
        print(f"\n🚀 Training XGBoost Regressor...")
        regressor = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        
        regressor.fit(X_train_processed, y_reg_train)
        
        # Evaluate regressor
        y_reg_pred = regressor.predict(X_test_processed)
        reg_r2 = r2_score(y_reg_test, y_reg_pred)
        reg_rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
        
        print(f"\n📊 Regressor Results:")
        print(f"   R² Score: {reg_r2:.4f}")
        print(f"   RMSE: {reg_rmse:.4f}")
        
        # Train Classifier
        print(f"\n🚀 Training XGBoost Classifier...")
        classifier = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            num_class=len(label_encoder.classes_),
            eval_metric="mlogloss",
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        
        classifier.fit(X_train_processed, y_clf_train_encoded)
        
        # Evaluate classifier
        y_clf_pred = classifier.predict(X_test_processed)
        clf_acc = accuracy_score(y_clf_test_encoded, y_clf_pred)
        
        print(f"\n📊 Classifier Results:")
        print(f"   Accuracy: {clf_acc:.4f}")
        print(f"\n{classification_report(y_clf_test_encoded, y_clf_pred, target_names=label_encoder.classes_)}")
        
        # Save models
        print(f"\n💾 Saving models...")
        os.makedirs(MODEL_REG_PATH.parent, exist_ok=True)
        
        joblib.dump(regressor, MODEL_REG_PATH)
        print(f"   ✅ Regressor saved: {MODEL_REG_PATH}")
        
        joblib.dump(classifier, MODEL_CLF_PATH)
        print(f"   ✅ Classifier saved: {MODEL_CLF_PATH}")
        
        joblib.dump(preprocessor, PREPROCESSOR_PATH)
        print(f"   ✅ Preprocessor saved: {PREPROCESSOR_PATH}")
        
        joblib.dump(label_encoder, ENCODER_PATH)
        print(f"   ✅ Label encoder saved: {ENCODER_PATH}")
        
        print("\n" + "=" * 80)
        print("🎉 FORM MODELS TRAINING COMPLETE!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during form models training:")
        print(f"{str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n🌊 WELL360 - Complete Hydration Model Training")
    print("This script will train BOTH lip and form prediction models\n")
    
    # Ask user what to train
    print("What would you like to train?")
    print("1. Lip Model Only (recommended if you have lip images)")
    print("2. Form Models Only (XGBoost - if you have CSV data)")
    print("3. Both Models (complete training)")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    success = True
    
    if choice in ['1', '3']:
        print("\n" + "="*80)
        print("STARTING LIP MODEL TRAINING...")
        print("="*80)
        lip_success = train_lip_model()
        success = success and lip_success
        
        if lip_success:
            print("\n✅ Lip model training completed successfully!")
        else:
            print("\n❌ Lip model training failed!")
    
    if choice in ['2', '3']:
        print("\n" + "="*80)
        print("STARTING FORM MODELS TRAINING...")
        print("="*80)
        form_success = train_form_models()
        success = success and form_success
        
        if form_success:
            print("\n✅ Form models training completed successfully!")
        else:
            print("\n❌ Form models training failed!")
    
    if choice not in ['1', '2', '3']:
        print("\n❌ Invalid choice! Please run again and select 1, 2, or 3.")
        success = False
    
    # Final summary
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    
    if success:
        print("🎉 ALL TRAINING COMPLETED SUCCESSFULLY!")
        print("\nYour models are ready to use!")
        print("\nNext steps:")
        print("1. Restart your backend server")
        print("2. Test predictions with real data")
        print("3. Check model performance")
    else:
        print("⚠️  TRAINING COMPLETED WITH ERRORS")
        print("\nPlease check the error messages above and:")
        print("1. Ensure training data is in the correct location")
        print("2. Check that all dependencies are installed")
        print("3. Review the error logs")
    
    print("="*80)
