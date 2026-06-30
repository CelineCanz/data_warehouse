import requests
import pandas as pd
from requests.auth import HTTPBasicAuth

from config.sap_utils import HOST, CLIENT, USER, PASSWORD, WINDOW_SIZE, BASE


def fetch_product_entity_incremental(entity: str, select_cols: list, last_run: str) -> pd.DataFrame:
    SERVICE = "API_PRODUCT_SRV"

    http = requests.Session()
    http.auth = HTTPBasicAuth(USER, PASSWORD)
    http.headers.update({"Accept": "application/json"})

    if "Product" not in select_cols:
        select_cols = select_cols + ["Product"]

    select_str = ",".join(select_cols)

    rows = []
    last_product = None

    while True:
        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$select": select_str,
            "$filter": f"LastChangeDateTime gt datetime'{last_run}'"
        }

        if last_product:
            params["$filter"] += f" and Product gt '{last_product}'"

        r = http.get(
            f"{BASE}/{SERVICE}/{entity}",
            params=params,
            timeout=60
        )
        r.raise_for_status()

        batch = r.json()["d"]["results"]
        if not batch:
            break

        rows.extend(batch)
        last_product = batch[-1]["Product"]

    return pd.json_normalize(rows)


def extract_product_incremental(last_run: str) -> pd.DataFrame:
    return fetch_product_entity_incremental(
        "A_Product",
        [
            "Product",
            "ProductType",
            "CreationDate",
            "ProductHierarchy",
            "CreatedByUser",
            "LastChangeDate",
            "LastChangedByUser",
            "LastChangeDateTime",
            "IsMarkedForDeletion",
            "ProductOldID",
            "ProductGroup",
            "BaseUnit",
            "ItemCategoryGroup",
            "Division",
            "VolumeUnit",
            "MaterialVolume",
            "ANPCode",
            "ExternalProductGroup",
            "AuthorizationGroup"
        ],
        last_run
    )


''' NOT USED BECAUSE NO TIME STAMP IN THESE TABLES
def extract_product_description_incremental(last_run: str) -> pd.DataFrame:
    return fetch_product_entity_incremental(
        "A_ProductDescription",
        [
            "Product",
            "Language",
            "ProductDescription"
        ],
        last_run
    )


def extract_product_sales_delivery_incremental(last_run: str) -> pd.DataFrame:
    return fetch_product_entity_incremental(
        "A_ProductSalesDelivery",
        [
            "Product",
            "ProductSalesOrg",
            "ProductDistributionChnl",
            "MinimumOrderQuantity",
            "AccountDetnProductGroup",
            "DeliveryNoteProcMinDelivQty",
            "ItemCategoryGroup",
            "ProductHierarchy",
            "FirstSalesSpecProductGroup",
            "SecondSalesSpecProductGroup",
            "CashDiscountIsDeductible"
        ],
        last_run
    )

'''