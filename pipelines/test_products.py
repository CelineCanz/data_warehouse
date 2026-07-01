
# %%
import sys
sys.path.append(r"E:\Python\data_warehouse")

# %%
from prefect import flow, task
from config.sql_server import create_table
from config.sap_date import process_sap_datetime
from config.sql_server import write_df_bcp

from ingestion.sap.product.product_full_load import extract_product

from ingestion.sap.billing.billing_full_load import (
    load_billing_header,
    load_billing_item,
)


# FONCTION Let's get the metadata out and prepare dates
def prepare_dataframe(df):

    df = process_sap_datetime(df)

    df = df.drop(
        columns=[
            "__metadata.id",
            "__metadata.uri",
            "__metadata.type"
        ],
        errors="ignore"
    )

    return df


# PRODUCT

# %%
@task
def run_product():

    df = prepare_dataframe(
        extract_product()
    )

    create_table(
        df,
        "DTL_SAP_Product"
    )

    return df

# BILLING HEADER

@task
def run_billing_header():
    print("Running billing header extraction...")
    df = load_billing_header()
    df = process_sap_datetime(df)
    print(f"Rows loaded: {df.shape}")
    return df


# BILLING ITEM

@task
def run_billing_item():
    print("Running billing item extraction...")
    df = load_billing_item()
    df = process_sap_datetime(df)
    print(f"Rows loaded: {df.shape}")
    return df




# %%
@flow(name="SAP Full Load")
def sap_flow():

    product = run_product()
    billing_header = run_billing_header()
    billing_item = run_billing_item()

    print(product.shape)
    print(billing_header.shape)
    print(billing_item.shape)





# %%
if __name__ == "__main__":
    sap_flow()




# %%
df = prepare_dataframe(extract_product())

create_table(
    df,
    "DTL_SAP_Product"
)

# %%
import importlib
import config.sql_server as sql_server

importlib.reload(sql_server)

from config.sql_server import write_df

df_test = df.head(1000)

write_df(
    df,
    table_name="DTL_SAP_Product"
)


