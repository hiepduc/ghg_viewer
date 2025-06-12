import requests
import json
from datetime import datetime

HEADERS = {'Content-Type': 'application/json', 'accept': 'application/json'}
SITE_URL = "https://data.airquality.nsw.gov.au/api/Data/get_SiteDetails"
PARAM_URL = "https://data.airquality.nsw.gov.au/api/Data/get_ParameterDetails"
API_URL = "https://data.airquality.nsw.gov.au/api/Data/Get_Observations"

# Step 1: Load site and parameter maps
sites = requests.get(SITE_URL, headers=HEADERS).json()
params = requests.get(PARAM_URL, headers=HEADERS).json()

site_map = {s["SiteName"]: s["Site_Id"] for s in sites if "SiteName" in s and "Site_Id" in s}
param_map = {p["ParameterCode"]: p for p in params if "ParameterCode" in p}

# Step 2: Pick one site and test parameter
test_site_name = "ROZELLE"
test_param_code = "NO2"

if test_site_name not in site_map:
    print(f"Site '{test_site_name}' not found.")
    exit()

if test_param_code not in param_map:
    print(f"Parameter '{test_param_code}' not found.")
    exit()

test_site_id = site_map[test_site_name]

# Step 3: Construct payload and test API call
payload = {
    "SiteId": test_site_id,
    "ParameterId": param_map[test_param_code]["ParameterCode"],
    "FromDate": "2023-01-01",
    "ToDate": "2023-01-07"
}

try:
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    print(f"Returned {len(data)} records for {test_param_code} at {test_site_name}")
    if len(data) > 0:
        print(json.dumps(data[:3], indent=2))  # Print first 3 data points
    else:
        print("No data returned.")

except Exception as e:
    print(f"Error occurred: {e}")

