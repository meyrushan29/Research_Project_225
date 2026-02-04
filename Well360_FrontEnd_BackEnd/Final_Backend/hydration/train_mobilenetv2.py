import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from sklearn.metrics import classification_report

from hydration.dataLoad_images import load_data_images
from core.config import DEVICE, EPOCHS, LR, MOBILENET_MODEL_OUT


# ======================================================
# LOAD DATA
# ======================================================
train_loader, test_loader, class_names, _ = load_data_images()
print("Classes:", class_names)


# ======================================================
# MODEL – MOBILENET V2
# ======================================================
model = models.mobilenet_v2(pretrained=True)

# Freeze backbone
for param in model.parameters():
    param.requires_grad = False

# Replace classifier
num_ftrs = model.classifier[1].in_features
model.classifier = nn.Sequential(
    nn.Linear(num_ftrs, 256),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(256, len(class_names))
)

model.to(DEVICE)


# ======================================================
# LOSS & OPTIMIZER
# ======================================================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.classifier.parameters(), lr=LR)


# ======================================================
# TRAINING LOOP
# ======================================================
for epoch in range(EPOCHS):
    model.train()
    running_loss, correct, total = 0.0, 0, 0

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

    print(
        f"Epoch [{epoch+1}/{EPOCHS}] "
        f"Loss: {running_loss/total:.4f} "
        f"Accuracy: {correct.double()/total:.4f}"
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
# SAVE MODEL (ONLY HERE!)
# ======================================================
torch.save(model.state_dict(), MOBILENET_MODEL_OUT)
print(f"\n✅ MobileNetV2 saved → {MOBILENET_MODEL_OUT}")


