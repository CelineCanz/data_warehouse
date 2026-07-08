{{ config(
    materialized='table'
) }}

with inventory as (

    select

        Material,
        Plant,
        StorageLocation,
        Supplier,
        Customer,
        MaterialBaseUnit,

        coalesce(
            InventoryStockType,
            'blank'
        ) as InventoryStockType,

        cast(
            MatlWrhsStkQtyInMatlBaseUnit
            as decimal(18,3)
        ) as Quantity

    from {{ source('sap', 'STG_MaterialStockPlant') }}

),

inventory_pivot as (

    select

        Material,
        Plant,
        StorageLocation,
        MaterialBaseUnit,

        sum(case when InventoryStockType = '01' then Quantity else 0 end)
            as ValuateFreeStock,

        sum(case when InventoryStockType = '02' then Quantity else 0 end)
            as StockInQualityInspection,

        sum(case when InventoryStockType = '04' then Quantity else 0 end)
            as InventoryStockType_04,

        sum(case when InventoryStockType = '05' then Quantity else 0 end)
            as InventoryStockType_05,

        sum(case when InventoryStockType = '06' then Quantity else 0 end)
            as InventoryStockType_06,

        sum(case when InventoryStockType = '07' then Quantity else 0 end)
            as BlockedStock,

        sum(case when InventoryStockType = '10' then Quantity else 0 end)
            as Inbound_ShippingQty,

        sum(case when InventoryStockType = 'blank' then Quantity else 0 end)
            as InventoryStockType_blank

    from inventory

    group by

        Material,
        Plant,
        StorageLocation,
        MaterialBaseUnit

)
,

sales_schedule as (

    select

        SalesOrder,
        SalesOrderItem,

        sum(cast(ScheduleLineOrderQuantity as decimal(18,3)))
            as ScheduleLineOrderQuantity,

        sum(cast(ConfdOrderQtyByMatlAvailCheck as decimal(18,3)))
            as ConfdOrderQtyByMatlAvailCheck,

        sum(cast(DeliveredQtyInOrderQtyUnit as decimal(18,3)))
            as DeliveredQtyInOrderQtyUnit,

        sum(cast(OpenConfdDelivQtyInOrdQtyUnit as decimal(18,3)))
            as OpenConfdDelivQtyInOrdQtyUnit

    from {{ source('sap', 'STG_SalesOrderScheduleLine') }}

    group by

        SalesOrder,
        SalesOrderItem

),

sales_item as (

    select

        SalesOrder,
        SalesOrderItem,
        Material,
        ProductionPlant as Plant,
        StorageLocation,
        cast(
            RequestedQuantity
            as decimal(18,3)
        ) as RequestedQuantity
        

    from {{ source('sap', 'STG_SalesOrderItem') }}

    where coalesce(
        ltrim(rtrim(SalesDocumentRjcnReason)),
        ''
    ) = ''

),

sales as (

    select

        i.Material,

        i.Plant,

        i.StorageLocation,

        sum(i.RequestedQuantity)
            as RequestedQuantity,

        sum(
            coalesce(
                s.ScheduleLineOrderQuantity,
                0
            )
        ) as ScheduleLineOrderQuantity,

        sum(
            coalesce(
                s.ConfdOrderQtyByMatlAvailCheck,
                0
            )
        ) as ConfdOrderQtyByMatlAvailCheck,

        sum(
            coalesce(
                s.DeliveredQtyInOrderQtyUnit,
                0
            )
        ) as DeliveredQtyInOrderQtyUnit,

        sum(
            coalesce(
                s.OpenConfdDelivQtyInOrdQtyUnit,
                0
            )
        ) as OpenConfdDelivQtyInOrdQtyUnit,

        count(*)
            as SalesOrderItemCount

    from sales_item i

    left join sales_schedule s

        on i.SalesOrder = s.SalesOrder
       and i.SalesOrderItem = s.SalesOrderItem

    group by

        i.Material,
        i.Plant,
        i.StorageLocation

),

product_desc as (

    select

        Product as Material,

        ProductDescription

    from {{ source('sap', 'STG_ProductDescription') }}

    where Language = 'EN'

),

product_group as (

    select distinct

        Product as Material,

        ProductGroup,

        ProductType

    from {{ source('sap', 'STG_Product') }}

),

product_sales_delivery as (

    select *

    from (

        select

            Product as Material,

            ProductHierarchy,

            FirstSalesSpecProductGroup,

            SecondSalesSpecProductGroup,

            row_number() over (
                partition by Product
                order by Product
            ) as rn

        from {{ source('sap', 'STG_ProductSalesDelivery') }}

    ) x

    where rn = 1

),

product_hierarchy as (

    select distinct

        ProductHierarchyLevel2Code,
        ProductHierarchyLevel2Name

    from {{ source('sap', 'MAP_ProductHierarchy') }}

),
inbound as (

    select

        DeliveryDocument,
        DeliveryDocumentItem,

        Material,
        Plant,

        coalesce(
            nullif(ltrim(rtrim(StorageLocation)), ''),
            '__BLANK__'
        ) as StorageLocation,

        cast(
            ActualDeliveryQuantity as decimal(18,3)
        ) as ActualDeliveryQuantity,

        ProductAvailabilityDate,

        GoodsMovementStatus,
        GoodsMovementType

    from {{ source('sap', 'STG_InboundDelivery') }}

),

purchase_order_item as (

    select

        PurchaseOrder,
        PurchaseOrderItem,

        Material,
        Plant,

        coalesce(
            nullif(ltrim(rtrim(StorageLocation)), ''),
            '__BLANK__'
        ) as StorageLocation,

        IsCompletelyDelivered,
        GoodsReceiptIsExpected

    from {{ source('sap', 'STG_PurchaseOrder') }}

),
purchase_order_schedule as (

    select

        PurchasingDocument,
        PurchasingDocumentItem,

        cast(
            ScheduleLineDeliveryDate as date
        ) as ScheduleLineDeliveryDate,

        cast(
            ScheduleLineOrderQuantity as decimal(18,3)
        ) as ScheduleLineOrderQuantity,

        cast(
            ScheduleLineCommittedQuantity as decimal(18,3)
        ) as ScheduleLineCommittedQuantity

    from {{ source('sap', 'STG_PurchaseOrderScheduleLine') }}

),
purchase_orders as (

    select

        i.Material,
        i.Plant,
        i.StorageLocation,

-- ATP Purchase Order logic:
-- Ordered Qty   : quantity expected from the supplier.
-- Committed Qty : quantity formally confirmed by the supplier.
-- ATP Qty       : confirmed quantity if available, otherwise ordered quantity.
-- The ATP quantity is used in availability calculations to represent the
-- most reliable future inbound stock estimate available in SAP.

    sum(s.ScheduleLineOrderQuantity) as PurchaseOrderQtyOrdered,

    sum(s.ScheduleLineCommittedQuantity) as PurchaseOrderQtyCommitted,

    sum(
        coalesce(
            nullif(
                s.ScheduleLineCommittedQuantity,
                0
            ),
            s.ScheduleLineOrderQuantity
        )
    ) as PurchaseOrderQtyATP


    from purchase_order_item i

    inner join purchase_order_schedule s

        on i.PurchaseOrder = s.PurchasingDocument
       and i.PurchaseOrderItem = s.PurchasingDocumentItem

    where

        i.IsCompletelyDelivered = 0

    group by

        i.Material,
        i.Plant,
        i.StorageLocation

)

select

    inv.*,

    sales.RequestedQuantity,

    sales.ScheduleLineOrderQuantity,

    sales.ConfdOrderQtyByMatlAvailCheck,

    sales.DeliveredQtyInOrderQtyUnit,

    sales.OpenConfdDelivQtyInOrdQtyUnit,

    sales.SalesOrderItemCount,

    coalesce(
        po.PurchaseOrderQtyOrdered,
        0
    ) as PurchaseOrderQtyOrdered,

    coalesce(
        po.PurchaseOrderQtyCommitted,
        0
    ) as PurchaseOrderQtyCommitted,

    coalesce(
        po.PurchaseOrderQtyATP,
        0
    ) as PurchaseOrderQtyATP,
    
    coalesce(inv.ValuateFreeStock,0)
    - coalesce(sales.OpenConfdDelivQtyInOrdQtyUnit,0)
    + coalesce(po.PurchaseOrderQtyATP,0)

    as EstimatedAvailableStock,


    coalesce(inv.ValuateFreeStock,0)
    + coalesce(inv.StockInQualityInspection,0)
    + coalesce(inv.BlockedStock,0)
        as TotalOnHand,
    
    coalesce(inv.ValuateFreeStock,0)
    - coalesce(sales.OpenConfdDelivQtyInOrdQtyUnit,0)
        as ATP_WithoutPO,

    coalesce(inv.ValuateFreeStock,0)
    - coalesce(sales.OpenConfdDelivQtyInOrdQtyUnit,0)
    + coalesce(po.PurchaseOrderQtyATP,0)
        as ATP_WithPO,

    desc_tbl.ProductDescription,

    prod.ProductGroup as MaterialGroupCode,

    prod.ProductType,

    psd.ProductHierarchy,
    ph.ProductHierarchyLevel2Name

from inventory_pivot inv

left join sales

    on inv.Material = sales.Material
   and inv.Plant = sales.Plant
   and inv.StorageLocation = sales.StorageLocation

left join product_desc desc_tbl

    on inv.Material = desc_tbl.Material

left join product_group prod

    on inv.Material = prod.Material

left join product_sales_delivery psd

    on inv.Material = psd.Material

left join product_hierarchy ph

    on left(psd.ProductHierarchy, 6)
       = ph.ProductHierarchyLevel2Code

left join purchase_orders po

    on inv.Material = po.Material
   and inv.Plant = po.Plant
   and inv.StorageLocation = po.StorageLocation