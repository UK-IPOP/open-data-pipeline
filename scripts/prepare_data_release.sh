#! /bin/bash

# This script prepares the data release.

# general tar info
# -c creates archive
# -z uses gzip compression
# -f specifies filename

mkdir -p assets

echo "Creating tarball zip of reports..."
tar -czf assets/reports.tar.gz reports

echo "Creating tarball zip of data sets..."
for folder in data/*/; do
    echo "Processing $folder ..."
    tar -czf assets/$(basename $folder).tar.gz $folder
done

echo "Copying spatial join form csv files to assets"
cp data/*_spatial_join.csv assets/
