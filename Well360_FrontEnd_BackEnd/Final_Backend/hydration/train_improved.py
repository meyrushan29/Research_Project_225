
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from sklearn.metrics import classification_report
import copy # For saving best weights
import time
import os
import sys
sys.path.append(os.getcwd()) # Fix module path

from hydration.dataLoad_images import load_data_images
from core.config import DEVICE, EPOCHS, LR, MOBILENET_MODEL_OUT

class EarlyStopping:
    def __init__(self, patience=5, min_delta=0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0

def train_model():
    print(f"--- Starting Advanced Training on {DEVICE} ---")
    
    # 1. LOAD DATA
    train_loader, test_loader, class_names, train_dataset = load_data_images()
    print(f"Dataset Loaded. Classes: {class_names}")
    print(f"Training Samples: {len(train_dataset)}")
    
    # 2. SETUP MODEL
    model = models.mobilenet_v2(pretrained=True)
    
    # Fine-tune more layers (unfreeze last block)
    # Freeze initial layers
    for param in model.features.parameters():
        param.requires_grad = False
        
    # Unfreeze the last convolutional block for better feature adaptation
    # MobileNetV2 features[18] is the last block
    for param in model.features[18].parameters():
        param.requires_grad = True

    num_ftrs = model.classifier[1].in_features
    # Enhanced Classifier Head
    model.classifier = nn.Sequential(
        nn.Linear(num_ftrs, 512),
        nn.ReLU(),
        nn.Dropout(0.5), # Increased dropout prevents overfitting
        nn.Linear(512, 128),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(128, len(class_names))
    )
    model.to(DEVICE)
    
    # 3. ADVANCED METRICS
    criterion = nn.CrossEntropyLoss()
    # Lower LR for fine-tuning
    optimizer = optim.Adam(model.parameters(), lr=LR * 0.1) 
    
    # Learning Rate Scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.1, patience=3, verbose=True
    )
    
    early_stopper = EarlyStopping(patience=7)
    
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0
    
    # 4. TRAINING LOOP
    for epoch in range(EPOCHS):
        start_time = time.time()
        
        # --- TRAIN ---
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels)
            total += labels.size(0)
            
        epoch_loss = running_loss / total
        epoch_acc = correct.double() / total
        
        # --- VALIDATE ---
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels)
                val_total += labels.size(0)
                
        val_loss = val_loss / val_total
        val_acc = val_correct.double() / val_total
        
        # --- STATS ---
        print(f"Epoch {epoch+1}/{EPOCHS} | "
              f"Train Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
              f"Time: {time.time() - start_time:.1f}s")
        
        # Scheduler Step
        scheduler.step(val_loss)
        
        # Save Best Model
        if val_acc > best_acc:
            best_acc = val_acc
            best_model_wts = copy.deepcopy(model.state_dict())
            
        # Early Stopping
        early_stopper(val_loss)
        if early_stopper.early_stop:
            print("🛑 Early stopping triggered!")
            break

    print(f"\n🏆 Best Validation Accuracy: {best_acc:.4f}")
    
    # 5. FINAL LOAD & SAVE
    model.load_state_dict(best_model_wts)
    torch.save(model.state_dict(), MOBILENET_MODEL_OUT)
    print(f"✅ Best model saved to {MOBILENET_MODEL_OUT}")
    
    # 6. REPORT
    print("\n--- Final Classification Report ---")
    y_true, y_pred = [], []
    model.eval()
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(DEVICE)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            y_true.extend(labels.numpy())
            y_pred.extend(preds.cpu().numpy())
            
    print(classification_report(y_true, y_pred, target_names=class_names))

if __name__ == "__main__":
    train_model()
