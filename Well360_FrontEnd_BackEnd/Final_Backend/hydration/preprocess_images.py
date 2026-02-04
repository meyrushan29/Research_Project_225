from torchvision import transforms
from core.config import IMG_SIZE


# ======================================================
# IMAGE PREPROCESSING (SAFE & STANDARDIZED)
# ======================================================
def get_transforms(train: bool = True):
    """
    Returns image transformations for lip dehydration classification.
    Uses ImageNet normalization (required for ResNet18).
    """

    if train:
        return transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(20), # Increased rotation
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)), # Shift position
            transforms.ColorJitter(
                brightness=0.2, # Stronger lighting variance
                contrast=0.2,
                saturation=0.2,
                hue=0.05
            ),
            transforms.RandomGrayscale(p=0.1), # Lighting invariance
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
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


# ======================================================
# TEST
# ======================================================
if __name__ == "__main__":
    t_train = get_transforms(train=True)
    t_test = get_transforms(train=False)

    print("Training transforms:", t_train)
    print("Testing transforms :", t_test)
