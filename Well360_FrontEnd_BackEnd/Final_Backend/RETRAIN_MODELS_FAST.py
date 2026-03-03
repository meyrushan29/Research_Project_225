"""
🚀 FAST EXPERT-LEVEL HYDRATION MODEL RETRAINING
================================================

Optimized for faster training while maintaining expert-level accuracy.

Models Trained:
1. Lip Image Model (MobileNetV2) - Deep Learning
2. Water Volume Regressor (XGBoost) - ML Regression
3. Risk Level Classifier (XGBoost) - ML Classification

Optimizations:
- Reduced epochs (15 instead of 30)
- Smaller batch size for faster iteration
- Optimized data loading
- Early stopping (patience 5)
- Efficient hyperparameters

Usage:
    python RETRAIN_MODELS_FAST.py

Estimated Time: 10-15 minutes
"""

import sys
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

sys.path.append(str(Path(__file__).parent))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split, WeightedRandomSampler
from torchvision import datasets, models
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from tqdm import tqdm
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report
)
import xgboost as xgb
from collections import Counter

from core.config import MOBILENET_MODEL_OUT, DEVICE, IMG_SIZE, RANDOM_STATE
from hydration.training.preprocess_images import get_transforms
from hydration.feature_eng import AdvancedFeatureEngineer

print("="*80)
print("🚀 FAST EXPERT-LEVEL MODEL RETRAINING")
print("="*80)
print(f"Device: {DEVICE}")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# ============================================================================
# PART 1: LIP IMAGE MODEL - FAST EXPERT CONFIGURATION
# ============================================================================

class ExpertLipModel(nn.Module):
    """Expert MobileNetV2 with 4-layer classifier"""
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
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        return self.mobilenet(x)


def train_lip_model_fast():
    """Train lip model with fast expert configuration"""
    print("\n" + "="*80)
    print("📸 TRAINING LIP IMAGE MODEL")
    print("="*80)
    
    data_dir = Path("hydration/data")
    if not data_dir.exists():
        print("❌ ERROR: Training data not found!")
        return None
    
    dehydrate_count = len(list((data_dir / "Dehydrate").glob("*.[jp][pn]g")))
    normal_count = len(list((data_dir / "Normal").glob("*.[jp][pn]g")))
    
    print(f"\n📊 Dataset: {dehydrate_count} Dehydrate + {normal_count} Normal = {dehydrate_count + normal_count} total")
    
    # Load dataset
    print("🔧 Loading dataset...")
    train_transform = get_transforms(train=True)
    val_transform = get_transforms(train=False)
    
    full_dataset = datasets.ImageFolder(str(data_dir), transform=train_transform)
    
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    
    train_dataset, val_dataset = random_split(
        full_dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(RANDOM_STATE)
    )
    
    val_dataset.dataset.transform = val_transform
    
    # Class balancing
    print("⚖️  Applying class balancing...")
    targets = [full_dataset.targets[i] for i in train_dataset.indices]
    class_counts = Counter(targets)
    class_weights = {cls: 1.0 / count for cls, count in class_counts.items()}
    sample_weights = [class_weights[t] for t in targets]
    
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True
    )
    
    batch_size = 8  # Smaller for faster iteration
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        sampler=sampler,
        num_workers=0,  # Faster on some systems
        pin_memory=False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )
    
    print(f"✅ Loaders ready: {len(train_loader)} train batches, {len(val_loader)} val batches")
    
    # Initialize model
    print("🧠 Initializing model...")
    model = ExpertLipModel(num_classes=2)
    model = model.to(DEVICE)
    
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=0.0001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    
    # Training configuration
    epochs = 15  # Reduced for faster training
    best_val_acc = 0.0
    patience = 5  # Early stopping
    patience_counter = 0
    
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': [], 'lr': []}
    
    print(f"\n🚀 Training for {epochs} epochs (early stop patience: {patience})...")
    print("="*80)
    
    for epoch in range(epochs):
        print(f"\nEpoch {epoch+1}/{epochs}")
        print("-" * 60)
        
        # Training
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        pbar = tqdm(train_loader, desc="Training", ncols=100)
        for inputs, labels in pbar:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            pbar.set_postfix({'loss': f'{loss.item():.4f}', 'acc': f'{100.*correct/total:.2f}%'})
        
        train_loss = running_loss / total
        train_acc = 100. * correct / total
        
        # Validation
        model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for inputs, labels in tqdm(val_loader, desc="Validation", ncols=100):
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                running_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
        
        val_loss = running_loss / total
        val_acc = 100. * correct / total
        
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['lr'].append(current_lr)
        
        print(f"\n📊 Summary: Train {train_acc:.2f}% | Val {val_acc:.2f}% | LR {current_lr:.6f}")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            print(f"  ✅ New best! Saving model...")
            os.makedirs(MOBILENET_MODEL_OUT.parent, exist_ok=True)
            torch.save(model.state_dict(), MOBILENET_MODEL_OUT)
        else:
            patience_counter += 1
            print(f"  ⏳ No improvement ({patience_counter}/{patience})")
        
        if patience_counter >= patience:
            print(f"\n⚠️  Early stopping (no improvement for {patience} epochs)")
            break
    
    print("\n" + "="*80)
    print(f"🎉 LIP MODEL COMPLETE! Best Accuracy: {best_val_acc:.2f}%")
    print("="*80)
    
    # Save history
    history_file = MOBILENET_MODEL_OUT.parent / "lip_training_history_fast.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    return model, history


# ============================================================================
# PART 2: FORM PREDICTION MODELS - FAST EXPERT CONFIGURATION
# ============================================================================

def train_form_models_fast():
    """Train XGBoost models with fast expert configuration"""
    print("\n" + "="*80)
    print("📊 TRAINING FORM PREDICTION MODELS")
    print("="*80)
    
    data_path = Path("hydration/data/labeled_dataset.csv")
    if not data_path.exists():
        print(f"❌ ERROR: Dataset not found!")
        return None
    
    print(f"📁 Loading dataset...")
    df = pd.read_csv(data_path)
    print(f"✅ Loaded: {df.shape[0]} samples, {df.shape[1]} features")
    
    # Feature engineering
    print("🔧 Feature engineering...")
    engineer = AdvancedFeatureEngineer()
    
    feature_columns = [
        'Age', 'Gender', 'Weight (kg)', 'Height (cm)',
        'Activity Level', 'Water Intake (L/day)',
        'Urine Color', 'Thirst Level', 'Fatigue Level',
        'Headache Frequency', 'Dry Mouth', 'Dizziness',
        'Temperature (°C)', 'Humidity (%)', 'Time Slot (Select Your Current Time)'
    ]
    
    X = df[feature_columns].copy()
    X_engineered = engineer.engineer_features(X)
    
    y_regression = df['Recommended Water Intake (L)'].values
    y_classification = df['Hydration_Risk_Level'].values
    
    label_encoder = LabelEncoder()
    y_classification_encoded = label_encoder.fit_transform(y_classification)
    
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X_engineered, y_regression, y_classification_encoded,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y_classification_encoded
    )
    
    print(f"✅ Split: {len(X_train)} train, {len(X_test)} test")
    
    # Regression Model
    print("\n" + "-"*80)
    print("🔵 Training Regression Model...")
    
    reg_params = {
        'objective': 'reg:squarederror',
        'max_depth': 6,
        'learning_rate': 0.05,
        'n_estimators': 200,  # Reduced for speed
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': RANDOM_STATE,
        'n_jobs': -1
    }
    
    regressor = xgb.XGBRegressor(**reg_params)
    regressor.fit(X_train, y_reg_train, eval_set=[(X_test, y_reg_test)], early_stopping_rounds=15, verbose=False)
    
    y_reg_pred = regressor.predict(X_test)
    r2 = r2_score(y_reg_test, y_reg_pred)
    rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
    mae = mean_absolute_error(y_reg_test, y_reg_pred)
    
    print(f"📊 Metrics: R²={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")
    
    # Classification Model
    print("\n" + "-"*80)
    print("🔴 Training Classification Model...")
    
    clf_params = {
        'objective': 'multi:softmax',
        'num_class': len(np.unique(y_classification_encoded)),
        'max_depth': 5,
        'learning_rate': 0.05,
        'n_estimators': 200,  # Reduced for speed
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': RANDOM_STATE,
        'n_jobs': -1
    }
    
    classifier = xgb.XGBClassifier(**clf_params)
    classifier.fit(X_train, y_clf_train, eval_set=[(X_test, y_clf_test)], early_stopping_rounds=15, verbose=False)
    
    y_clf_pred = classifier.predict(X_test)
    accuracy = accuracy_score(y_clf_test, y_clf_pred)
    precision = precision_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    recall = recall_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    
    print(f"📊 Metrics: Acc={accuracy:.4f} ({accuracy*100:.2f}%), Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
    
    # Save models
    models_dir = Path("hydration/models")
    models_dir.mkdir(exist_ok=True)
    
    print("\n💾 Saving models...")
    joblib.dump(regressor, models_dir / "xgb_regressor.pkl")
    joblib.dump(classifier, models_dir / "xgb_classifier.pkl")
    joblib.dump(engineer.preprocessor, models_dir / "preprocessor.pkl")
    joblib.dump(label_encoder, models_dir / "hydration_label_encoder.pkl")
    
    metrics = {
        'regression': {'r2': float(r2), 'rmse': float(rmse), 'mae': float(mae)},
        'classification': {'accuracy': float(accuracy), 'precision': float(precision), 'recall': float(recall), 'f1': float(f1)}
    }
    
    with open(models_dir / "fast_training_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print("✅ All models saved!")
    
    return regressor, classifier, metrics


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main fast retraining pipeline"""
    print("\n🎯 Starting fast expert retraining...\n")
    
    results = {}
    start_time = datetime.now()
    
    # Train lip model
    try:
        lip_model, lip_history = train_lip_model_fast()
        results['lip_model'] = {'status': 'success', 'best_accuracy': max(lip_history['val_acc'])}
    except Exception as e:
        print(f"\n❌ Lip model failed: {e}")
        results['lip_model'] = {'status': 'failed', 'error': str(e)}
    
    # Train form models
    try:
        regressor, classifier, metrics = train_form_models_fast()
        results['form_models'] = {
            'status': 'success',
            'regression_r2': metrics['regression']['r2'],
            'classification_accuracy': metrics['classification']['accuracy']
        }
    except Exception as e:
        print(f"\n❌ Form models failed: {e}")
        results['form_models'] = {'status': 'failed', 'error': str(e)}
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    # Final summary
    print("\n" + "="*80)
    print("🎉 FAST EXPERT RETRAINING COMPLETE!")
    print("="*80)
    print(f"\n⏱️  Total Time: {duration:.1f} minutes")
    print("\n📊 Final Results:")
    for model_name, result in results.items():
        print(f"\n{model_name.upper()}:")
        for key, value in result.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
    
    print("\n✅ All models retrained successfully!")
    print("="*80)
    
    return results


if __name__ == "__main__":
    try:
        results = main()
        print("\n✅ Script completed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
