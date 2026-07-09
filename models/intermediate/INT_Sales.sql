{{ config(
    materialized='table'
) }}

with sales_schedule as (

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

)

select

    i.Material,
    i.Plant,
    i.StorageLocation,

    sum(i.RequestedQuantity)
        as RequestedQuantity,

    sum(coalesce(s.ScheduleLineOrderQuantity,0))
        as ScheduleLineOrderQuantity,

    sum(coalesce(s.ConfdOrderQtyByMatlAvailCheck,0))
        as ConfdOrderQtyByMatlAvailCheck,

    sum(coalesce(s.DeliveredQtyInOrderQtyUnit,0))
        as DeliveredQtyInOrderQtyUnit,

    sum(coalesce(s.OpenConfdDelivQtyInOrdQtyUnit,0))
        as OpenConfdDelivQtyInOrdQtyUnit,

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