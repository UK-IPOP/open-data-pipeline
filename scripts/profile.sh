#! /bin/bash

for file in data/*.jsonl; do

    echo "Processing $file ..."
    # take action on each file. $f store current file name
    title=$(basename $file .jsonl)
    echo "Pandas Profiling Report -> $title"

    pandas_profiling $file "reports/$title.html" \
        --title "Pandas Profiling Report for $title" \
        --silent \
        --minimal  # toggle for faster... check duration once all data is merged

done

