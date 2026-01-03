import pandas as pd
import numpy as np
import json
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_score

from config import (
    RF_REGRESSOR_PARAMS,
    RF_CLASSIFIER_PARAMS,
    RANDOM_STATE,
    MODEL_REG_PATH,
    MODEL_CLF_PATH,
    PREPROCESSOR_PATH,
    ENCODER_PATH
)

from utils import (
    setup_logging,
    save_pickle,
    calculate_model_metrics,
    Timer
)

from dataLoad import load_data
from preprocess import build_preprocessor, prepare_data

LOG = setup_logging()


# =====================================================
# MODEL TRAINER (FINAL – PANEL SAFE)
# =====================================================
class AdvancedModelTrainer:

    def __init__(self):
        self.regressor = None
        self.classifier = None
        self.preprocessor = None
        self.label_encoder = None
        self.training_metrics = {}

    # -------------------------------------------------
    # FEATURE PREPARATION
    # -------------------------------------------------
    def prepare_features(self, df: pd.DataFrame):
        LOG.info("Preparing features (engineering + preprocessing)...")

        (
            X_train,
            X_test,
            y_reg_train,
            y_reg_test,
            y_clf_train,
            y_clf_test,
            le_hydration
        ) = prepare_data(df)

        self.preprocessor = build_preprocessor()

        X_train_p = self.preprocessor.fit_transform(X_train)
        X_test_p = self.preprocessor.transform(X_test)

        self.label_encoder = le_hydration

        LOG.info(
            f"Processed features | Train: {X_train_p.shape}, Test: {X_test_p.shape}"
        )

        return (
            X_train_p,
            X_test_p,
            y_reg_train,
            y_reg_test,
            y_clf_train,
            y_clf_test
        )

    # -------------------------------------------------
    # REGRESSION MODEL (NEXT 4H WATER)
    # -------------------------------------------------
    def train_regressor(self, X_train, y_train, X_test, y_test):
        LOG.info("Training RandomForest Regressor (Next 4h Water)...")

        with Timer() as t:
            model = RandomForestRegressor(**RF_REGRESSOR_PARAMS)
            model.fit(X_train, y_train)

        preds = model.predict(X_test)
        metrics = calculate_model_metrics(y_test, preds, "regression")

        self.training_metrics["regression"] = metrics

        LOG.info(
            f"Regressor trained in {t.get_duration():.2f}s | "
            f"RMSE={metrics['rmse']:.3f}, R²={metrics['r2']:.3f}"
        )

        return model

    # -------------------------------------------------
    # CLASSIFICATION MODEL (HYDRATION RISK)
    # -------------------------------------------------
    def train_classifier(self, X_train, y_train, X_test, y_test):
        LOG.info("Training Hydration Risk Classifier...")

        with Timer() as t:
            model = RandomForestClassifier(**RF_CLASSIFIER_PARAMS)
            model.fit(X_train, y_train)

        preds = model.predict(X_test)
        metrics = calculate_model_metrics(y_test, preds, "classification")

        cv_scores = cross_val_score(
            model, X_train, y_train, cv=5, scoring="accuracy"
        )

        metrics["cv_accuracy_mean"] = cv_scores.mean()
        metrics["cv_accuracy_std"] = cv_scores.std()

        self.training_metrics["hydration_classification"] = metrics

        LOG.info(
            f"Classifier trained in {t.get_duration():.2f}s | "
            f"Accuracy={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}"
        )

        return model

    # -------------------------------------------------
    # SAVE ARTIFACTS
    # -------------------------------------------------
    def save_all(self):
        LOG.info("Saving models and preprocessing artifacts...")

        MODEL_DIR = Path("models")
        MODEL_DIR.mkdir(exist_ok=True)

        save_pickle(self.regressor, MODEL_REG_PATH)
        save_pickle(self.classifier, MODEL_CLF_PATH)
        save_pickle(self.preprocessor, PREPROCESSOR_PATH)
        save_pickle(self.label_encoder, ENCODER_PATH)

        with open(MODEL_DIR / "training_metrics.json", "w") as f:
            json.dump(self.training_metrics, f, indent=2)

        LOG.info("Models and artifacts saved successfully")

    # -------------------------------------------------
    # FULL PIPELINE
    # -------------------------------------------------
    def train_pipeline(self, df: pd.DataFrame):
        LOG.info("Starting full training pipeline...")

        (
            X_train,
            X_test,
            y_reg_train,
            y_reg_test,
            y_clf_train,
            y_clf_test
        ) = self.prepare_features(df)

        self.regressor = self.train_regressor(
            X_train, y_reg_train, X_test, y_reg_test
        )

        self.classifier = self.train_classifier(
            X_train, y_clf_train, X_test, y_clf_test
        )

        self.save_all()
        self.print_summary()

    # -------------------------------------------------
    # SUMMARY (VIVA READY)
    # -------------------------------------------------
    def print_summary(self):
        LOG.info("\n" + "=" * 60)
        LOG.info("FINAL TRAINING SUMMARY")
        LOG.info("=" * 60)

        reg = self.training_metrics["regression"]
        clf = self.training_metrics["hydration_classification"]

        LOG.info("Water Requirement Regressor:")
        LOG.info(f"  RMSE: {reg['rmse']:.3f}")
        LOG.info(f"  MAE : {reg['mae']:.3f}")
        LOG.info(f"  R²  : {reg['r2']:.3f}")

        LOG.info("\nHydration Risk Classifier:")
        LOG.info(f"  Accuracy: {clf['accuracy']:.3f}")
        LOG.info(f"  F1 Score: {clf['f1']:.3f}")
        LOG.info(
            f"  CV Accuracy: {clf['cv_accuracy_mean']:.3f} "
            f"± {clf['cv_accuracy_std']:.3f}"
        )

        LOG.info("=" * 60)


# =====================================================
# MAIN
# =====================================================
def main():
    LOG.info("=" * 60)
    LOG.info("HYDRATION ML TRAINING PIPELINE (TIME-WINDOW AWARE)")
    LOG.info("=" * 60)

    df = load_data()
    LOG.info(f"Dataset loaded: {len(df)} samples")

    trainer = AdvancedModelTrainer()
    trainer.train_pipeline(df)

    LOG.info("TRAINING COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
