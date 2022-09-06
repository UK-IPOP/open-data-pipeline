#! /bin/bash

# this simulates the github workflow locally, with some modifications for local vs github environments
# however it will not run without the .env secrets

poetry install

# JOB 1
# fetch new records and update db
poetry run python update_records.py


# JOB 2
# get records that haven't been drug processed (save as artifact file -.csv)
# process new records (artifact file) with drug tool (drug_pipeline dockerfile as template)
# update db with drug results
# extract-drugs ...

# JOB 3
# get records that haven't been geocoded (save as artifact file -.jsonl)
# geocode new records (artifact file) with geocoder
# update db with geocode results
# poetry run python geocode_records.py

# JOB 4
# EVENTUALLY: support geospatial joining
