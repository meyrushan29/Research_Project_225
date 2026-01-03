from torchvision import datasets
from torch.utils.data import DataLoader, random_split
from config import DATA_DIR, BATCH_SIZE
from preprocess_images import get_transforms


def load_data_images():
    train_transform = get_transforms(train=True)
    test_transform = get_transforms(train=False)

    full_dataset = datasets.ImageFolder(DATA_DIR, transform=train_transform)
    class_names = full_dataset.classes

    train_size = int(0.8 * len(full_dataset))
    test_size = len(full_dataset) - train_size

    train_dataset, test_dataset = random_split(
        full_dataset, [train_size, test_size]
    )

    # IMPORTANT: apply test transform
    test_dataset.dataset.transform = test_transform

    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True
    )

    test_loader = DataLoader(
        test_dataset, batch_size=BATCH_SIZE, shuffle=False
    )

    return train_loader, test_loader, class_names, train_dataset
