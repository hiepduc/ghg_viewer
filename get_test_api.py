import requests
import pandas as pd

# Example endpoint (for forecast AQI)
url = "https://data.airquality.nsw.gov.au/api/Data/get_forecast_aqi"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    
    # Convert to DataFrame for readability
    df = pd.DataFrame(data)
    
    print(df.head())
else:
    print(f"Error: {response.status_code}")
