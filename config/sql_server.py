'''---------------------------------------------------------------------------------
                                SQL CONFIG
---------------------------------------------------------------------------------'''
# %%
import sys
print(sys.executable)
import pandas as pd
import numpy as np
import requests
import pyodbc
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, inspect, BigInteger, DateTime, Boolean
import parse

import matplotlib.pyplot as plt
import subprocess
import uuid
from pathlib import Path

from config.sap_sql_types import infer_sql_types

SQL_SERVER = "dereldb03.ymce.local\\YME_Warehouse"
SQL_DATABASE = "D2C_Datawarehouse"
SQL_USER = "SA-DEREL-D2C-JOBS"
SQL_PASSWORD = "#LAlGRAnJsejtvfUWQPKxMKe5t1gYiGuXb$#9oKE;"

conn_str = (
    f"DRIVER={{SQL Server}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USER};"
    f"PWD={SQL_PASSWORD};"
)



# Try to establish a connection - error message if no connection
try:
    with pyodbc.connect(conn_str) as conn:
        print("Connection successful!")
except pyodbc.Error as ex:
    print("Could not establish connection: ", ex)


# Create SQLAlchemy engine
#engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}', use_setinputsizes=False)

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={conn_str}",
    fast_executemany=True,
    use_setinputsizes=False,
)
# Establish a connection
conn = pyodbc.connect(conn_str)
# Create a cursor
cursor = conn.cursor()

# Get a list of all tables
#tables = cursor.tables(tableType='TABLE')

# Print all table names
#for table in tables:
#    print(table.table_name)



# %%
def infer_sql_types(df):

    dtype_mapping = {}

    for col in df.columns:

        dtype = df[col].dtype

        if pd.api.types.is_datetime64_any_dtype(dtype):

            dtype_mapping[col] = DateTime()

        elif pd.api.types.is_integer_dtype(dtype):

            dtype_mapping[col] = BigInteger()

        elif pd.api.types.is_float_dtype(dtype):

            dtype_mapping[col] = Float()

        elif pd.api.types.is_bool_dtype(dtype):

            dtype_mapping[col] = Boolean()

        else:

            col_lower = col.lower()

            if any(
                x in col_lower
                for x in [
                    "description",
                    "name",
                    "text",
                    "longname",
                ]
            ):

                dtype_mapping[col] = String(1000)

            else:

                dtype_mapping[col] = String(100)

    return dtype_mapping




def create_table(df, table_name):

    print(f"\nCreating table {table_name}")

    dtype_mapping = infer_sql_types(df)

    df.head(0).to_sql(
        name=table_name,
        con=engine,
        schema="sap",
        if_exists="replace",
        index=False,
        dtype=dtype_mapping,
    )

    print(f"✅ Table {table_name} créée")


def write_df(
    df: pd.DataFrame,
    table_name: str,
    chunk_size: int = 100_000,
):

    total = len(df)

    for start in range(0, total, chunk_size):

        end = min(start + chunk_size, total)

        chunk = df.iloc[start:end]

        chunk.to_sql(
            name=table_name,
            con=engine,
            schema="sap",
            if_exists="append",
            index=False,
            method=None
        )

        print(
            f"{end:,}/{total:,} rows loaded into {table_name}"
        )

    print(f"✅ {table_name} fully loaded")




def write_df_bcp(
    df: pd.DataFrame,
    table_name: str,
):

    temp_file = Path(
        f"temp_{uuid.uuid4().hex}.csv"
    )

    df.to_csv(
        temp_file,
        index=False,
        sep="|",
        encoding="utf-8",
    )
    cmd = [
        "bcp",
        f"{SQL_DATABASE}.sap.{table_name}",
        "in",
        str(temp_file),
        "-S", SQL_SERVER,
        "-T",
        "-c",
        "-t", "|",
        "-F", "2",
    ]

    subprocess.run(
        cmd,
        check=True
    )

    temp_file.unlink()

    print(
        f"{len(df):,} rows loaded into {table_name}"
    )