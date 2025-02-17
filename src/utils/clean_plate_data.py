import pandas as pd


def clean_dataset(file_path: str):
    df = pd.read_csv(file_path)

    df_filtered = df[df['PLATE'].str.len() > 3]

    print('output count', len(df_filtered))
    df_filtered.to_csv(file_path)


