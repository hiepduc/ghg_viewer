import requests
from datetime import datetime

API_URL = "https://data.airquality.nsw.gov.au/api/Data/Get_Observations"
HEADERS = {
    "Content-Type": "application/json",
    "accept": "application/json"
}

# Replace this with actual ID for Rozelle from get_SiteDetails
site_id = 39  # Check this is correct
parameter_code = "NO2"  # Must match ParameterCode, NOT description

# Use a recent, short date range
from_date = datetime(2024, 12, 1).strftime("%Y-%m-%d")
to_date = datetime(2024, 12, 3).strftime("%Y-%m-%d")

payload = {
    "Site_Id": site_id,
    "ParameterCode": parameter_code,
    "StartDate": from_date,
    "EndDate": to_date,
    "Categories": "Averages",
    "SubCategories": "Hourly",
    "Frequency": "Hourly average"
}

print("Sending payload:", payload)

try:
    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    print(f"Returned {len(data)} records.")
    if data:
        print("Sample record:", data[0])
except requests.exceptions.RequestException as e:
    print(f"Error occurred: {e}")

