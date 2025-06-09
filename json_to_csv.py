import json
import pandas as pd

with open("HistoricalObs.json", "r") as f:
    data = json.load(f)

flat_data = []
for entry in data:
    row = {
        "Site_Id": entry["Site_Id"],
        "Parameter": entry["Parameter"]["ParameterCode"],
        "Date": entry["Date"],
        "Hour": entry["Hour"],
        "Value": entry["Value"],
        "Units": entry["Parameter"]["Units"]
    }
    flat_data.append(row)

df = pd.DataFrame(flat_data)
df.to_csv("HistoricalObs.csv", index=False)
print("Saved as HistoricalObs.csv")

