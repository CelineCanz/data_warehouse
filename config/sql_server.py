'''---------------------------------------------------------------------------------
                                SQL CONFIG
---------------------------------------------------------------------------------'''

import os

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
engine = create_engine(f'mssql+pyodbc:///?odbc_connect={conn_str}', use_setinputsizes=False)
# Establish a connection
conn = pyodbc.connect(conn_str)
# Create a cursor
cursor = conn.cursor()

# Get a list of all tables
#tables = cursor.tables(tableType='TABLE')

# Print all table names
#for table in tables:
#    print(table.table_name)
