# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:53:07 2026

@author: ccanziani
"""
import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
from config.sap_utils import HOST, CLIENT, USER, PASSWORD, WINDOW_SIZE, BASE


def fetch_product_entity(entity: str, select_cols: list) -> pd.DataFrame:
    SERVICE = "API_PRODUCT_SRV"

    http = requests.Session()
    http.auth = HTTPBasicAuth(USER, PASSWORD)
    http.headers.update({"Accept": "application/json"})

    # ✅ ensure Product is always present
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
            "$select": select_str
        }

        if last_product:
            params["$filter"] = f"Product gt '{last_product}'"

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








def extract_product() -> pd.DataFrame:
    return fetch_product_entity("A_Product", [
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
])



def extract_product_description() -> pd.DataFrame:
    return fetch_product_entity("A_ProductDescription", [
        "Product",
        "Language",
        "ProductDescription"
    ])


def extract_product_sales_delivery() -> pd.DataFrame:
    return fetch_product_entity("A_ProductSalesDelivery", [
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
    ])