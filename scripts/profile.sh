#! /bin/bash

# This script runs pandas profiling on each dataset.

mkdir -p reports

for file in data/*_wide_form.csv; do

    echo "Processing $file ..."
    # take action on each file. $f store current file name
    title=$(basename "$file" .csv)

    uvx --python="3.12" --with="setuptools" ydata_profiling "$file" "reports/$title.html" \
        --title "Pandas Profiling Report for $title" \
        --infer_dtypes \
        --silent \
        --silent --minimal # switch to minimal mode because normal took ~20 minutes

done
