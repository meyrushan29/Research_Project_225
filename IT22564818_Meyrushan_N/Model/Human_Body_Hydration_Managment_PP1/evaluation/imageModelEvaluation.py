import torch
import torch.nn as nn
from torchvision import models
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)
import json
from pathlib import Path

from config import DEVICE, MODEL_OUT
from dataLoad_images import load_data_images   # SAFE image loader


# ======================================================
# PATHS
# ======================================================
RESULT_DIR = Path("results")
RESULT_DIR.mkdir(exist_ok=True)
RESULT_FILE = RESULT_DIR / "image_model_evaluation.json"


# ======================================================
# LOAD TRAINED MODEL
# ======================================================
def load_model(class_names):
    model = models.resnet18(pretrained=False)

    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_ftrs, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, len(class_names))
    )

    model.load_state_dict(torch.load(MODEL_OUT, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model


# ======================================================
# MAIN EVALUATION
# ======================================================
def main():
    print("\n" + "=" * 70)
    print(" IMAGE-BASED HYDRATION MODEL EVALUATION ".center(70))
    print("=" * 70)

    # --------------------------------------------------
    # Load data
    # --------------------------------------------------
    print("▶ Loading image dataset...")
    _, test_loader, class_names, _ = load_data_images()

    print(f"Classes detected: {class_names}")

    # --------------------------------------------------
    # Load model
    # --------------------------------------------------
    print("▶ Loading trained ResNet-18 model...")
    model = load_model(class_names)

    # --------------------------------------------------
    # Evaluation
    # --------------------------------------------------
    y_true, y_pred = [], []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(DEVICE)
            outputs = model(images)
            preds = torch.argmax(outputs, dim=1)

            y_true.extend(labels.numpy())
            y_pred.extend(preds.cpu().numpy())

    # --------------------------------------------------
    # Metrics
    # --------------------------------------------------
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_true, y_pred).tolist()
    report = classification_report(
        y_true, y_pred, target_names=class_names, output_dict=True
    )

    # --------------------------------------------------
    # Print (Viva Friendly)
    # --------------------------------------------------
    print("\n--- Classification Performance ---")
    print(f"Accuracy : {acc * 100:.2f}%")
    print(f"Precision: {prec:.3f}")
    print(f"Recall   : {rec:.3f}")
    print(f"F1 Score : {f1:.3f}")

    print("\nConfusion Matrix:")
    for row in cm:
        print(row)

    # --------------------------------------------------
    # Save results
    # --------------------------------------------------
    results = {
        "model": "ResNet-18 (Lip Hydration Classification)",
        "classes": class_names,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm,
        "classification_report": report
    }

    with open(RESULT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("✅ Image model evaluation completed successfully")
    print(f"📁 Results saved to: {RESULT_FILE}")
    print("=" * 70)


# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    main()
