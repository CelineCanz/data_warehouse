

import requests
import pandas as pd
from requests.auth import HTTPBasicAuth

from config.sap_utils import (
    sap_session,
    BASE,
    CLIENT,
    WINDOW_SIZE,
)


def load_billing_header() -> pd.DataFrame:

    SERVICE = "API_BILLING_DOCUMENT_SRV"

    http = sap_session()

    rows = []
    last_doc = None

    while True:

        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "BillingDocument"
        }

        filters = [
            "SalesOrganization ge '7500'",
            "SalesOrganization lt '7600'"
        ]

        if last_doc:
            filters.insert(
                0,
                f"BillingDocument gt '{last_doc}'"
            )

        params["$filter"] = " and ".join(filters)

        r = http.get(
            f"{BASE}/{SERVICE}/A_BillingDocument",
            params=params,
            timeout=120
        )

        r.raise_for_status()

        batch = r.json()["d"]["results"]

        if not batch:
            break

        rows.extend(batch)

        last_doc = batch[-1]["BillingDocument"]

        print(f"→ Header : {last_doc}")

    return pd.json_normalize(rows)






def load_billing_item() -> pd.DataFrame:

    SERVICE = "API_BILLING_DOCUMENT_SRV"

    http = sap_session()

    rows = []

    last_doc = None
    last_item = None

    while True:

        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "BillingDocument,BillingDocumentItem"
        }

        if last_doc:

            params["$filter"] = (
                f"(BillingDocument gt '{last_doc}') "
                f"or "
                f"(BillingDocument eq '{last_doc}' "
                f"and BillingDocumentItem gt '{last_item}')"
            )

        r = http.get(
            f"{BASE}/{SERVICE}/A_BillingDocumentItem",
            params=params,
            timeout=120
        )

        r.raise_for_status()

        batch = r.json()["d"]["results"]

        if not batch:
            break

        rows.extend(batch)

        last_doc = batch[-1]["BillingDocument"]
        last_item = batch[-1]["BillingDocumentItem"]

        print(
            f"→ Item : {last_doc}/{last_item}"
        )

    df = pd.json_normalize(rows)

    df = df.drop_duplicates(
        subset=[
            "BillingDocument",
            "BillingDocumentItem"
        ]
    )

    return df