{{ config(
    materialized='table'
) }}

with purchase_order_item as (

    select

        PurchaseOrder,
        PurchaseOrderItem,

        Material,
        Plant,

        StorageLocation,

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

)

select

    i.Material,
    i.Plant,
    i.StorageLocation,

    sum(s.ScheduleLineOrderQuantity)
        as PurchaseOrderQtyOrdered,

    sum(s.ScheduleLineCommittedQuantity)
        as PurchaseOrderQtyCommitted,

    sum(
        case
            when s.ScheduleLineDeliveryDate >= cast(getdate() as date)
            then
                coalesce(
                    nullif(
                        s.ScheduleLineCommittedQuantity,
                        0
                    ),
                    s.ScheduleLineOrderQuantity
                )
            else 0
        end
    ) as FuturePurchaseOrderQty,
    
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

where i.IsCompletelyDelivered = 0

group by

    i.Material,
    i.Plant,
    i.StorageLocation