import requests
import json
from pathlib import Path

Path("data").mkdir(exist_ok=True)

# fetch san diego county
resp = requests.get("https://data.sandiegocounty.gov/resource/jkvb-n4p7.json")
data = resp.json()
with open(Path("data/san_diego_county.json"), "w") as f:
    json.dump(data, f)


# fetch cook county
resp = requests.get("https://datacatalog.cookcountyil.gov/resource/3trz-enys.json")
data = resp.json()
with open(Path("data/cook_county.json"), "w") as f:
    json.dump(data, f)


# fetch milwaukee, taken directly from https://github.com/UK-IPOP/milwaukee-analysis/blob/main/scripts/fetch_data.py
payload = {"resultOffset": 0}
response_valid = True

data = []
with open(Path("data/milwaukee_county.json"), "w") as f:
    while response_valid:
        response = requests.get(
            "https://lio.milwaukeecountywi.gov/arcgis/rest/services/MedicalExaminer/PublicDataAccess/MapServer/1/query?f=json&where=1%3D1&outFields=*&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outSR=102100",
            params=payload,
        )
        json_data = response.json()
        if len(json_data["features"]) == 0:
            response_valid = False
            break
        for record in json_data["features"]:
            info = record["attributes"]
            data.append(info)
        payload["resultOffset"] += 1000
        print(payload)

    json.dump(data, f)
