
select *
from {{ source('sap', 'STG_Product') }}