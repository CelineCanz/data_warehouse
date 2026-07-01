from sqlalchemy import (
    String,
    Float,
    BigInteger,
    DateTime,
    Boolean,
)

import pandas as pd

def infer_sql_types(df):

    dtype_mapping = {}

    for col in df.columns:

        dtype = df[col].dtype

        if pd.api.types.is_datetime64_any_dtype(dtype):

            dtype_mapping[col] = DateTime()

        elif pd.api.types.is_bool_dtype(dtype):

            dtype_mapping[col] = Boolean()

        elif pd.api.types.is_integer_dtype(dtype):

            dtype_mapping[col] = BigInteger()

        elif pd.api.types.is_float_dtype(dtype):

            dtype_mapping[col] = Float()

        else:

            # Longueur max réelle de la colonne
            max_len = (
                df[col]
                .dropna()
                .astype(str)
                .str.len()
                .max()
            )

            if pd.isna(max_len):
                max_len = 50

            max_len = int(max_len)

            # Marge de sécurité
            max_len += 20

            # Taille minimale cohérente
            max_len = max(50, max_len)

            # Colonnes très longues -> VARCHAR(MAX)
            if max_len > 1000:

                dtype_mapping[col] = String(None)

                print(
                    f"{col:<40} VARCHAR(MAX)"
                )

            else:

                dtype_mapping[col] = String(max_len)

                print(
                    f"{col:<40} VARCHAR({max_len})"
                )

    return dtype_mapping
