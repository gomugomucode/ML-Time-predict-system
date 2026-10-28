import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PATH = "data"


def load_queue_datasets(
    data_path: str = PATH,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Load, standardize, and unify all queue CSV datasets from the target directory.

    Standardizations applied:
      - Column renaming to uniform schema: arrival_time, start_time, finish_time, wait_time.
      - Datetime parsing across all timestamp fields (handling format variations).
      - Normalized date extraction from arrival_time.
      - Origin file provenance tracking (source_file).
    """
    dfs: dict[str, pd.DataFrame] = {}

    for file in sorted(os.listdir(data_path)):
        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(data_path, file)
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
        print(
            f"Loaded CSV: {file:40s} | Shape: {str(df.shape):12s} | Columns: {list(df.columns)}"
        )

    # Combine all loaded CSVs into one unified DataFrame
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
) -> tuple[RandomForestRegressor, dict[str, float]]:
    """
    Train and evaluate a RandomForestRegressor model on queue waiting-time features.
    Computes MAE, RMSE, R2, and benchmarks against a naive Historical Mean baseline.
    """
    # 80% training / 20% testing split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Train the Random Forest Regressor
    model = RandomForestRegressor(n_estimators=100, random_state=random_state)
    model.fit(X_train, y_train)

    # Predictions on the test set
    y_pred = model.predict(X_test)

    # Calculate evaluation metrics
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    # Baseline comparison: Historical Mean
    baseline_pred = np.full_like(y_test, fill_value=y_train.mean())
    baseline_mae = float(mean_absolute_error(y_test, baseline_pred))
    improvement = ((baseline_mae - mae) / baseline_mae) * 100

    metrics = {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "baseline_mae": baseline_mae,
        "improvement_pct": improvement,
    }

    return model, metrics


if __name__ == "__main__":
    dfs, raw_df = load_queue_datasets(PATH)

    if not raw_df.empty:
        # 1. Extract prediction-time features
        full_df = extract_arrival_features(raw_df)

        # 2. Define X (Inputs) and y (Target)
        features = ["queue_length", "hour_of_day", "day_of_week", "is_weekend"]
        target = "wait_time"

        X = full_df[features]
        y = full_df[target]

        print("\n" + "=" * 60)
        print(f"Combined Dataset Shape: {full_df.shape}")
        print("=" * 60)
        print(f"Features (X) Shape: {X.shape} | Target (y) Shape: {y.shape}")
        print(f"Selected Features: {features}")
        print(f"Target Variable:   '{target}'")
        print("\nMissing Values in Features (X):")
        print(X.isnull().sum())

        # 3. Train and evaluate the model
        print("\n" + "=" * 60)
        print("Training RandomForestRegressor (100 estimators, 80/20 split)...")
        print("=" * 60)
        model, metrics = train_and_evaluate_model(X, y)

        print("Model Training & Evaluation Complete:")
        print(f"  - Mean Absolute Error (MAE):     {metrics['mae']:.2f} minutes")
        print(f"  - Root Mean Squared Error (RMSE): {metrics['rmse']:.2f} minutes")
        print(f"  - Coefficient of Determination (R2): {metrics['r2']:.4f}")
        print(f"  - Naive Baseline MAE (Mean):     {metrics['baseline_mae']:.2f} minutes")
        print(f"  - Accuracy Improvement:          {metrics['improvement_pct']:.2f}% over baseline")
    else:
        print("No CSV files found in the data directory.")
