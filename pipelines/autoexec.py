# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 14:37:36 2024

@author: ccanziani
"""

import os
import pandas as pd
import numpy as np
import json
import ast
import requests
from urllib.parse import unquote
from urllib.parse import quote
import traceback
import datetime
import csv
import pyodbc
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, inspect
from urllib.parse import urlparse, parse_qs
import parse
# needed to script all programs
import glob
import re
import matplotlib.pyplot as plt
import sqlalchemy


""" ------------------------------SQL CONNECTION ---------------------------"""

# Definition of the connection string
conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=dereldb03.ymce.local\YME_Warehouse;'
    r'DATABASE=D2C_Datawarehouse;'
    r'UID=SA-DEREL-D2C-JOBS;'
    r'PWD=#LAlGRAnJsejtvfUWQPKxMKe5t1gYiGuXb$#9oKE;'
)


# Try to establish a connection - error message if no connection
try:
    with pyodbc.connect(conn_str) as conn:
        print("Connection successful!")
except pyodbc.Error as ex:
    print("Could not establish connection: ", ex)


# Create SQLAlchemy engine
engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}', use_setinputsizes=False)
# Establish a connection
conn = pyodbc.connect(conn_str)
# Create a cursor
cursor = conn.cursor()




""" -------------------------------- FUNCTIONS  ----------------------------"""
#check if columns are completely empty. If so, we drop them.
def empty_columns(df):
    df=df.replace('', np.nan)
    out=df.isna().all().reset_index(name='0')
    out=out.rename(columns={"index" : "col_name"})
    out_var=out["col_name"].loc[(out["0"]==True)].tolist()
    include_columns = list(df.columns[~df.columns.isin(out_var)])
    df=df[include_columns]
    df.reset_index(drop=True, inplace=True)
    return df


""" ------------------------------- TREASURE DATA  ---------------------------"""
path_csv="C:\\Users\\ccanziani\\OneDrive - YAMAHA Group\\YME BCX Digital\\General\\FY24-25\\TreasureData\\csv_data\\"


""" ------------------------------- DIM DATE  ---------------------------"""


# Définir la plage de dates
date_range = pd.date_range(start='2020-01-01', end='2040-12-31')

# Créer un DataFrame avec la plage de dates
date_dim = pd.DataFrame(date_range, columns=['date'])

# Ajouter des colonnes supplémentaires pour les attributs temporels
date_dim['date_short'] = date_dim['date'].dt.date
date_dim['year'] = date_dim['date'].dt.year
date_dim['quarter'] = date_dim['date'].dt.quarter
date_dim['month'] = date_dim['date'].dt.month
date_dim['day'] = date_dim['date'].dt.day
date_dim['day_of_week'] = date_dim['date'].dt.dayofweek
date_dim['week_of_year'] = date_dim['date'].dt.isocalendar().week
date_dim['day_name'] = date_dim['date'].dt.day_name()
date_dim['month_name'] = date_dim['date'].dt.month_name()
date_dim['is_weekend'] = np.where(date_dim['day_of_week'] >= 5, 1, 0)

# Calculer l'année fiscale
def calculate_fiscal_year(date):
    year = date.year
    if date.month >= 4:
        return year
    else:
        return year - 1

date_dim['fiscal_year'] = date_dim['date'].apply(calculate_fiscal_year)

date_dim.to_sql('DATE_DIM', con=engine, if_exists='replace', index=False)



""" ------------------------------- WRITE SQL  ---------------------------"""

import subprocess
import tempfile

def write_df_to_sql_bcp(df, table_name, schema="dbo"):

    print(f"BCP load started for {table_name} ({len(df)} rows)")

    # sécurisation des données
    df = df.copy()
    df = df.fillna("")
    df = df.replace({"\n": " ", "\r": " "}, regex=True)

    # fichier temporaire
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    file_path = tmp.name
    tmp.close()

    # export CSV
    df.to_csv(
        file_path,
        index=False,
        sep="|",               # séparateur SAFE
        header=False,
        encoding="utf-8"
    )

    # commande BCP
    cmd = [
        "bcp",
        f"{table_name}",
        "in",
        file_path,
        "-S", "dereldb03.ymce.local\\YME_Warehouse",
        "-d", "D2C_Datawarehouse",
        "-U", "SA-DEREL-D2C-JOBS",
        "-P", "YOUR_PASSWORD",
        "-c",
        "-t", "|",
        "-b", "50000",
        "-h", "TABLOCK",
        "-C", "65001"
    ]

    subprocess.run(cmd, check=True)

    os.remove(file_path)

    print(f"✅ BCP load finished for {table_name}")



def write_df_bcp_chunked(df, table_name, chunk_size=300000):

    total = len(df)

    for i in range(0, total, chunk_size):
        chunk = df.iloc[i:i+chunk_size]

        print(f"Chunk {i} → {i+len(chunk)} / {total}")

        write_df_to_sql_bcp(chunk, table_name)



from multiprocessing import Pool, cpu_count

def process_chunk(args):
    df_chunk, table_name, i, total = args
    print(f"Chunk {i} → {i+len(df_chunk)} / {total}")
    write_df_to_sql_bcp(df_chunk, table_name)


def write_df_bcp_parallel(df, table_name, chunk_size=300000, n_jobs=None):

    if n_jobs is None:
        n_jobs = max(cpu_count() - 1, 1)

    total = len(df)

    # Split chunks
    tasks = []
    for i in range(0, total, chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        tasks.append((chunk, table_name, i, total))

    print(f"Launching {len(tasks)} chunks with {n_jobs} workers")

    with Pool(n_jobs) as pool:
        pool.map(process_chunk, tasks)

    print("✅ All chunks loaded!")