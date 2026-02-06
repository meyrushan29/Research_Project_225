import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from typing import Tuple, List

from core.config import (
    NUMERIC_COLS,
    CATEGORICAL_COLS,
    TARGET_COLS,
    RANDOM_STATE,
    TEST_SIZE,
    DROP_COLS
)
from core.utils import setup_logging

LOG = setup_logging()


# ======================================================
# ADVANCED PREPROCESSOR (FINAL & API SAFE)
# ======================================================
class AdvancedPreprocessor(BaseEstimator, TransformerMixin):

    def __init__(self):
        self.numeric_cols = NUMERIC_COLS
        self.categorical_cols = CATEGORICAL_COLS
        self.target_cols = TARGET_COLS
        self.drop_cols = DROP_COLS

        self.preprocessor = None
        self.feature_names_in_ = None   # 🔥 REQUIRED FOR PREDICTION

    # --------------------------------------------------
    # FIT
    # --------------------------------------------------
    def fit(self, X: pd.DataFrame, y=None):
        X = X.copy()

        # Remove targets & ID columns
        X = X.drop(columns=self.target_cols + self.drop_cols, errors="ignore")

        actual_numeric = [c for c in self.numeric_cols if c in X.columns]
        actual_categorical = [c for c in self.categorical_cols if c in X.columns]

        LOG.info(
            f"Preprocessor using {len(actual_numeric)} numeric and "
            f"{len(actual_categorical)} categorical features"
        )

        numeric_pipeline = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])

        categorical_pipeline = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(
                handle_unknown="ignore",
                drop="first",
                sparse_output=False
            ))
        ])

        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", numeric_pipeline, actual_numeric),
                ("cat", categorical_pipeline, actual_categorical)
            ],
            remainder="drop"
        )

        self.preprocessor.fit(X)

        # 🔥 SAVE EXACT INPUT FEATURE ORDER
        self.feature_names_in_ = actual_numeric + actual_categorical

        return self

    # --------------------------------------------------
    # TRANSFORM
    # --------------------------------------------------
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        X = X.copy()
        X = X.drop(columns=self.target_cols + self.drop_cols, errors="ignore")

        return self.preprocessor.transform(X)

    # --------------------------------------------------
    # FEATURE NAMES (OPTIONAL – DEBUG / EXPLAIN)
    # --------------------------------------------------
    def get_feature_names(self) -> List[str]:
        if self.preprocessor is None:
            raise RuntimeError("Preprocessor not fitted")

        feature_names = []

        # Numeric
        num_features = self.preprocessor.transformers_[0][2]
        feature_names.extend(num_features)

        # Categorical
        cat_pipeline = self.preprocessor.named_transformers_["cat"]
        onehot = cat_pipeline.named_steps["onehot"]
        cat_features = onehot.get_feature_names_out(
            self.preprocessor.transformers_[1][2]
        )
        feature_names.extend(cat_features.tolist())

        return feature_names


# ======================================================
# BUILD PREPROCESSOR
# ======================================================
def build_preprocessor() -> AdvancedPreprocessor:
    return AdvancedPreprocessor()


# ======================================================
# PREPARE DATA (TRAINING PIPELINE)
# ======================================================
def prepare_data(df: pd.DataFrame) -> Tuple:

    # -------------------------------
    # FEATURES & TARGETS
    # -------------------------------
    X = df.drop(columns=TARGET_COLS, errors="ignore")

    y_reg = df["Recommended_Water_Next_4_Hours"]
    y_clf_raw = df["Hydration_Risk_Level"]

    # Encode classification target ONLY
    le_hydration = LabelEncoder()
    y_clf = le_hydration.fit_transform(y_clf_raw)

    # -------------------------------
    # TRAIN / TEST SPLIT
    # -------------------------------
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X,
        y_reg,
        y_clf,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_clf
    )

    LOG.info(f"Train X: {X_train.shape}, Test X: {X_test.shape}")

    return (
        X_train,
        X_test,
        y_reg_train,
        y_reg_test,
        y_clf_train,
        y_clf_test,
        le_hydration
    )
