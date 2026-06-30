

import requests
from requests.auth import HTTPBasicAuth

# -------------------- SAP CONFIG --------------------

HOST = "prd.hec.yamaha.com"
CLIENT = "100"
USER = "7500D2C_DWH"
PASSWORD = "Yama#098"
WINDOW_SIZE = 5000

BASE = f"https://{HOST}/sap/opu/odata/sap"

# -------------------- SAP SESSION --------------------

def sap_session():
    session = requests.Session()
    session.auth = HTTPBasicAuth(USER, PASSWORD)
    session.headers.update({
        "Accept": "application/json"
    })
    return session
