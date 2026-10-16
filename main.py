import os
import pandas as pd

PATH = "data"

# Store by filename: dfs["queue_data.csv"]
dfs = {}

# Store by index: dfs_list[0], dfs_list[1], etc.
dfs_list = []

for file in os.listdir(PATH):
    file_path = os.path.join(PATH, file)

    if file.endswith(".xlsx"):
        df = pd.read_excel(file_path)
        dfs[file] = df
        dfs_list.append(df)
        # print(f"Loaded Excel: {file} - Shape: {df.shape}")

    elif file.endswith(".csv"):
        df = pd.read_csv(file_path)
        dfs[file] = df
        dfs_list.append(df)
        # print(f"Loaded CSV: {file} - Shape: {df.shape}")


# print(dfs_list[0].columns)

for col in dfs_list[0].columns:
    print(col)
