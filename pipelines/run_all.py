# -*- coding: utf-8 -*-
"""
Created on Mon May  4 11:31:39 2026

@author: ccanziani
"""

# run_all.py
# -*- coding: utf-8 -*-
# %%
import os
import pandas as pd
import re

# -------------------------------------------------
# WORKDIR
# -------------------------------------------------


import pipelines.autoexec

# -------------------------------------------------
# IMPORTS SAP
# -------------------------------------------------
# %%
from ingestion.sap.product.product_full_load import (
    extract_product,
    extract_product_description,
    extract_product_sales_delivery,
)
# %%
from extract.company import load_company_code_full
from extract.business_partners import load_business_partner
from extract.billing_header_item import (
    load_billing_header,
    load_billing_item,
    
)
from extract.customers import load_customer
from extract.material_stocks import (
    load_material_stock,
    load_material_stock_by_plant,
)
from extract.sales_org import load_sales_organization_full
from extract.profit_center import load_profit_center_full, load_profit_center_text

from extract.sales_header_item import (
    load_sales_order_header,
    load_sales_order_item,
    load_sales_order_schedule_line,
)

from extract.material_stocks import (
    load_material_stock,
    load_material_stock_by_plant,
)
# -------------------------------------------------
# DATE FUNCTION
# -------------------------------------------------

def process_sap_datetime(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def parse_sap_date(x):
        if pd.isna(x):
            return pd.NaT

        if isinstance(x, str) and "/Date" in x:
            match = re.search(r"\d+", x)
            if match:
                ts = int(match.group())
                return pd.to_datetime(ts, unit="ms", errors="coerce")

        return pd.to_datetime(x, errors="coerce")

    date_cols = [c for c in df.columns if c.endswith("Date")]
    time_cols = [c for c in df.columns if c.endswith("Time")]

    for col in date_cols:
        df[col] = df[col].apply(parse_sap_date)

    for col in time_cols:
        df[col + "_td"] = pd.to_timedelta(
            df[col]
            .astype(str)
            .str.replace("PT", "", regex=False)
            .str.replace("H", ":", regex=False)
            .str.replace("M", ":", regex=False)
            .str.replace("S", "", regex=False),
            errors="coerce"
        )

    for col in date_cols:
        time_col = col.replace("Date", "Time")
        if time_col in df.columns:
            df[col.replace("Date", "DateTime")] = (
                df[col] + df[time_col + "_td"]
            )

    return df


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    print("=== SAP → SQL RUN STARTED ===")
    # --------------------------------------------------
    # SALES ORDER
    # --------------------------------------------------

    print("Loading sales order header...")
    DTL_SAP_SalesOrder = load_sales_order_header()
    DTL_SAP_SalesOrder=process_sap_datetime(DTL_SAP_SalesOrder)
    print(f"Sales order header loaded: {DTL_SAP_SalesOrder.shape}")

    print("Loading sales order item...")
    DTL_SAP_SalesItem = load_sales_order_item()
    DTL_SAP_SalesItem=process_sap_datetime(DTL_SAP_SalesItem)
    print(f"Sales order item loaded: {DTL_SAP_SalesItem.shape}")

   
    print("Loading sales order schedule line...")
    DTL_SAP_SalesSchedule = load_sales_order_schedule_line()
    DTL_SAP_SalesSchedule=process_sap_datetime(DTL_SAP_SalesSchedule)
    print(f"Sales order schedule line loaded: {DTL_SAP_SalesSchedule.shape}")
    
    # ---------------- PRODUCTS ----------------
    print("Loading PRODUCTS...")
    DTL_SAP_Product = extract_product()
    #write_df_to_sql(df, "DTL_SAP_Product", key_columns=["Product"])

    DTL_SAP_ProductDescription = extract_product_description()
    #write_df_to_sql(df, "DTL_SAP_ProductDescription", key_columns=["Product"])

    DTL_SAP_ProductSalesDelivery = extract_product_sales_delivery()
    #write_df_to_sql(df, "DTL_SAP_ProductSalesDelivery", key_columns=["Product"])

    # ---------------- COMPANY ----------------
    print("Loading COMPANY CODES...")
    DTL_SAP_Company = load_company_code_full()
    #write_df_to_sql(df, "DTL_SAP_Company", key_columns=["CompanyCode"])

    # ---------------- BUSINESS PARTNERS -----
    print("Loading BUSINESS PARTNERS...")
    DTL_SAP_BusinessPartner = load_business_partner()
    #write_df_to_sql(df, "DTL_SAP_BusinessPartner", key_columns=["BusinessPartner"])

    # ---------------- BILLING ----------------
    print("Loading BILLING HEADER...")
    DTL_SAP_BillingHeader = load_billing_header()
    DTL_SAP_BillingHeader=process_sap_datetime(DTL_SAP_BillingHeader)

    print("Loading BILLING ITEM...")
    DTL_SAP_BillingItem = load_billing_item()
    DTL_SAP_BillingItem=process_sap_datetime(DTL_SAP_BillingItem)

    
    # ---------------- CUSTOMERS --------------
    print("Loading CUSTOMERS...")
    DTL_SAP_Customer = load_customer()
    #write_df_to_sql(df, "DTL_SAP_Customer", key_columns=["Customer"])

    # ---------------- STOCKS ------------------
    print("Loading MATERIAL STOCK...")
    DTL_SAP_MaterialStock = load_material_stock()
    #write_df_to_sql(df, "DTL_SAP_MaterialStock", key_columns=["Material"])
    plants = ["7500", "7501", "7502", "750B", "7510", "7520", "7522", "7530", "7535", "7550", "7555", "7570", "7575" ]  # à adapter avec tes vrais plant
    print("Loading MATERIAL STOCK BY PLANT...")
    DTL_SAP_MaterialStockPlant = load_material_stock_by_plant(plants)
    #write_df_to_sql(
    #    df,
    #    "DTL_SAP_MaterialStockPlant",
    #    key_columns=["Material", "Plant"],
    #)

    # ---------------- SALES ORG ----------------
    #print("Loading SALES ORGANIZATION...")
    #DTL_SAP_SalesOrg = load_sales_organization_full()
    #write_df_to_sql(df, "DTL_SAP_SalesOrg", key_columns=["SalesOrganization"])


    
    # ------------------ PROFIT CENTER ----------
    print("Loading PROFIT CENTERS...")
    DTL_SAP_ProfitCenter=load_profit_center_full()

    print("Loading PROFIT CENTER TEXTS...")
    DTL_SAP_ProfitCenterText=load_profit_center_text()
    
    print("Merging both Profit Center tables")
    DTL_SAP_ProfitCenter = DTL_SAP_ProfitCenter.merge(
        DTL_SAP_ProfitCenterText[
            ["ProfitCenter", "ProfitCenterName", "ProfitCenterLongName"]
        ],
        on="ProfitCenter",
        how="left"
    )
    
    print("There are", DTL_SAP_ProfitCenter["ProfitCenter"].nunique(), "distinct ProfitCenters")
    print("There are", len(DTL_SAP_ProfitCenter), "total rows in the data set (show be the same as above)")


    # ✅ RETOUR DES TABLES
    return {
        "DTL_SAP_Product": DTL_SAP_Product,
        "DTL_SAP_ProductDescription": DTL_SAP_ProductDescription,
        "DTL_SAP_ProductSalesDelivery": DTL_SAP_ProductSalesDelivery,
        "DTL_SAP_Company": DTL_SAP_Company,
        "DTL_SAP_BusinessPartner": DTL_SAP_BusinessPartner,
        "DTL_SAP_BillingHeader": DTL_SAP_BillingHeader,
        "DTL_SAP_BillingItem": DTL_SAP_BillingItem,
        "DTL_SAP_Customer": DTL_SAP_Customer,
        "DTL_SAP_ProfitCenter" : DTL_SAP_ProfitCenter,
        "DTL_SAP_ProfitCenterText" : DTL_SAP_ProfitCenterText,
        "DTL_SAP_SalesOrder" : DTL_SAP_SalesOrder,
        "DTL_SAP_SalesItem" : DTL_SAP_SalesItem,
        "DTL_SAP_SalesSchedule" : DTL_SAP_SalesSchedule,
        "DTL_SAP_MaterialStock": DTL_SAP_MaterialStock,
        "DTL_SAP_MaterialStockPlant": DTL_SAP_MaterialStockPlant,
        #"DTL_SAP_SalesOrg": DTL_SAP_SalesOrg,
    }




    
if __name__ == "__main__":
    tables = main()



# 🔽 DÉBALLAGE EXPLICITE POUR SPYDER
DTL_SAP_Product = tables["DTL_SAP_Product"]
DTL_SAP_ProductDescription = tables["DTL_SAP_ProductDescription"]
DTL_SAP_ProductSalesDelivery = tables["DTL_SAP_ProductSalesDelivery"]
DTL_SAP_Company = tables["DTL_SAP_Company"]
DTL_SAP_BusinessPartner = tables["DTL_SAP_BusinessPartner"]
DTL_SAP_BillingHeader = tables["DTL_SAP_BillingHeader"]
DTL_SAP_BillingItem = tables["DTL_SAP_BillingItem"]
DTL_SAP_Customer = tables["DTL_SAP_Customer"]
DTL_SAP_ProfitCenter = tables["DTL_SAP_ProfitCenter"]
DTL_SAP_ProfitCenterText = tables["DTL_SAP_ProfitCenterText"]
DTL_SAP_SalesOrder = tables["DTL_SAP_SalesOrder"]
DTL_SAP_SalesItem = tables["DTL_SAP_SalesItem"]
DTL_SAP_SalesSchedule = tables["DTL_SAP_SalesSchedule"]
DTL_SAP_MaterialStock = tables["DTL_SAP_MaterialStock"],
DTL_SAP_MaterialStockPlant = tables["DTL_SAP_MaterialStockPlant"]

drop_billingItem = [
"SalesDocumentItemType",
"ReturnItemProcessingType",
"CreatedByUser",
"ReferenceLogicalSystem",
"SalesOffice",
"Batch",
#"AdditionalMaterialGroup3",
#"AdditionalMaterialGroup4",
#"AdditionalMaterialGroup5",
"MaterialCommissionGroup",
"ReplacementPartType",
"MaterialGroupHierarchy1",
"MaterialGroupHierarchy2",
"PlantCounty",
"PlantCity",
"BOMExplosion",
"MaterialDeterminationType",
"ItemGrossWeight",
"ItemNetWeight",
"ItemWeightUnit",
"ItemVolume",
"ItemVolumeUnit",
"BillingPlanRule",
"BillingPlan",
"BillingPlanItem",
"Subtotal4Amount",
"Subtotal5Amount",
"Subtotal6Amount",
"StatisticalValueControl",
"CustomerConditionGroup1",
"CustomerConditionGroup2",
"CustomerConditionGroup3",
"CustomerConditionGroup4",
"CustomerConditionGroup5",
"AbsltStatisticsExchangeRate",
"StatisticsExchRateIsIndrctQtan",
"MainItemPricingRefMaterial",
"MainItemMaterialPricingGroup",
"TaxJurisdiction",
"ProductTaxClassification3",
"ProductTaxClassification4",
"ProductTaxClassification5",
"ProductTaxClassification6",
"ProductTaxClassification7",
"ProductTaxClassification8",
"ProductTaxClassification9",
"ZeroVATRsn",
"WBSElement",
"OrderID",
"CostCenter",
"SalesGroup",
#"AdditionalCustomerGroup3",
#"AdditionalCustomerGroup4",
#"AdditionalCustomerGroup5",
"RetailPromotion",
"VolumeRebateGroup",
"SalesOrderCustomerPriceGroup",
"SalesOrderPriceListType",
"HigherLevelItemUsage",
"__metadata.id",
"__metadata.uri",
"__metadata.type",
"to_BillingDocument.__deferred.uri",
"to_ItemText.__deferred.uri",
"to_Partner.__deferred.uri",
"to_PricingElement.__deferred.uri"
]


DTL_SAP_BillingItem = DTL_SAP_BillingItem.drop(columns=drop_billingItem, errors="ignore")



drop_BillingHeader = [
"ForeignTrade",
"IsExportDelivery",
"IncotermsLocation2",
"ContractAccount",
"PaymentMethod",
"AdditionalValueDays",
"SEPAMandate",
"ExchangeRateDate",
"ExchangeRateType",
"DunningArea",
"DunningBlockingReason",
"DunningKey",
"InternalFinancialDocument",
"IsRelevantForAccrual",
"PartnerCompany",
"PurchaseOrderByCustomer",
"CityCode",
"County",
"CustomerRebateAgreement",
"BillingIssueType",
"InvoiceListStatus",
"OvrlItmGeneralIncompletionSts",
"CustomerTaxClassification3",
"CustomerTaxClassification4",
"CustomerTaxClassification5",
"CustomerTaxClassification6",
"CustomerTaxClassification7",
"CustomerTaxClassification8",
"CustomerTaxClassification9",
"__metadata.id",
"__metadata.uri",
"__metadata.type",
"__metadata.etag",
"to_Item.__deferred.uri",
"to_Partner.__deferred.uri",
"to_PricingElement.__deferred.uri",
"to_Text.__deferred.uri"
]


DTL_SAP_BillingHeader = DTL_SAP_BillingHeader.drop(columns=drop_BillingHeader, errors="ignore")


