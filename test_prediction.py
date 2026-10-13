"""Run one example row through the saved model."""

import os

from dotenv import load_dotenv

load_dotenv()
from pathlib import Path

import joblib
import pandas as pd

from features import TARGET_COLUMN, make_features

CSV_PATH = Path(os.getenv("CSV_PATH", "TrafficVolumeData.csv"))
MODEL_PATH = Path(os.getenv("MODEL_PATH", "traffic_model.pkl"))


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}. Run `python ml_model.py` first."
        )

    data = pd.read_csv(CSV_PATH, nrows=1)
    if data.empty:
        raise ValueError("The dataset contains no rows.")

    model = joblib.load(MODEL_PATH)
    X = make_features(data)
    prediction = float(model.predict(X)[0])

    if TARGET_COLUMN in data.columns and pd.notna(data.iloc[0][TARGET_COLUMN]):
        actual = float(data.iloc[0][TARGET_COLUMN])
        print(f"Actual traffic volume:    {actual:.0f}")
        print(f"Predicted traffic volume: {prediction:.0f}")
    else:
        print(f"Predicted traffic volume: {prediction:.0f}")


if __name__ == "__main__":
    main()
