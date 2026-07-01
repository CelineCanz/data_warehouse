import pandas as pd
import re

def process_sap_datetime(df):

    df = df.copy()

    for col in df.columns:

        sample = df[col].dropna().astype(str)

        if len(sample) == 0:
            continue

        if sample.str.startswith("/Date(").mean() > 0.8:

            print(f"Converting {col}")

            df[col] = pd.to_datetime(
                pd.to_numeric(
                    df[col]
                    .astype(str)
                    .str.extract(
                        r"/Date\((\d+)",
                        expand=False
                    ),
                    errors="coerce"
                ),
                unit="ms",
                errors="coerce"
            )

    return df