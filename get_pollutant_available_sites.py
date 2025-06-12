import requests
import json
import datetime as dt
import urllib.parse

# Base URL and endpoints
url_api = "https://data.airquality.nsw.gov.au"
get_observations = "api/Data/get_Observations"
get_sites = "api/Data/get_SiteDetails"
headers = {'Content-Type': 'application/json', 'accept': 'application/json'}

# 1. Get all site IDs
site_url = urllib.parse.urljoin(url_api, get_sites)
site_response = requests.get(site_url, headers=headers)
site_list = site_response.json()
site_ids = [site["site_id"] for site in site_list]

# 2. Define parameters and date range
parameters = ["CH4", "CO2"]
start_date = "2025-01-01"
end_date = "2025-03-31"

# 3. Check data availability
results = []

for site_id in site_ids:
    for param in parameters:
        obs_request = {
            "Parameters": [param],
            "Sites": [site_id],
            "StartDate": start_date,
            "EndDate": end_date,
            "Categories": ["Averages"],
            "SubCategories": ["Hourly"],
            "Frequency": ["Hourly average"]
        }

        query_url = urllib.parse.urljoin(url_api, get_observations)
        response = requests.post(query_url, data=json.dumps(obs_request), headers=headers)

        if response.status_code == 200:
            data = response.json()
            has_data = any(entry.get("Value") is not None for entry in data)
            results.append({"Site_Id": site_id, "Parameter": param, "HasData": has_data})
        else:
            results.append({"Site_Id": site_id, "Parameter": param, "HasData": False})

# 4. Print the result
print("Availability of CH4 and CO2 from 2025-01-01 to 2025-03-31:\n")
for r in results:
    print(f"Site {r['Site_Id']} | {r['Parameter']} → {'✅ Yes' if r['HasData'] else '❌ No'}")

