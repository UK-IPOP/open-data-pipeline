#! /bin/bash

mkdir -p reports

for file in data/*_records.jsonl; do

    echo "Processing $file ..."
    # take action on each file. $f store current file name
    title=$(basename $file .jsonl)
    echo "Pandas Profiling Report -> $title"

    pandas_profiling $file "reports/$title.html" \
        --title "Pandas Profiling Report for $title" \
        --silent 
        # --silent --minimal  # switch to minimal mode because normal took ~20 minutes

done

