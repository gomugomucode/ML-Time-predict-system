"""
ML Queue Waiting-Time Training Pipeline (Inside Django Backend)
===============================================================
Self-contained data ingestion, leakage-free feature engineering, model training,
evaluation, and Joblib serialization pipeline for the Queue Waiting-Time
Prediction System.

Moving the training pipeline directly into `queue_backend/api/ml_trainer.py`
ensures that anyone who clones or copies the repository without the pre-built
33 MB `wait_time_rf_model.joblib` artifact will automatically train and save
the exact same deterministic RandomForestRegressor model on first startup
(or manually via `python manage.py train_model`).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# Feature schema (strictly prediction-time features available at arrival epoch t_A)
FEATURE_COLUMNS: list[str] = [
    "queue_length",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
]
TARGET_COLUMN: str = "wait_time"

# Default paths resolved relative to `queue_backend/api/`
API_DIR: Path = Path(__file__).resolve().parent
DEFAULT_MODEL_OUTPUT_PATH: Path = API_DIR / "wait_time_rf_model.joblib"
CANDIDATE_DATA_DIRS: list[Path] = [
    API_DIR / "data",                  # queue_backend/api/data
    API_DIR.parent / "data",           # queue_backend/data
    API_DIR.parent.parent / "data",    # <repo_root>/data
]


def resolve_data_dir(data_path: Optional[str | Path] = None) -> Path:
    """
    Locate the directory containing historical queue CSV datasets.
    Checks explicit path first, then candidate directories inside `queue_backend`
    and the repository root.
    """
    if data_path is not None:
        explicit = Path(data_path).resolve()
        if explicit.exists() and explicit.is_dir():
            return explicit
        raise FileNotFoundError(f"Specified dataset directory not found: {explicit}")

    for candidate in CANDIDATE_DATA_DIRS:
        if candidate.exists() and candidate.is_dir():
            if any(p.suffix.lower() == ".csv" for p in candidate.iterdir() if p.is_file()):
                return candidate

    raise FileNotFoundError(
        "Could not locate queue CSV dataset directory in candidate paths: "
        f"{[str(p) for p in CANDIDATE_DATA_DIRS]}"
    )


def load_queue_datasets(
    data_path: Optional[str | Path] = None,
    verbose: bool = True,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Load, standardize, and unify all queue CSV datasets from the target directory.

    Standardizations applied:
      - Column renaming to uniform schema: arrival_time, start_time, finish_time, wait_time.
      - Datetime parsing across all timestamp fields (handling format variations).
      - Normalized date extraction from arrival_time.
      - Origin file provenance tracking (source_file).
    """
    resolved_dir = resolve_data_dir(data_path)
    dfs: dict[str, pd.DataFrame] = {}

    for file in sorted(os.listdir(resolved_dir)):
        if not file.endswith(".csv"):
            continue

        file_path = resolved_dir / file
        df = pd.read_csv(file_path)

        # Standardize column names across datasets
        df = df.rename(
            columns={
                "arrival": "arrival_time",
                "start": "start_time",
                "end": "finish_time",
                "wait_min": "wait_time",
            }
        )

        # Parse timestamp columns to native datetime
        if file == "queue_data.csv":
            # queue_data.csv uses DD-MM-YYYY H.M format for arrival and start times
            df["arrival_time"] = pd.to_datetime(
                df["arrival_time"], format="%d-%m-%Y %H.%M"
            )
            if "start_time" in df.columns:
                df["start_time"] = pd.to_datetime(
                    df["start_time"], format="%d-%m-%Y %H.%M"
                )
            if "finish_time" in df.columns:
                df["finish_time"] = pd.to_datetime(df["finish_time"])
        else:
            # Handle cases where arrival_time has no date (date column provided separately)
            if "arrival_time" in df.columns:
                sample_val = (
                    str(df["arrival_time"].dropna().iloc[0])
                    if not df["arrival_time"].dropna().empty
                    else ""
                )
                if "date" in df.columns and (
                    "-" not in sample_val and "/" not in sample_val
                ):
                    df["arrival_time"] = pd.to_datetime(
                        df["date"].astype(str) + " " + df["arrival_time"].astype(str)
                    )
                else:
                    df["arrival_time"] = pd.to_datetime(df["arrival_time"])

            if "start_time" in df.columns:
                df["start_time"] = pd.to_datetime(df["start_time"])
            if "finish_time" in df.columns:
                df["finish_time"] = pd.to_datetime(df["finish_time"])

        # Derive uniform date and track dataset provenance
        if "arrival_time" in df.columns:
            df["date"] = df["arrival_time"].dt.date
        df["source_file"] = file

        dfs[file] = df
        if verbose:
            print(
                f"Loaded CSV: {file:40s} | Shape: {str(df.shape):12s} | Columns: {list(df.columns)}"
            )

    if dfs:
        combined_df = pd.concat(list(dfs.values()), ignore_index=True)
    else:
        combined_df = pd.DataFrame()

    return dfs, combined_df


def extract_arrival_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature Engineering & Data Leakage Prevention:
    Extracts prediction-time features strictly available at ticket issuance (t_A).
    Post-arrival variables (start_time, finish_time, actual service duration) are excluded.
    """
    df = df.copy()

    # Extract temporal features from arrival_time
    df["arrival_time"] = pd.to_datetime(df["arrival_time"])
    df["hour_of_day"] = df["arrival_time"].dt.hour
    df["day_of_week"] = df["arrival_time"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Impute missing queue_length if not recorded (e.g., in wait_times.csv)
    if "queue_length" not in df.columns or df["queue_length"].isnull().any():
        df["queue_length"] = df["queue_length"].fillna(0)

    return df


def train_and_evaluate_model(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
) -> tuple[RandomForestRegressor, dict[str, float]]:
    """
    Train and evaluate a RandomForestRegressor model on queue waiting-time features.
    Computes MAE, RMSE, R2, and benchmarks against a naive Historical Mean baseline.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    baseline_pred = np.full_like(y_test, fill_value=y_train.mean())
    baseline_mae = float(mean_absolute_error(y_test, baseline_pred))
    improvement = ((baseline_mae - mae) / baseline_mae) * 100

    metrics = {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "baseline_mae": baseline_mae,
        "improvement_pct": improvement,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
    }

    return model, metrics


def train_and_save_model(
    data_path: Optional[str | Path] = None,
    output_path: Optional[str | Path] = None,
    verbose: bool = True,
) -> tuple[RandomForestRegressor, dict[str, float], Path]:
    """
    End-to-end training pipeline:
      1. Load and harmonize CSV datasets from `data/`.
      2. Extract leakage-free arrival-time features.
      3. Train and benchmark RandomForestRegressor (100 trees, seed=42).
      4. Save serialized model to `queue_backend/api/wait_time_rf_model.joblib`.

    Returns:
        (trained_model, evaluation_metrics, saved_model_path)
    """
    _, raw_df = load_queue_datasets(data_path=data_path, verbose=verbose)

    if raw_df.empty:
        raise ValueError("No CSV records found in the dataset directory.")

    full_df = extract_arrival_features(raw_df)
    X = full_df[FEATURE_COLUMNS]
    y = full_df[TARGET_COLUMN]

    if verbose:
        print("\n" + "=" * 60)
        print(f"Combined Dataset Shape: {full_df.shape}")
        print("=" * 60)
        print(f"Features (X) Shape: {X.shape} | Target (y) Shape: {y.shape}")
        print(f"Selected Features: {FEATURE_COLUMNS}")
        print(f"Target Variable:   '{TARGET_COLUMN}'")
        print("\nMissing Values in Features (X):")
        print(X.isnull().sum())
        print("\n" + "=" * 60)
        print("Training RandomForestRegressor (100 estimators, 80/20 split)...")
        print("=" * 60)

    model, metrics = train_and_evaluate_model(X, y)

    target_path = Path(output_path) if output_path is not None else DEFAULT_MODEL_OUTPUT_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, target_path)

    if verbose:
        print("Model Training & Evaluation Complete:")
        print(f"  - Mean Absolute Error (MAE):       {metrics['mae']:.2f} minutes")
        print(f"  - Root Mean Squared Error (RMSE):  {metrics['rmse']:.2f} minutes")
        print(f"  - Coefficient of Determination R2: {metrics['r2']:.4f}")
        print(f"  - Naive Baseline MAE (Mean):       {metrics['baseline_mae']:.2f} minutes")
        print(f"  - Accuracy Improvement:            {metrics['improvement_pct']:.2f}% over baseline")
        print(f"\nModel saved successfully to '{target_path}'!")

    logger.info(
        "Trained and saved wait-time model to %s (MAE=%.2f min, R2=%.4f, +%.2f%% over baseline)",
        target_path,
        metrics["mae"],
        metrics["r2"],
        metrics["improvement_pct"],
    )

    return model, metrics, target_path


if __name__ == "__main__":
    train_and_save_model(verbose=True)
