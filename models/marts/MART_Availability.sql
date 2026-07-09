{{ config(
    materialized='table'
) }}

with inventory as (

    select *
    from {{ ref('INT_Inventory') }}

),

sales as (

    select *
    from {{ ref('INT_Sales') }}

),

purchase_orders as (

    select *
    from {{ ref('INT_PurchaseOrders') }}

),

product as (

    select *
    from {{ ref('INT_Products') }}

)

select

    inv.Material,
    inv.Plant,
    inv.StorageLocation,

    inv.MaterialBaseUnit,

    -- Stock

    inv.TotalOnHand,

    inv.ValuateFreeStock
        as UnrestrictedStock,

    inv.BlockedStock,

    inv.InventoryStockType_04
        as InTransferStock,

    inv.StockInQualityInspection,

    inv.Inbound_ShippingQty
        as IBShippingNotification,

    -- Sales

    sales.RequestedQuantity,

    sales.ScheduleLineOrderQuantity
        as SalesOrderQty,

    sales.ConfdOrderQtyByMatlAvailCheck
        as ConfirmedSalesOrderQty,

    sales.DeliveredQtyInOrderQtyUnit
        as DeliveredSalesOrderQty,

    sales.OpenConfdDelivQtyInOrdQtyUnit
        as OpenConfirmedSalesOrderQty,

    sales.SalesOrderItemCount,

    -- Purchase Orders

    coalesce(
        po.PurchaseOrderQtyOrdered,
        0
    ) as PurchaseOrderOrderedQty,

    coalesce(
        po.PurchaseOrderQtyCommitted,
        0
    ) as PurchaseOrderCommittedQty,

    coalesce(
        po.PurchaseOrderQtyATP,
        0
    ) as PurchaseOrderQty,

        coalesce(
        po.FuturePurchaseOrderQty,
        0
    ) as FuturePurchaseOrderQty,

    -- ATP Calculations

    coalesce(inv.ValuateFreeStock,0)
    - coalesce(sales.OpenConfdDelivQtyInOrdQtyUnit,0)

        as CumATP,

    coalesce(inv.ValuateFreeStock,0)
    - coalesce(sales.OpenConfdDelivQtyInOrdQtyUnit,0)
    + coalesce(po.PurchaseOrderQtyATP,0)

        as ATPWithPO,

    coalesce(inv.ValuateFreeStock,0)
    - coalesce(sales.OpenConfdDelivQtyInOrdQtyUnit,0)
    + coalesce(po.PurchaseOrderQtyATP,0)

        as EstimatedATP,

    -- Product

    product.ProductDescription,

    product.MaterialGroupCode,

    product.ProductType,

    product.ProductHierarchy,

    product.ProductHierarchyLevel2Name

from inventory inv

left join sales

    on inv.Material = sales.Material
   and inv.Plant = sales.Plant
   and inv.StorageLocation = sales.StorageLocation

left join purchase_orders po

    on inv.Material = po.Material
   and inv.Plant = po.Plant
   and inv.StorageLocation = po.StorageLocation

left join product

    on inv.Material = product.Material