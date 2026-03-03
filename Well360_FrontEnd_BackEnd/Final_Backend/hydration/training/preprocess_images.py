from torchvision import transforms
from core.config import IMG_SIZE


def get_transforms(train: bool = True):
    """
    Image transforms for lip hydration classification.

    Training: Aggressive augmentation to generalize across:
      - Different skin tones (light/dark)
      - Different genders (male/female)
      - Different lighting/camera conditions (studio vs phone)
      - With/without facial hair

    Val/Inference: Resize + normalize only.
    """
    if train:
        return transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),

            # ── Geometry ──
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=20),
            transforms.RandomAffine(
                degrees=0,
                translate=(0.10, 0.10),
                scale=(0.85, 1.15),
                shear=5,
            ),
            transforms.RandomPerspective(distortion_scale=0.2, p=0.3),

            # ── Color: generalize across skin tones and lighting ──
            transforms.ColorJitter(
                brightness=0.5,   # wide range: studio → phone camera
                contrast=0.5,
                saturation=0.5,   # helps with dark/light skin
                hue=0.10,         # small hue shift
            ),
            transforms.RandomGrayscale(p=0.10),

            # ── Blur/sharpen: robustness to focus / camera quality ──
            transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),

            # ── Tensor + ImageNet normalization ──
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),

            # ── Cutout regularization ──
            transforms.RandomErasing(p=0.20, scale=(0.02, 0.20)),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
