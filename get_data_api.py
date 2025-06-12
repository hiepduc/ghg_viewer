import requests
import pandas as pd

# POST endpoint
url = "https://data.airquality.nsw.gov.au/api/Data/get_air_quality_site_data"

# Set payload with required parameters
payload = {
    "date": "2024-06-01",             # Date in yyyy-mm-dd
    "site": "39",                # Site name (e.g., Rozelle, Lidcombe)
    "parameter": "PM2.5",             # Parameter (e.g., PM2.5, NO2)
    "type": "Hourly"                  # Type: "Hourly" or "Daily"
}

# Send request
response = requests.post(url, json=payload)

# Parse response
if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data["data"])
    print(df.head())
else:
    print(f"Failed to retrieve data: {response.status_code}")

