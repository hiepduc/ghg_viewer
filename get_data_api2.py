import os
import requests
import logging
import urllib.parse
import datetime as dt
import json

class AQMS_API:
    """
    This class defines and configures the API to query the AQMS database.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.url_api = "https://data.airquality.nsw.gov.au/"
        self.headers = {
            'content-type': 'application/json',
            'accept': 'application/json'
        }
        self.get_observations_endpoint = 'api/Data/get_Observations'

    def get_observations(self, obs_request):
        """
        Send a POST request to fetch observation data.
        """
        query_url = urllib.parse.urljoin(self.url_api, self.get_observations_endpoint)
        response = requests.post(url=query_url, data=json.dumps(obs_request), headers=self.headers)
        return response

    def build_obs_request(self):
        """
        Build the observation request payload.
        """
        obs_request = {
            'Parameters': ['NO2'],
            'Sites': [141, 39, 336],  # Site IDs (example)
            'StartDate': dt.date(2024, 12, 5).strftime('%Y-%m-%d'),
            'EndDate': dt.date(2024, 12, 15).strftime('%Y-%m-%d'),
            'Categories': ['Averages'],
            'SubCategories': ['Hourly'],
            'Frequency': ['Hourly average']
        }
        return obs_request


if __name__ == '__main__':
    aqms = AQMS_API()
    obs_request = aqms.build_obs_request()
    response = aqms.get_observations(obs_request)

    if response.status_code == 200:
        # Parse JSON response
        data = response.json()

        # Save to file
        with open("HistoricalObs.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("Data saved to HistoricalObs.json")
    else:
        print(f"Failed to get data: {response.status_code}")
        print(response.text)

