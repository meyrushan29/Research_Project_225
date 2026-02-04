import logging
import sys
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
import json
from datetime import datetime

def setup_logging(level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger('hydration_ml')
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler('hydration_ml.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def save_pickle(obj: Any, path: Path) -> None:

    try:
        with open(path, 'wb') as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise IOError(f"Failed to save pickle to {path}: {e}")


def load_pickle(path: Path) -> Any:

    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        raise IOError(f"Failed to load pickle from {path}: {e}")


def ensure_dir(path: Path) -> Path:

    path.mkdir(parents=True, exist_ok=True)
    return path


def calculate_model_metrics(y_true, y_pred, model_type: str) -> Dict[str, float]:

    from sklearn.metrics import (
        mean_squared_error, mean_absolute_error, r2_score,
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report
    )

    metrics = {}

    if model_type == 'regression':
        metrics['mse'] = mean_squared_error(y_true, y_pred)
        metrics['rmse'] = np.sqrt(metrics['mse'])
        metrics['mae'] = mean_absolute_error(y_true, y_pred)
        metrics['r2'] = r2_score(y_true, y_pred)
        metrics['mape'] = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    elif model_type == 'classification':
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        metrics['f1'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)

        # Confusion matrix as dictionary
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()

    return metrics


def save_metrics(metrics: Dict, path: Path) -> None:

    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)


class Timer:


    def __enter__(self):
        self.start = datetime.now()
        return self

    def __exit__(self, *args):
        self.end = datetime.now()
        self.duration = self.end - self.start

    def get_duration(self) -> float:
        return self.duration.total_seconds()


def calculate_unified_score(input_type: str, value: Any, confidence: float = 1.0) -> int:
    """
    Unified Hydration Score (0-100)
    0 = Severely Dehydrated
    100 = Perfectly Hydrated
    """
    score = 50

    if input_type == 'form':
        # Value is recommended_water_liters (0.0 to 4.0+)
        # 0.0L needed -> Score 100
        # 4.0L needed -> Score 0
        rec_liter = float(value)
        if rec_liter <= 0: return 100
        
        # Linear decay: 100 - (liters * 25)
        # 0L -> 100
        # 1L -> 75
        # 2L -> 50
        # 3L -> 25
        # 4L -> 0
        score = 100 - (rec_liter * 25)
        
    elif input_type == 'lip':
        # Value is Label (Normal/Dehydrate), Confidence is 0.0-1.0
        label = str(value).lower()
        if "normal" in label:
            # 50 to 100 based on confidence
            # Conf 0.5 -> 75
            # Conf 1.0 -> 100
            score = 50 + (confidence * 50)
        else:
            # 50 to 0 based on confidence (Dehydrated)
            # Conf 0.5 -> 25
            # Conf 1.0 -> 0
            score = 50 - (confidence * 50)

    return int(max(0, min(100, score)))
