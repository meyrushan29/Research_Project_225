import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import os
from datetime import datetime

from config import DEVICE, MODEL_OUT
from preprocess_images import get_transforms   # ✅ CORRECT FILE


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
# RECOMMENDATION LOGIC
# ======================================================
def get_recommendation(label):
    if label == "Dehydrate":
        return (
            "Possible dehydration detected.\n"
            "- Drink 1–2 glasses of water immediately\n"
            "- Avoid heavy activity\n"
            "- Avoid caffeine & alcohol\n"
            "- Monitor urine color\n"
            "- Seek medical advice if symptoms persist"
        )
    else:
        return (
            "Hydration level appears normal.\n"
            "- Maintain regular water intake\n"
            "- Stay hydrated during activity"
        )


# ======================================================
# HYDRATION SCORE (0–100)
# ======================================================
def calculate_hydration_score(label, confidence):
    if label == "Dehydrate":
        return int(confidence * 40)
    return int(60 + confidence * 40)


# ======================================================
# FONT SAFE LOADER
# ======================================================
def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()


# ======================================================
# UI OVERLAY
# ======================================================
def draw_hydration_score(image, score):
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    title_font = load_font(24)
    text_font = load_font(18)

    if score < 40:
        bg, bar, status = (220, 60, 60, 150), (200, 40, 40, 220), "Dehydrated"
    elif score < 70:
        bg, bar, status = (240, 170, 60, 150), (220, 140, 40, 220), "Moderate"
    else:
        bg, bar, status = (60, 160, 90, 150), (40, 130, 70, 220), "Normal"

    x1, y1, x2, y2 = 15, 15, 360, 150
    draw.rectangle((x1, y1, x2, y2), fill=bg)

    draw.text((x1 + 15, y1 + 10), "Hydration Status", fill="white", font=title_font)
    draw.text((x1 + 15, y1 + 50), f"Score: {score}/100", fill="white", font=text_font)
    draw.text((x1 + 15, y1 + 75), f"Status: {status}", fill="white", font=text_font)

    bar_x1, bar_y1, bar_x2 = x1 + 15, y1 + 110, x2 - 15
    draw.rectangle((bar_x1, bar_y1, bar_x2, bar_y1 + 14), fill=(255, 255, 255, 90))

    fill = int((score / 100) * (bar_x2 - bar_x1))
    draw.rectangle((bar_x1, bar_y1, bar_x1 + fill, bar_y1 + 14), fill=bar)

    return Image.alpha_composite(image, overlay).convert("RGB")


# ======================================================
# IMAGE SELECTION
# ======================================================
def select_image_from_terminal():
    images = [f for f in os.listdir(".") if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    if not images:
        raise FileNotFoundError("No images found in current directory")

    print("\nAvailable Images:")
    for i, img in enumerate(images, 1):
        print(f"{i}. {img}")

    choice = input("\nSelect image number (default 1): ").strip()
    return images[int(choice) - 1] if choice.isdigit() else images[0]


# ======================================================
# PREDICTION
# ======================================================
def predict_image(image_path, model, class_names):
    transform = get_transforms(train=False)
    image = Image.open(image_path).convert("RGB")

    tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(tensor)
        probs = F.softmax(outputs, dim=1)
        pred = probs.argmax(dim=1).item()

    label = class_names[pred]
    confidence = probs[0][pred].item()
    score = calculate_hydration_score(label, confidence)

    final_image = draw_hydration_score(image, score)

    os.makedirs("img", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"img/result_{timestamp}.png"
    final_image.save(out_path)

    plt.imshow(final_image)
    plt.axis("off")
    plt.title(f"{label} | Score: {score}/100")
    plt.show()

    return label, score, confidence, get_recommendation(label), out_path


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    class_names = ["Dehydrate", "Normal"]  # must match training
    model = load_model(class_names)

    image_path = select_image_from_terminal()

    label, score, conf, rec, saved = predict_image(
        image_path, model, class_names
    )

    print("\n" + "=" * 60)
    print(f"Prediction      : {label}")
    print(f"Hydration Score : {score}/100")
    print(f"Confidence      : {conf:.2f}")
    print(f"Saved Image     : {saved}")
    print("\nRecommendation:\n" + rec)
    print("=" * 60)
