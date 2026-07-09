# sales_full_load.py

import pandas as pd

from config.sap_utils import (
    sap_session,
    BASE,
    CLIENT,
    WINDOW_SIZE
)

SERVICE = "API_SALES_ORDER_SRV"

def load_sales_order_header() -> pd.DataFrame:
    """
    Load Sales Order headers from SAP using keyset pagination on SalesOrder.

    Business filter:
    - SalesOrganization between 7500 and 7599
    """

    http = sap_session()
    entity = "A_SalesOrder"

    rows = []
    last_doc = None

    while True:
        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "SalesOrder"
        }

        if last_doc:
            params["$filter"] = (
                f"SalesOrder gt '{last_doc}' "
                "and SalesOrganization ge '7500' "
                "and SalesOrganization lt '7600'"
            )
        else:
            params["$filter"] = (
                "SalesOrganization ge '7500' "
                "and SalesOrganization lt '7600'"
            )

        r = http.get(
            f"{BASE}/{SERVICE}/{entity}",
            params=params,
            timeout=120,
        )
        r.raise_for_status()

        batch = r.json().get("d", {}).get("results", [])
        if not batch:
            break

        rows.extend(batch)
        last_doc = batch[-1]["SalesOrder"]

        print(f"→ SalesOrderHeader up to {last_doc}")

    df = pd.json_normalize(rows)

    return df


# --------------------------------------------------
# SALES ORDER ITEM
# --------------------------------------------------

def load_sales_order_item() -> pd.DataFrame:
    """
    Load Sales Order items from SAP using pagination on SalesOrder.

    IMPORTANT:
    Do not paginate on SalesOrderItem only.
    SalesOrderItem is not globally unique and usually repeats:
    10, 20, 30, etc.

    Here we use SalesOrder as the pagination key, same logic as billing items.
    Business filtering should ideally be done outside, after joining with header,
    because SalesOrganization may not always be available/reliable on item entity
    depending on the SAP metadata.
    """

    http = sap_session()
    entity = "A_SalesOrderItem"

    rows = []
    last_doc = None

    while True:
        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "SalesOrder"
        }

        # ✅ Pagination ONLY
        if last_doc:
            params["$filter"] = f"SalesOrder gt '{last_doc}'"

        r = http.get(
            f"{BASE}/{SERVICE}/{entity}",
            params=params,
            timeout=120,
        )
        r.raise_for_status()

        batch = r.json().get("d", {}).get("results", [])
        if not batch:
            break

        rows.extend(batch)
        last_doc = batch[-1]["SalesOrder"]

        print(f"→ SalesOrderItem up to {last_doc}")

    df = pd.json_normalize(rows)

    return df


# --------------------------------------------------
# SALES ORDER SCHEDULE LINE
# --------------------------------------------------

def load_sales_order_schedule_line() -> pd.DataFrame:
    """
    Load Sales Order schedule lines from SAP.

    Schedule lines are useful for availability because they usually contain:
    - requested quantities
    - confirmed quantities
    - delivery dates
    - open quantities

    Pagination is done on SalesOrder only.
    """

    http = sap_session()
    entity = "A_SalesOrderScheduleLine"

    rows = []
    last_doc = None

    while True:
        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "SalesOrder"
        }

        # ✅ Pagination ONLY
        if last_doc:
            params["$filter"] = f"SalesOrder gt '{last_doc}'"

        r = http.get(
            f"{BASE}/{SERVICE}/{entity}",
            params=params,
            timeout=120,
        )
        r.raise_for_status()

        batch = r.json().get("d", {}).get("results", [])
        if not batch:
            break

        rows.extend(batch)
        last_doc = batch[-1]["SalesOrder"]

        print(f"→ SalesOrderScheduleLine up to {last_doc}")

    df = pd.json_normalize(rows)

    return df