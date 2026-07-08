# -*- coding: utf-8 -*-
"""
Extract inbound deliveries from API_INBOUND_DELIVERY_SRV
"""

import pandas as pd

from config.sap_utils import (
    sap_session,
    CLIENT,
    WINDOW_SIZE,
    BASE
)

SERVICE = "API_INBOUND_DELIVERY_SRV"


def load_inbound_delivery() -> pd.DataFrame:
    """
    Full extraction of inbound delivery items.

    Useful ATP fields:

    - DeliveryDocument
    - DeliveryDocumentItem
    - Material
    - Plant
    - StorageLocation
    - ActualDeliveryQuantity
    - DeliveryQuantityUnit
    - ProductAvailabilityDate
    - GoodsMovementStatus
    """

    http = sap_session()

    entity = "A_InbDeliveryItem"

    rows_all = []
    last_delivery = None

    while True:

        params = {
            "sap-client": CLIENT,
            "$format": "json",
            "$top": WINDOW_SIZE,
            "$orderby": "DeliveryDocument"
        }

        if last_delivery:

            params["$filter"] = (
                f"DeliveryDocument gt '{last_delivery}'"
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

        rows_all.extend(batch)

        last_delivery = batch[-1]["DeliveryDocument"]

        print(
            f"→ InboundDelivery up to {last_delivery}"
        )

    df = pd.json_normalize(rows_all)

    return df