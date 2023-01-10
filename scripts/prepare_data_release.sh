#! /bin/bash

# This script prepares the data release.

mkdir -p assets

echo "Creating zip of reports..."
# recurisve, verbose, highly compressed
zip -rv9 assets/reports.zip reports/*.html 

echo "Creating zip of data sets..."
for folder in data/*/; do
    echo "Processing $folder ..."
    zip -rv9 assets/$(basename $folder).zip $folder
done

echo "Copying spatial join form csv files to assets"
cp data/*_wide_form.csv assets/
