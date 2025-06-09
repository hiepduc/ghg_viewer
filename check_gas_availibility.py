import requests
import json
from datetime import date
import urllib.parse
import time

# Base API setup
BASE_URL = "https://data.airquality.nsw.gov.au/"
GET_OBSERVATIONS = "api/Data/get_Observations"
FULL_URL = urllib.parse.urljoin(BASE_URL, GET_OBSERVATIONS)

# Headers
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Date range
start_date = date(2024, 1, 1).strftime("%Y-%m-%d")
end_date = date(2025, 3, 31).strftime("%Y-%m-%d")

# Parameters to check
#pollutants = ["CH4", "CO2", "NH3"]
pollutants = ["NH3"]

# Load previously fetched site list
with open("sites.json", "r") as f:
    sites = json.load(f)

available_data = []

for site in sites:
    site_id = site["Site_Id"]
    site_name = site["SiteName"]

    print(f"Checking site {site_id} - {site_name}")

    for param in pollutants:
        payload = {
            "Parameters": [param],
            "Sites": [site_id],
            "StartDate": start_date,
            "EndDate": end_date,
            "Categories": ["Averages"],
            "SubCategories": ["Hourly"],
            "Frequency": ["Hourly average"]
        }

        try:
            response = requests.post(FULL_URL, headers=HEADERS, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data:  # non-empty
                    print(f"  ✅ Found {param} data")
                    available_data.append({
                        "Site_Id": site_id,
                        "SiteName": site_name,
                        "Parameter": param
                    })
                else:
                    print(f"  ⛔ No {param} data")
            else:
                print(f"  ⚠️ API error {response.status_code} for {param} at site {site_name}")
        except Exception as e:
            print(f"  ❌ Error for {param} at site {site_name}: {e}")

        time.sleep(0.3)  # Avoid overloading API

# Save results
with open("available_parameters_2025_Q1.csv", "w") as f:
    f.write("Site_Id,SiteName,Parameter\n")
    for entry in available_data:
        f.write(f"{entry['Site_Id']},{entry['SiteName']},{entry['Parameter']}\n")

print("\n✅ Done. Results saved to available_parameters_2025_Q1.csv")

