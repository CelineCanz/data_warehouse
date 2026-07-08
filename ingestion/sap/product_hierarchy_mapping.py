#%%import pandas as pd

import pandas as pd 
from config.sql_server import create_table, write_df
import sys
sys.path.append(r"E:\Python\data_warehouse")
# Lecture du CSV
df = pd.read_csv(
    r"E:\Python\data_warehouse\ingestion\sap\product_hierarchy_mapping.csv",
    sep=";",
    encoding="utf-8"
)

# Renommage
df = df.rename(
    columns={
        "PH2Number": "ProductHierarchyLevel2Code",
        "PH2Name": "ProductHierarchyLevel2Name",
        "PH3Number": "ProductHierarchyLevel3Code",
        "PH3Name": "ProductHierarchyLevel3Name",
        "PH4Number": "ProductHierarchyLevel4Code",
        "PH4Name": "ProductHierarchyLevel4Name",
    }
)

# Garder uniquement le niveau 2
df = (
    df[
        [
            "ProductHierarchyLevel2Code",
            "ProductHierarchyLevel2Name"
        ]
    ]
    .drop_duplicates()
    .sort_values("ProductHierarchyLevel2Code")
)


#%%
# Chargement SQL
create_table(
    df,
    "MAP_ProductHierarchy"
)

write_df(
    df,
    "MAP_ProductHierarchy"
)

print(df.shape)
print(df.head())
# %%
print(df)
# %%
