import os
import pandas as pd

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


# extract the time feature  from the arrival time


if __name__ == "__main__":
    dfs, full_df = load_queue_datasets(PATH)

    if not full_df.empty:
        print("\n" + "=" * 60)
        print(f"Combined Dataset Shape: {full_df.shape}")
        print("=" * 60)
        print("Combined Dataset Column Types:")
        print(full_df.dtypes)
        print("\nMissing Values per Column:")
        print(full_df.isnull().sum())
        print("\nSample Preview (First 3 rows):")
        print(full_df.head(3))
    else:
        print("No CSV files found in the data directory.")
