import requests
import urllib.parse
import json

# Define API URL and endpoint
url_api = "https://data.airquality.nsw.gov.au"
get_parameters = "api/Data/get_ParameterDetails"
headers = {'Content-Type': 'application/json', 'accept': 'application/json'}

# Build full request URL
param_url = urllib.parse.urljoin(url_api, get_parameters)

# Send GET request
response = requests.get(param_url, headers=headers)

# Handle response
if response.status_code == 200 and response.text.strip():
    try:
        parameter_list = response.json()
        print(f"✅ Retrieved {len(parameter_list)} parameters")
        
        # Print some parameter names
        for p in parameter_list[:5]:  # show first 5 as a preview
            print(f"- {p['ParameterCode']}: {p['ParameterDescription']} ({p['Units']})")
        
        # Save to JSON
        with open("parameters.json", "w") as f:
            json.dump(parameter_list, f, indent=2)
        print("✅ Saved to parameters.json")

    except Exception as e:
        print(f"⚠️ JSON parsing error: {e}")
else:
    print(f"❌ Failed to fetch parameter details (status {response.status_code})")

