import requests
import urllib.parse
import json  # Needed to save to JSON

url_api = "https://data.airquality.nsw.gov.au"
get_sites = "api/Data/get_SiteDetails"
headers = {'Content-Type': 'application/json', 'accept': 'application/json'}

# Construct full URL
site_url = urllib.parse.urljoin(url_api, get_sites)

# Make request
response = requests.get(site_url, headers=headers)

# Debug info
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text[:200]}")  # print first 200 chars

# Parse and save
if response.status_code == 200 and response.text.strip():
    try:
        site_list = response.json()
        print(f"Retrieved {len(site_list)} sites")

        # Save to file
        with open("sites.json", "w") as f:
            json.dump(site_list, f, indent=2)
        print("✅ Site list saved to sites.json")

    except Exception as e:
        print(f"JSON parsing error: {e}")
else:
    print("❌ Failed to fetch or empty response from get_SiteDetails")

