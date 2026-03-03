"""
COMPREHENSIVE LIP HYDRATION MODEL TRAINING SCRIPT
==================================================

Trains a MobileNetV2 model for lip-based hydration detection.
Uses preprocessed inner-lip mucosa images from data_processed/.

Requirements:
- Preprocessed data in: hydration/data_processed/Dehydrate/ and data_processed/Normal/
- Run preprocessing first: python hydration/scripts/preprocess_all_lips.py

Usage:
    cd d:\PP2\Research_Project_225\Well360_FrontEnd_BackEnd\Final_Backend
    python hydration/training/train_lip_model_complete.py

Output:
    - hydration/models/LipModel_MobileNetV2.pth (trained model)
    - Training metrics and plots
"""

import sys
import os
from pathlib import Path

# Add parent directories to path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
sys.path.append(str(backend_dir))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split, WeightedRandomSampler
from torchvision import datasets, models
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from tqdm import tqdm
import json
import copy

from core.config import (
    MOBILENET_MODEL_OUT, 
    DEVICE, 
    BATCH_SIZE, 
    EPOCHS, 
    LR, 
    IMG_SIZE,
    RANDOM_STATE
)

from hydration.training.preprocess_images import get_transforms

print("="*60)
print("LIP HYDRATION MODEL TRAINING (INNER MUCOSA)")
print("="*60)
print(f"Device: {DEVICE}")
print(f"Model Output: {MOBILENET_MODEL_OUT}")
print(f"Batch Size: {BATCH_SIZE}")
print(f"Epochs: {EPOCHS}")
print(f"Learning Rate: {LR}")
print("="*60)

# ======================================================
# 1. MODEL ARCHITECTURE
# ======================================================
class ImprovedLipModel(nn.Module):
    """
    Enhanced MobileNetV2 with dropout and batch normalization.
    Trained on inner lip mucosa images for hydration detection.
    """
    def __init__(self, num_classes=2):
        super().__init__()
        self.mobilenet = models.mobilenet_v2(pretrained=True)
        num_ftrs = self.mobilenet.classifier[1].in_features
        
        # Custom classifier head
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

# ======================================================
# 2. TRAINING FUNCTION
# ======================================================
def train_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(loader, desc="Training")
    for inputs, labels in pbar:
        inputs, labels = inputs.to(device), labels.to(device)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        
        # Gradient clipping to stabilize training
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        # Statistics
        running_loss += loss.item() * inputs.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        # Update progress bar
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'acc': f'{100.*correct/total:.2f}%'
        })
    
    epoch_loss = running_loss / total
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc

# ======================================================
# 3. VALIDATION FUNCTION
# ======================================================
def validate_epoch(model, loader, criterion, device):
    """Validate for one epoch"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for inputs, labels in tqdm(loader, desc="Validation"):
            inputs, labels = inputs.to(device), labels.to(device)
            
            # Forward pass
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            # Statistics
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    epoch_loss = running_loss / total
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc

# ======================================================
# 4. MAIN TRAINING PIPELINE
# ======================================================
def main():
    # ============ USE PREPROCESSED DATA ============
    data_dir = backend_dir / "hydration" / "data_processed"
    raw_data_dir = backend_dir / "hydration" / "data"
    
    # Check if preprocessed data exists, if not suggest running preprocessing
    if not data_dir.exists() or not any(data_dir.iterdir()):
        print(f"\n⚠️  Preprocessed data not found at: {data_dir}")
        print(f"   Running preprocessing first...")
        print(f"   Looking for raw data at: {raw_data_dir}")
        
        if raw_data_dir.exists():
            # Auto-run preprocessing
            import subprocess
            preprocess_script = backend_dir / "hydration" / "scripts" / "preprocess_all_lips.py"
            if preprocess_script.exists():
                print(f"\n🔄 Auto-preprocessing raw images...")
                result = subprocess.run(
                    [sys.executable, str(preprocess_script)],
                    cwd=str(backend_dir),
                    capture_output=True,
                    text=True
                )
                print(result.stdout)
                if result.returncode != 0:
                    print(f"❌ Preprocessing failed:\n{result.stderr}")
                    return None, None
            else:
                print(f"❌ Preprocessing script not found: {preprocess_script}")
                return None, None
        else:
            print(f"\n❌ ERROR: No training data found!")
            print(f"   Create directories:")
            print(f"     hydration/data/Dehydrate/  (dehydrated lip images)")
            print(f"     hydration/data/Normal/     (hydrated lip images)")
            return None, None
    
    dehydrate_dir = data_dir / "Dehydrate"
    normal_dir = data_dir / "Normal"
    
    if not dehydrate_dir.exists() or not normal_dir.exists():
        print(f"\n❌ ERROR: Training data subdirectories not found!")
        print(f"Expected:")
        print(f"  - {dehydrate_dir}")
        print(f"  - {normal_dir}")
        return None, None
    
    # Count images
    dehydrate_count = len([f for f in dehydrate_dir.iterdir() if f.suffix.lower() in ('.png', '.jpg', '.jpeg')])
    normal_count = len([f for f in normal_dir.iterdir() if f.suffix.lower() in ('.png', '.jpg', '.jpeg')])
    
    print(f"\n📊 Training Data (Preprocessed Inner Lip):")
    print(f"  Dehydrate: {dehydrate_count} images")
    print(f"  Normal: {normal_count} images")
    print(f"  Total: {dehydrate_count + normal_count} images")
    
    if dehydrate_count < 5 or normal_count < 5:
        print(f"\n❌ ERROR: Too few images to train! Need at least 5 per class.")
        return None, None
    
    # Load dataset
    print("\n📁 Loading preprocessed dataset...")
    train_transform = get_transforms(train=True)
    val_transform = get_transforms(train=False)
    
    full_dataset = datasets.ImageFolder(str(data_dir), transform=train_transform)
    
    # Split dataset (80% train, 20% validation)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    
    train_dataset, val_dataset = random_split(
        full_dataset, 
        [train_size, val_size],
        generator=torch.Generator().manual_seed(RANDOM_STATE)
    )
    
    # ============ CLASS-WEIGHTED SAMPLING ============
    # Handle class imbalance (Dehydrate vs Normal)
    class_counts = [0] * len(full_dataset.classes)
    for _, label in full_dataset.samples:
        class_counts[label] += 1
    
    class_weights = [1.0 / c for c in class_counts]
    sample_weights = [class_weights[full_dataset.targets[i]] for i in train_dataset.indices]
    
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True
    )
    
    # ============ CLASS-WEIGHTED LOSS ============
    total = sum(class_counts)
    loss_weights = torch.tensor([total / (len(class_counts) * c) for c in class_counts], dtype=torch.float32).to(DEVICE)
    print(f"  Class weights (loss): {loss_weights.tolist()}")
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        sampler=sampler,  # Use weighted sampler instead of shuffle
        num_workers=0,    # Use 0 for Windows compatibility
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    # Create a separate copy for validation with val_transform
    val_dataset_with_transform = datasets.ImageFolder(str(data_dir), transform=val_transform)
    val_indices = val_dataset.indices
    val_subset = torch.utils.data.Subset(val_dataset_with_transform, val_indices)
    
    val_loader = DataLoader(
        val_subset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    print(f"✅ Dataset loaded:")
    print(f"  Training samples: {len(train_dataset)}")
    print(f"  Validation samples: {len(val_subset)}")
    print(f"  Classes: {full_dataset.classes}")
    
    # Initialize model
    print(f"\n🔧 Initializing MobileNetV2 model...")
    model = ImprovedLipModel(num_classes=len(full_dataset.classes))
    model = model.to(DEVICE)
    
    # Freeze backbone for first few epochs (fine-tuning strategy)
    print("  Freezing backbone for warm-up...")
    for param in model.mobilenet.features.parameters():
        param.requires_grad = False
    
    # Loss function with class weights
    criterion = nn.CrossEntropyLoss(weight=loss_weights)
    
    # Optimizer — only classifier params initially
    optimizer = optim.Adam(model.mobilenet.classifier.parameters(), lr=LR)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, 
        mode='min', 
        factor=0.5, 
        patience=3
    )
    print("✅ Optimizer and scheduler initialized")
    
    # Training history
    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': []
    }
    
    best_val_acc = 0.0
    best_model_wts = None
    patience_counter = 0
    EARLY_STOP_PATIENCE = 8  # Stop if no improvement for 8 epochs
    UNFREEZE_EPOCH = 5  # Unfreeze backbone after 5 epochs
    
    # Training loop
    print(f"\n🚀 Starting training for {EPOCHS} epochs...")
    print(f"   Phase 1 (Epochs 1-{UNFREEZE_EPOCH}): Train classifier only")
    print(f"   Phase 2 (Epochs {UNFREEZE_EPOCH+1}+): Fine-tune entire model")
    print("="*60)
    
    for epoch in range(EPOCHS):
        print(f"\nEpoch {epoch+1}/{EPOCHS}")
        print("-" * 40)
        
        # Unfreeze backbone after warm-up period
        if epoch == UNFREEZE_EPOCH:
            print("🔓 Unfreezing backbone for full fine-tuning...")
            for param in model.mobilenet.features.parameters():
                param.requires_grad = True
            
            # Add all params to optimizer with lower LR for backbone
            optimizer = optim.Adam([
                {'params': model.mobilenet.features.parameters(), 'lr': LR * 0.1},
                {'params': model.mobilenet.classifier.parameters(), 'lr': LR}
            ])
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode='min', factor=0.5, patience=3
            )
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, DEVICE)
        
        # Validate
        val_loss, val_acc = validate_epoch(model, val_loader, criterion, DEVICE)
        
        # Update learning rate
        scheduler.step(val_loss)
        
        # Save history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        # Print epoch summary
        print(f"\n📊 Epoch {epoch+1} Summary:")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_wts = copy.deepcopy(model.state_dict())
            patience_counter = 0
            print(f"  ✅ New best model! (Val Acc: {val_acc:.2f}%)")
        else:
            patience_counter += 1
            print(f"  ⏳ No improvement ({patience_counter}/{EARLY_STOP_PATIENCE})")
        
        # Early stopping
        if patience_counter >= EARLY_STOP_PATIENCE:
            print(f"\n⚠️  Early stopping triggered after {epoch+1} epochs")
            break
    
    # Load best model weights
    if best_model_wts is not None:
        model.load_state_dict(best_model_wts)
    
    # Save model
    os.makedirs(str(MOBILENET_MODEL_OUT.parent), exist_ok=True)
    torch.save(model.state_dict(), MOBILENET_MODEL_OUT)
    
    print("\n" + "="*60)
    print("🎉 TRAINING COMPLETE!")
    print("="*60)
    print(f"Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f"Model saved to: {MOBILENET_MODEL_OUT}")
    
    # Save training history
    history_file = MOBILENET_MODEL_OUT.parent / "training_history.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"Training history saved to: {history_file}")
    
    # Save training metrics
    metrics_file = MOBILENET_MODEL_OUT.parent / "training_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump({
            "best_val_acc": best_val_acc,
            "final_train_acc": history['train_acc'][-1],
            "total_epochs": len(history['train_loss']),
            "data_dir": str(data_dir),
            "timestamp": datetime.now().isoformat(),
            "model_type": "ImprovedLipModel (Inner Mucosa)",
            "class_counts": {full_dataset.classes[i]: class_counts[i] for i in range(len(class_counts))}
        }, f, indent=2)
    
    # Plot training curves
    plot_training_curves(history)
    
    return model, history

# ======================================================
# 5. PLOTTING FUNCTION
# ======================================================
def plot_training_curves(history):
    """Plot and save training curves"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    epochs = range(1, len(history['train_loss']) + 1)
    
    # Loss plot
    ax1.plot(epochs, history['train_loss'], 'b-', label='Training Loss')
    ax1.plot(epochs, history['val_loss'], 'r-', label='Validation Loss')
    ax1.set_title('Training and Validation Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True)
    
    # Accuracy plot
    ax2.plot(epochs, history['train_acc'], 'b-', label='Training Accuracy')
    ax2.plot(epochs, history['val_acc'], 'r-', label='Validation Accuracy')
    ax2.set_title('Training and Validation Accuracy')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    
    # Save plot
    plot_file = MOBILENET_MODEL_OUT.parent / "training_curves.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"📈 Training curves saved to: {plot_file}")
    
    plt.close()

# ======================================================
# 6. RUN TRAINING
# ======================================================
if __name__ == "__main__":
    try:
        result = main()
        if result is not None:
            model, history = result
            print("\n✅ Script completed successfully!")
        else:
            print("\n⚠️  Training did not complete. Check errors above.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR during training:")
        print(f"{str(e)}")
        import traceback
        traceback.print_exc()
