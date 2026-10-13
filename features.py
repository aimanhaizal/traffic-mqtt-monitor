"""Shared feature preparation used for both model training and inference."""

import numpy as np
import pandas as pd

CATEGORICAL_FEATURES = [
    "is_holiday",
    "weather_type",
    "weather_description",
]

NUMERIC_FEATURES = [
    "air_pollution_index",
    "humidity",
    "wind_speed",
    "wind_direction",
    "visibility_in_miles",
    "dew_point",
    "temperature",
    "rain_p_h",
    "snow_p_h",
    "clouds_all",
    "hour",
    "day_of_week",
    "month",
    "day",
]

TARGET_COLUMN = "traffic_volume"
REQUIRED_COLUMNS = [
    "date_time",
    "is_holiday",
    "air_pollution_index",
    "humidity",
    "wind_speed",
    "wind_direction",
    "visibility_in_miles",
    "dew_point",
    "temperature",
    "rain_p_h",
    "snow_p_h",
    "clouds_all",
    "weather_type",
    "weather_description",
]


def make_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert raw traffic rows to the exact feature columns used by the model."""
    data = frame.copy()

    if "date_time" not in data.columns:
        raise ValueError("Input data must contain a 'date_time' column.")

    timestamps = pd.to_datetime(data["date_time"], errors="coerce")
    if timestamps.isna().any():
        raise ValueError("One or more date_time values could not be parsed.")

    data["hour"] = timestamps.dt.hour
    data["day_of_week"] = timestamps.dt.dayofweek
    data["month"] = timestamps.dt.month
    data["day"] = timestamps.dt.day

    # Keep categorical values as strings while preserving missing values for imputation.
    for column in CATEGORICAL_FEATURES:
        if column not in data.columns:
            data[column] = np.nan
        data[column] = data[column].map(
            lambda value: str(value) if pd.notna(value) else np.nan
        )

    for column in NUMERIC_FEATURES:
        if column not in data.columns:
            data[column] = np.nan
        data[column] = pd.to_numeric(data[column], errors="coerce")

    # Fixed order prevents training/inference column drift.
    return data[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
