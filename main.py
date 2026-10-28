import os
import pandas as pd

PATH = "data"

# Store by filename: dfs["queue_data.csv"]
dfs = {}

# Store by index: dfs_list[0], dfs_list[1], etc.
dfs_list = []

for file in sorted(os.listdir(PATH)):
    file_path = os.path.join(PATH, file)

    # Optional Excel support if needed in the future
    # if file.endswith(".xlsx"):
    #     df = pd.read_excel(file_path)
    #     dfs[file] = df
    #     dfs_list.append(df)
    #     print(f"Loaded Excel: {file} - Shape: {df.shape}")

    if file.endswith(".csv"):
        df = pd.read_csv(file_path)

        # 1. Standardize column names across datasets
        df = df.rename(
            columns={
                "arrival": "arrival_time",
                "start": "start_time",
                "end": "finish_time",  # aligns with queue_data and verified_queue datasets
                "wait_min": "wait_time",
            }
        )

        # 2. Parse timestamp columns to datetime
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

        # 3. Ensure a consistent date column across all records
        if "arrival_time" in df.columns:
            df["date"] = df["arrival_time"].dt.date

        # 4. Track origin dataset for provenance
        df["source_file"] = file

        dfs[file] = df
        dfs_list.append(df)
        print(f"Loaded CSV: {file:40s} | Shape: {str(df.shape):12s} | Columns: {list(df.columns)}")

# 5. Combine all loaded CSVs into one unified DataFrame (executed after all files are loaded)
if dfs_list:
    full_df = pd.concat(dfs_list, ignore_index=True)
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
