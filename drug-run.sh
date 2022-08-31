#! /bin/bash


terms=`jq -r 'keys | sort | join("|")' lookup_data.json`

extract-drugs \
    simple-search \
    "drug_input.csv" \
    --target-column "text" \
    --id-column "case_identifier" \
    --search-words $terms \
    --algorithm "d" \
    --threshold "0.9" \
    --format "jsonl"