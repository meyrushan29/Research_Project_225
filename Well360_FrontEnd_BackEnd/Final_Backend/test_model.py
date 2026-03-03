"""Quick model test on training data samples."""
import torch, torch.nn.functional as F, os, glob, sys
sys.path.insert(0, '.')
from torchvision import datasets
from hydration.training.preprocess_images import get_transforms
from hydration.imagePredict_mobilenet import load_model
from PIL import Image

ds = datasets.ImageFolder(r'hydration/data_processed')
model = load_model(ds.classes)
t = get_transforms(False)

correct = 0
total = 0
for cls_idx, cls_name in enumerate(ds.classes):
    samples = [s for s in ds.samples if s[1] == cls_idx]
    cls_correct = 0
    for path, label in samples:
        img = Image.open(path).convert('RGB')
        tensor = t(img).unsqueeze(0)
        with torch.no_grad():
            probs = F.softmax(model(tensor), dim=1)
        pred_idx = probs.argmax().item()
        if pred_idx == label:
            cls_correct += 1
        total += 1
    correct += cls_correct
    print(f"{cls_name}: {cls_correct}/{len(samples)} correct ({100*cls_correct/len(samples):.1f}%)")

print(f"\nOverall: {correct}/{total} ({100*correct/total:.1f}%)")

# Test latest upload
uploads = sorted(glob.glob('img/uploads/result_*.png'))
if uploads:
    latest = uploads[-1]
    img = Image.open(latest).convert('RGB')
    tensor = t(img).unsqueeze(0)
    with torch.no_grad():
        probs = F.softmax(model(tensor), dim=1)
    print(f"\nLatest upload ({os.path.basename(latest)}):")
    print(f"  Dehydrate={probs[0][0].item():.4f}, Normal={probs[0][1].item():.4f}")
