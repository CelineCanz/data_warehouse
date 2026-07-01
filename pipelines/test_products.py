
# %%
import sys
sys.path.append(r"E:\Python\data_warehouse")

# %%
from prefect import flow, task

# %%

from ingestion.sap.product.product_full_load import extract_product

from ingestion.sap.billing.billing_full_load import (
    load_billing_header,
    load_billing_item,
)



# PRODUCT

@task
def run_product():
    print("Running product extraction...")
    df = extract_product()
    print(f"Rows loaded: {df.shape}")
    return df


# BILLING HEADER

@task
def run_billing_header():
    print("Running billing header extraction...")
    df = load_billing_header()
    print(f"Rows loaded: {df.shape}")
    return df


# BILLING ITEM

@task
def run_billing_item():
    print("Running billing item extraction...")
    df = load_billing_item()
    print(f"Rows loaded: {df.shape}")
    return df





@flow(name="SAP Full Load")
def sap_flow():

    product = run_product()

    billing_header = run_billing_header()

    billing_item = run_billing_item()

    return {
        "DTL_SAP_Product": product,
        "DTL_SAP_BillingHeader": billing_header,
        "DTL_SAP_BillingItem": billing_item,
    }




if __name__ == "__main__":

    tables = sap_flow()

    DTL_SAP_Product = tables["DTL_SAP_Product"]
    DTL_SAP_BillingHeader = tables["DTL_SAP_BillingHeader"]
    DTL_SAP_BillingItem = tables["DTL_SAP_BillingItem"]
