#! /bin/bash

python prepare_drugs.py

curl \
    "https://raw.githubusercontent.com/UK-IPOP/drug-extraction/main/de-workflow/data/drug_info.json" | \
    jq 'map_values(join(";"))' > lookup_data.json

TERMS=`jq -r 'keys | sort | join("|")' lookup_data.json`

extract-drugs \
    simple-search \
    "data/drug_input.csv" \
    --target-column "text" \
    --id-column "case_identifier" \
    --search-words $TERMS \
    --algorithm "osa" \
    --threshold "0.9" \
    --format "jsonl"

python3 update_drugs.py

