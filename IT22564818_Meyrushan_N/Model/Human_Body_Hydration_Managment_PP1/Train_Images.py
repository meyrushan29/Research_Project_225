import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from sklearn.metrics import classification_report

from config import DEVICE, EPOCHS, LR, MODEL_OUT
from dataLoad_images import load_data_images   # ✅ NEW SAFE LOADER


# ======================================================
# LOAD DATA
# ======================================================
train_loader, test_loader, class_names, train_dataset = load_data_images()
print("Classes:", class_names)


# ======================================================
# MODEL – RESNET18 (TRANSFER LEARNING)
# ======================================================
model = models.resnet18(pretrained=True)

# Freeze backbone
for param in model.parameters():
    param.requires_grad = False

# Replace classifier head
num_ftrs = model.fc.in_features
model.fc = nn.Sequential(
    nn.Linear(num_ftrs, 256),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(256, len(class_names))  # ✅ Safe (auto = 2)
)

model.to(DEVICE)


# ======================================================
# LOSS & OPTIMIZER
# ======================================================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.fc.parameters(), lr=LR)


# ======================================================
# TRAINING LOOP
# ======================================================
for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in train_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

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

    print(
        f"Epoch [{epoch+1}/{EPOCHS}] "
        f"Loss: {epoch_loss:.4f} "
        f"Accuracy: {epoch_acc:.4f}"
    )


# ======================================================
# EVALUATION
# ======================================================
model.eval()
y_true, y_pred = [], []

with torch.no_grad():
    for images, labels in test_loader:
        images = images.to(DEVICE)

        outputs = model(images)
        _, preds = torch.max(outputs, 1)

        y_true.extend(labels.numpy())
        y_pred.extend(preds.cpu().numpy())

print("\nClassification Report:")
print(classification_report(y_true, y_pred, target_names=class_names))


# ======================================================
# SAVE MODEL
# ======================================================
torch.save(model.state_dict(), MODEL_OUT)
print(f"\nModel saved successfully → {MODEL_OUT}")
