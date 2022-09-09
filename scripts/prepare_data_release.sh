#! /bin/bash

# general tar info
# -c creates archive
# -z uses gzip compression
# -f specifies filename

mkdir -p assets

tar -czf assets/reports.tar.gz reports

for folder in data/*/; do
    echo "Processing $folder ..."
    tar -czf assets/$(basename $folder).tar.gz $folder
done

echo "Copying wide form csv files to assets"
cp data/*_wide_form.csv assets/
