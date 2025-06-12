import requests
import json
import pandas as pd
import datetime as dt
import urllib.parse

# API base and endpoint
url_api = "https://data.airquality.nsw.gov.au"
get_observations = "api/Data/get_Observations"
headers = {'Content-Type': 'application/json', 'accept': 'application/json'}

# Setup request payload
ObsRequest = {
    "Parameters": ["NO2"],          # Replace with "CH4" if needed
    "Sites": [39],                  # Replace with desired Site ID
    "StartDate": "2024-12-05",
    "EndDate": "2024-12-15",
    "Categories": ["Averages"],
    "SubCategories": ["Hourly"],
    "Frequency": ["Hourly average"]
}

# Send POST request
query_url = urllib.parse.urljoin(url_api, get_observations)
response = requests.post(query_url, data=json.dumps(ObsRequest), headers=headers)

# Parse response
data = response.json()

# Filter non-null values and flatten
flat_data = []
for entry in data:
    if entry.get("Value") is not None:
        flat_data.append({
            "Site_Id": entry["Site_Id"],
            "Date": entry["Date"],
            "Hour": entry["Hour"],
            "Value": entry["Value"],
            "ParameterCode": entry["Parameter"]["ParameterCode"],
            "Units": entry["Parameter"]["Units"]
        })

# Convert to DataFrame and save to CSV
df = pd.DataFrame(flat_data)
df.to_csv("AQMS_Observations.csv", index=False)
print("Saved to AQMS_Observations.csv")
