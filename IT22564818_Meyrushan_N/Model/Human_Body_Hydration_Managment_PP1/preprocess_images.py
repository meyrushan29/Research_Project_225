from torchvision import transforms
from config import IMG_SIZE


# ======================================================
# IMAGE PREPROCESSING (SAFE & STANDARDIZED)
# ======================================================
def get_transforms(train: bool = True):
    """
    Returns image transformations for lip dehydration classification.
    Uses ImageNet normalization (required for ResNet18).
    
    IMPORTANT: Includes center cropping to focus on lips and reduce background.
    This addresses the dataset quality issue where 83% of images have too much background.
    """

    if train:
        return transforms.Compose([
            # Step 1: Resize to larger size first
            transforms.Resize((int(IMG_SIZE * 1.3), int(IMG_SIZE * 1.3))),
            
            # Step 2: Center crop to focus on lips (removes background)
            transforms.CenterCrop((IMG_SIZE, IMG_SIZE)),
            
            # Step 3: Data augmentation
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(
                brightness=0.2,  # Increased for better robustness
                contrast=0.2,
                saturation=0.15
            ),
            
            # Step 4: Convert to tensor and normalize
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    else:
        return transforms.Compose([
            # Step 1: Resize to larger size first
            transforms.Resize((int(IMG_SIZE * 1.3), int(IMG_SIZE * 1.3))),
            
            # Step 2: Center crop to focus on lips (removes background)
            transforms.CenterCrop((IMG_SIZE, IMG_SIZE)),
            
            # Step 3: Convert to tensor and normalize
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
