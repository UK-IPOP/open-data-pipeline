#! /bin/bash

# This script runs pandas profiling on each dataset.

mkdir -p reports

for file in data/*_records.jsonl; do

    echo "Processing $file ..."
    # take action on each file. $f store current file name
    title=$(basename $file .jsonl)

    pandas_profiling $file "reports/$title.html" \
        --title "Pandas Profiling Report for $title" \
        --silent 
        # --silent --minimal  # switch to minimal mode because normal took ~20 minutes

done

