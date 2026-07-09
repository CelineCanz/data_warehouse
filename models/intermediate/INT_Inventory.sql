{{ config(
    materialized='table'
) }}

with inventory as (

    select

        Material,
        Plant,
        StorageLocation,
        MaterialBaseUnit,

        coalesce(
            InventoryStockType,
            'blank'
        ) as InventoryStockType,

        cast(
            MatlWrhsStkQtyInMatlBaseUnit
            as decimal(18,0)
        ) as Quantity

    from {{ source('sap', 'STG_MaterialStockPlant') }}

),

inventory_base as (

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

),

inbound_reallocation as (

    select

        Material,
        Plant,

        sum(Inbound_ShippingQty)
            as InboundShippingQty

    from inventory_base

    where coalesce(
        ltrim(rtrim(StorageLocation)),
        ''
    ) = ''

    group by

        Material,
        Plant

),

target_storage_location as (

    select

        Material,
        Plant,

        case

            when count(
                case
                    when coalesce(
                        ltrim(rtrim(StorageLocation)),
                        ''
                    ) <> ''
                    then 1
                end
            ) = 1

            then max(
                case
                    when coalesce(
                        ltrim(rtrim(StorageLocation)),
                        ''
                    ) <> ''
                    then StorageLocation
                end
            )

            else max(
                case
                    when right(StorageLocation,2) = '00'
                    then StorageLocation
                end
            )

        end as TargetStorageLocation

    from inventory_base

    group by

        Material,
        Plant

)

select

    inv.Material,
    inv.Plant,
    inv.StorageLocation,
    inv.MaterialBaseUnit,

    inv.ValuateFreeStock,
    inv.StockInQualityInspection,
    inv.InventoryStockType_04,
    inv.InventoryStockType_05,
    inv.InventoryStockType_06,
    inv.BlockedStock,

    inv.Inbound_ShippingQty
    +
    coalesce(
        case
            when inv.StorageLocation = tsl.TargetStorageLocation
            then ir.InboundShippingQty
        end,
        0
    ) as Inbound_ShippingQty,

    inv.InventoryStockType_blank,

    coalesce(inv.ValuateFreeStock,0)
    + coalesce(inv.StockInQualityInspection,0)
    + coalesce(inv.BlockedStock,0)
        as TotalOnHand

from inventory_base inv

left join target_storage_location tsl

    on inv.Material = tsl.Material
   and inv.Plant = tsl.Plant

left join inbound_reallocation ir

    on inv.Material = ir.Material
   and inv.Plant = ir.Plant

where coalesce(
    ltrim(rtrim(inv.StorageLocation)),
    ''
) <> ''