# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 11:16:33 2026

@author: ccanziani
"""

from prefect import flow, task

# Import your existing function
from ingestion.sap.product.product_full_load import extract_product


@task
def run_product():
    print("Running product extraction...")
    df = extract_product()
    print(f"Rows loaded: {df.shape}")
    return df


@flow
def product_flow():
    print("=== START PRODUCT FLOW ===")
    df = run_product()
    print("=== END PRODUCT FLOW ===")
    return df


if __name__ == "__main__":
    DTL_SAP_Product=product_flow()