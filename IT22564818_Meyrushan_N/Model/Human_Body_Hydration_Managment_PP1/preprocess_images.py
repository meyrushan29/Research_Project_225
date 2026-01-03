from torchvision import transforms
from config import IMG_SIZE


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
            transforms.RandomRotation(10),
            transforms.ColorJitter(
                brightness=0.1,
                contrast=0.1,
                saturation=0.1
            ),
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
