"""Train and save the traffic-volume Random Forest regression pipeline."""

import os

from dotenv import load_dotenv

load_dotenv()
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    make_features,
)

CSV_PATH = Path(os.getenv("CSV_PATH", "TrafficVolumeData.csv"))
MODEL_PATH = Path(os.getenv("MODEL_PATH", "traffic_model.pkl"))


def main():
    print(f"Loading dataset from: {CSV_PATH}")
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {CSV_PATH}. Put TrafficVolumeData.csv in the "
            "project root or set CSV_PATH."
        )

    data = pd.read_csv(CSV_PATH)
    if TARGET_COLUMN not in data.columns:
        raise ValueError(f"Dataset must contain the target column '{TARGET_COLUMN}'.")

    y = pd.to_numeric(data[TARGET_COLUMN], errors="coerce")
    valid_target = y.notna()
    data = data.loc[valid_target].copy()
    y = y.loc[valid_target].astype(float)
    X = make_features(data)

    print(f"Dataset loaded: {len(data)} usable rows")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    numeric_pipeline = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median"))]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=200,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    print("Training Random Forest...")
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    print("\nHoldout evaluation")
    print("------------------")
    print(f"Mean Absolute Error: {mean_absolute_error(y_test, predictions):.2f}")
    print(f"R² Score:            {r2_score(y_test, predictions):.4f}")

    print("\nRetraining on the complete dataset...")
    pipeline.fit(X, y)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
