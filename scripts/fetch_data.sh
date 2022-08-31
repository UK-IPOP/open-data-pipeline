#! /bin/bash

# this script curls each dataset (a single json file) and sends it through `jq` to be processed into jsonlines

# fetch san diego county data
curl https://data.sandiegocounty.gov/resource/jkvb-n4p7.json | jq -c '.[]' > data/san_diego_county.jsonl

# fetch cook county data
curl "https://datacatalog.cookcountyil.gov/resource/3trz-enys.json?$limit=20000" | jq -c '.[]' > data/cook_county.jsonl


# TODO: solve milwaukee problem
# https://lio.milwaukeecountywi.gov/arcgis/rest/services/MedicalExaminer/PublicDataAccess/MapServer/1/query?f=json&where=1%3D1&outFields=*&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outSR=102100
