{{ config(
    materialized='table'
) }}

with product_desc as (

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

)

select

    p.Material,

    d.ProductDescription,

    p.ProductGroup as MaterialGroupCode,

    p.ProductType,

    psd.ProductHierarchy,

    ph.ProductHierarchyLevel2Name

from product_group p

left join product_desc d

    on p.Material = d.Material

left join product_sales_delivery psd

    on p.Material = psd.Material

left join product_hierarchy ph

    on left(psd.ProductHierarchy,6)
       = ph.ProductHierarchyLevel2Code