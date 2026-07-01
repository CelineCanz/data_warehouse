

# %%
import sys
sys.path.append(r"E:\Python\data_warehouse")

# %%
from prefect import flow, task
from config.sap_date import process_sap_datetime
from config.sql_server import write_df, create_table


from ingestion.sap.product.product_full_load import (
    extract_product,
    extract_product_description,
    extract_product_sales_delivery,
)

from ingestion.sap.billing.billing_full_load import (
    load_billing_header,
    load_billing_item,
)


# FONCTION Let's get the metadata out and prepare dates
def prepare_dataframe(df):

    df = process_sap_datetime(df)

    cols_to_drop = [

        col for col in df.columns

        if (
            "__metadata" in col
            or "__deferred" in col
        )

    ]

    df = df.drop(
        columns=cols_to_drop,
        errors="ignore"
    )

    return df

@task
def create_and_load(
    df,
    table_name
):

    create_table(
        df,
        table_name
    )

    write_df(
        df,
        table_name
    )


# PRODUCT
# %%
@task
def run_product():
    return prepare_dataframe(
        extract_product()
    )


@task
def run_product_desc():
    return prepare_dataframe(
        extract_product_description()
    )


@task
def run_product_sales_delivery():
    return prepare_dataframe(
        extract_product_sales_delivery()
    )

@task
def run_billing_header():
    return prepare_dataframe(
        load_billing_header()
    )

@task
def run_billing_item():
    return prepare_dataframe(
        load_billing_item()
    )


@flow(name="SAP Full Load")
def sap_flow():

    product = run_product()

    create_and_load(
        product,
        "DTL_SAP_Product"
    )

    product_description = run_product_desc()

    create_and_load(
        product_description,
        "DTL_SAP_Product_Description"
    )

    product_sales_delivery = run_product_sales_delivery()

    create_and_load(
        product_sales_delivery,
        "DTL_SAP_Product_Sales_Delivery"
    )

    
    billing_header = run_billing_header()

    create_and_load(
        billing_header,
        "DTL_SAP_BillingHeader"
    )

    billing_item = run_billing_item()

    create_and_load(
        billing_item,
        "DTL_SAP_BillingItem"
    )


@flow(name="SAP Full Load")
def sap_flow():
    
    billing_header = run_billing_header()

    create_and_load(
        billing_header,
        "DTL_SAP_BillingHeader"
    )

    billing_item = run_billing_item()

    create_and_load(
        billing_item,
        "DTL_SAP_BillingItem"
    )


# %%
if __name__ == "__main__":
    sap_flow()
