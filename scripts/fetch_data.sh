#! /bin/bash

# this script curls each dataset (a single json file) and sends it through `jq` to be processed into jsonlines

# fetch san diego county data
curl --data-urlencode https://data.sandiegocounty.gov/resource/jkvb-n4p7.json | jq -c '.[]' 
-o  data/san_diego_county.jsonl

# fetch cook county data
curl -G --data-urlencode "%24limit=100" --data-urlencode "%24order=death_date%20DESC" https://datacatalog.cookcountyil.gov/resource/3trz-enys.json


# TODO: solve milwaukee problem
# https://lio.milwaukeecountywi.gov/arcgis/rest/services/MedicalExaminer/PublicDataAccess/MapServer/1/query?f=json&where=1%3D1&outFields=*&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outSR=102100
