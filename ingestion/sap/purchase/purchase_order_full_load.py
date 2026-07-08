# %%
import pandas as pd

from config.sap_utils import (
    sap_session,
    CLIENT,
    WINDOW_SIZE,
    BASE
)


def load_purchase_order_item():

    http = sap_session()

    rows_all = []
    last_po = None

    while True:

        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "PurchaseOrder"
        }

        if last_po:
            params["$filter"] = (
                f"PurchaseOrder gt '{last_po}'"
            )

        r = http.get(
            f"{BASE}/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrderItem",
            params=params,
            timeout=180
        )

        r.raise_for_status()

        batch = r.json().get("d", {}).get("results", [])

        if not batch:
            break

        rows_all.extend(batch)

        last_po = batch[-1]["PurchaseOrder"]

        print(
            f"→ PO Item up to {last_po}"
        )

    return pd.json_normalize(rows_all)






def load_purchase_order_schedule_line():

    http = sap_session()

    rows_all = []
    last_po = None

    while True:

        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "PurchasingDocument"
        }

        if last_po:
            params["$filter"] = (
                f"PurchasingDocument gt '{last_po}'"
            )

        r = http.get(
            f"{BASE}/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrderScheduleLine",
            params=params,
            timeout=180
        )

        r.raise_for_status()

        batch = r.json().get("d", {}).get("results", [])

        if not batch:
            break

        rows_all.extend(batch)

        last_po = batch[-1]["PurchasingDocument"]

        print(
            f"→ PO Schedule up to {last_po}"
        )

    return pd.json_normalize(rows_all)