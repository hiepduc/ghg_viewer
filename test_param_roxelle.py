import requests

params_url = "https://data.airquality.nsw.gov.au/api/Data/get_ParameterDetails"
response = requests.get(params_url)
params = response.json()

for p in params:
    # print all keys to understand structure
    print(p.keys())
    # or just print param details with "NO2"
    if 'NO2' in (p.get("ParameterCode","") + p.get("ParameterDescription","")):
        print(p)

