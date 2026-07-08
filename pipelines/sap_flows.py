

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

from ingestion.sap.inbounds.inbouds_full_load import (
    load_inbound_delivery,
)

from ingestion.sap.purchase.purchase_order_full_load import (
    load_purchase_order_item,
    load_purchase_order_schedule_line,
)

import importlib

import ingestion.sap.sales.sales_full_load as sales_full_load

importlib.reload(sales_full_load)


from ingestion.sap.sales.sales_full_load import (
    load_sales_order_header,
    load_sales_order_item,
    load_sales_order_schedule_line,
)


from ingestion.sap.material.material_stocks_full_load import (
    load_material_stock,
    load_material_stock_by_plant,
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


@task
def run_sales_order():

    return prepare_dataframe(
        load_sales_order_header()
    )

@task
def run_sales_order_item():

    return prepare_dataframe(
        load_sales_order_item()
    )

@task
def run_sales_order_schedule_line():

    return prepare_dataframe(
        load_sales_order_schedule_line()
    )


@task
def run_material_stock_by_plant():
    plants = ["7500", "7501", "7502", "750B", "7510", "7520", "7522", "7530", "7535", "7550", "7555", "7570", "7575" ]
    return prepare_dataframe(
        load_material_stock_by_plant(plants)
    )

@task
def run_material_stock():

    return prepare_dataframe(
        load_material_stock()
    )

@task
def run_inbounds_delivery():

    return prepare_dataframe(
        load_inbound_delivery()
    )


@task
def run_purchase_order():

    return prepare_dataframe(
        load_purchase_order_item()
    )


@task
def run_purchase_order_schedule_line():

    return prepare_dataframe(
        load_purchase_order_schedule_line()
    )

# %%
@flow(name="SAP Full Load")
def sap_flow():

    product = run_product()

    create_and_load(
        product,
        "STG_Product"
    )

    product_description = run_product_desc()

    create_and_load(
        product_description,
        "STG_ProductDescription"
    )

    product_sales_delivery = run_product_sales_delivery()

    create_and_load(
        product_sales_delivery,
        "STG_ProductSalesDelivery"
    )

    
    billing_header = run_billing_header()

    create_and_load(
        billing_header,
        "STG_BillingHeader"
    )

    billing_item = run_billing_item()

    create_and_load(
        billing_item,
        "STG_BillingItem"
    )

    sales_header = run_sales_order()

    create_and_load(
        sales_header,
        "STG_SalesOrder"
    )

    sales_item = run_sales_order_item()

    create_and_load(
        sales_item,
        "STG_SalesOrderItem"
    )

    sales_schedule = run_sales_order_schedule_line()

    create_and_load(
        sales_schedule,
        "STG_SalesOrderScheduleLine"
    )

    material_stock = run_material_stock()

    create_and_load(
        material_stock,
        "STG_MaterialStock"
    )

    material_stock_plant = run_material_stock_by_plant()

    create_and_load(
        material_stock_plant,
        "STG_MaterialStockPlant"
    )

    inbounds_delivery = run_inbounds_delivery()

    create_and_load(
        inbounds_delivery,
        "STG_InboundDelivery"
    )


# %%
@flow(name="SAP Full Load")
def sap_flow():
    purchase_order_item = run_purchase_order()

    create_and_load(
        purchase_order_item,
        "STG_PurchaseOrder"
    )

    purchase_order_item_schedule_line = run_purchase_order_schedule_line()

    create_and_load(
        purchase_order_item_schedule_line,
        "STG_PurchaseOrderScheduleLine"
    )

# %%
if __name__ == "__main__":
    sap_flow()

# %%
