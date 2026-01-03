import json
import joblib
import numpy as np
from pathlib import Path
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from config import (
    MODEL_REG_PATH,
    MODEL_CLF_PATH,
    PREPROCESSOR_PATH
)

from dataLoad import load_data
from preprocess import prepare_data

# ======================================================
# Paths
# ======================================================
RESULT_DIR = Path("results")
RESULT_DIR.mkdir(exist_ok=True)

# ======================================================
# Regression metrics
# ======================================================
def evaluate_regression(y_true, y_pred):
    return {
        "rmse": mean_squared_error(y_true, y_pred, squared=False),
        "mae": mean_absolute_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred)
    }

def regression_tolerance_accuracy(y_true, y_pred, tolerance_l=0.05):
    """
    Percentage of predictions within ± tolerance (liters)
    Default: ±0.05 L (50 ml)
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return float((np.abs(y_true - y_pred) <= tolerance_l).mean())

# ======================================================
# Classification metrics
# ======================================================
def evaluate_classification(y_true, y_pred):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average="weighted", zero_division=0),
        "recall": recall_score(y_true, y_pred, average="weighted", zero_division=0),
        "f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(
            y_true, y_pred, output_dict=True, zero_division=0
        )
    }

# ======================================================
# Main evaluation
# ======================================================
def main():
    print("\n" + "=" * 72)
    print(" HYDRATION MODEL EVALUATION (FINAL PIPELINE)".center(72))
    print("=" * 72)

    # --------------------------------------------------
    # Load models
    # --------------------------------------------------
    print("\n▶ Loading trained models...")
    regressor = joblib.load(MODEL_REG_PATH)
    classifier = joblib.load(MODEL_CLF_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)

    # --------------------------------------------------
    # Load and prepare data
    # --------------------------------------------------
    print("▶ Loading and preparing dataset...")
    df = load_data()

    (
        X_train, X_test,
        y_reg_train, y_reg_test,
        y_clf_train, y_clf_test,
        *_  # ignore disease targets & encoders
    ) = prepare_data(df)

    X_test_processed = preprocessor.transform(X_test)

    results = {}

    # ==================================================
    # REGRESSION EVALUATION
    # ==================================================
    print("\n--- Water Requirement Prediction (Next 4 Hours) ---")
    y_reg_pred = regressor.predict(X_test_processed)

    reg_metrics = evaluate_regression(y_reg_test, y_reg_pred)
    reg_accuracy_50ml = regression_tolerance_accuracy(
        y_reg_test, y_reg_pred, tolerance_l=0.05
    )

    reg_metrics["accuracy_within_50ml"] = reg_accuracy_50ml
    results["water_prediction_regression"] = reg_metrics

    print(f"MAE               : {reg_metrics['mae']:.3f} L")
    print(f"RMSE              : {reg_metrics['rmse']:.3f} L")
    print(f"R² Score          : {reg_metrics['r2']:.3f}")
    print(f"Accuracy (±50 ml) : {reg_accuracy_50ml * 100:.2f}%")

    # ==================================================
    # HYDRATION RISK CLASSIFICATION
    # ==================================================
    print("\n--- Hydration Risk Classification ---")
    y_clf_pred = classifier.predict(X_test_processed)

    clf_metrics = evaluate_classification(y_clf_test, y_clf_pred)
    results["hydration_risk_classification"] = clf_metrics

    print(f"Accuracy : {clf_metrics['accuracy'] * 100:.2f}%")
    print(f"Precision: {clf_metrics['precision']:.3f}")
    print(f"Recall   : {clf_metrics['recall']:.3f}")
    print(f"F1 Score : {clf_metrics['f1']:.3f}")

    # ==================================================
    # Save results
    # ==================================================
    output_path = RESULT_DIR / "final_hydration_metrics.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 72)
    print(" Evaluation completed successfully".center(72))
    print(f" Metrics saved to: {output_path}".center(72))
    print("=" * 72)

# ======================================================
# Run
# ======================================================
if __name__ == "__main__":
    main()
