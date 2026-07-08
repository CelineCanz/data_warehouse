# -*- coding: utf-8 -*-
"""
Extract material stock from API_MATERIAL_STOCK_SRV
"""
import requests
import pandas as pd
from requests.auth import HTTPBasicAuth

from config.sap_utils import (
    sap_session,
    BASE,
    CLIENT,
    WINDOW_SIZE
)

SERVICE = "API_MATERIAL_STOCK_SRV"


# ============================================================
# Full Material Stock extraction - Account Model
# ============================================================

def load_material_stock() -> pd.DataFrame:
    """
    Extract full material stock data from SAP.

    Recommended entity for availability:
    - A_MatlStkInAcctMod

    Expected useful fields:
    - Material
    - Plant
    - StorageLocation
    - InventoryStockType
    - InventorySpecialStockType
    - MatlWrhsStkQtyInMatlBaseUnit
    - MaterialBaseUnit
    """

    http = sap_session()
    entity = "A_MatlStkInAcctMod"

    rows_all = []
    last_material = None

    while True:
        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "Material"
        }

        if last_material:
            params["$filter"] = f"Material gt '{last_material}'"

        r = http.get(
            f"{BASE}/{SERVICE}/{entity}",
            params=params,
            timeout=180
        )
        r.raise_for_status()

        batch = r.json().get("d", {}).get("results", [])
        if not batch:
            break

        rows_all.extend(batch)
        last_material = batch[-1]["Material"]

        print(f"→ MaterialStock up to {last_material}")

    df = pd.json_normalize(rows_all)

    return df


# ============================================================
# Material Stock by Plant
# ============================================================

def load_material_stock_by_plant(plants) -> pd.DataFrame:
    """
    SAP-safe stock extraction:
    - Loop by Plant
    - Avoid massive global requests
    - Uses A_MatlStkInAcctMod for availability quantities
    """

    http = sap_session()
    entity = "A_MatlStkInAcctMod"

    all_rows = []

    for plant in plants:
        print(f"📦 Loading stock for Plant {plant}")

        last_material = None

        while True:
            params = {
                "sap-client": CLIENT,
                "$format": "json",
                "$top": 2000,
                "$orderby": "Material",
                "$filter": f"Plant eq '{plant}'"
            }

            if last_material:
                params["$filter"] = (
                    f"Plant eq '{plant}' "
                    f"and Material gt '{last_material}'"
                )

            r = http.get(
                f"{BASE}/{SERVICE}/{entity}",
                params=params,
                timeout=180
            )
            r.raise_for_status()

            batch = r.json().get("d", {}).get("results", [])
            if not batch:
                break

            all_rows.extend(batch)
            last_material = batch[-1]["Material"]

            print(f"→ Plant {plant} / Material up to {last_material}")

        print(f"✅ Done Plant {plant}")

    df = pd.json_normalize(all_rows)

    return df