FROM rust:latest

COPY ./sample.py .
COPY ./for-drug-test.csv .

RUN apt-get update && apt-get install jq -y

RUN cargo install drug-extraction-cli

RUN curl \
    "https://raw.githubusercontent.com/UK-IPOP/drug-extraction/main/de-workflow/data/drug_info.json" | \
    jq 'map_values(join(";"))' > lookup_data.json

RUN TERMS=`jq -r 'keys | sort | join("|")' lookup_data.json`; extract-drugs \
    simple-search \
    "for-drug-test.csv" \
    --target-column "primarycause" \
    --id-column "casenumber" \
    --search-words $TERMS \
    --algorithm "d" \
    --threshold "0.9" \
    --format "jsonl"

RUN python3 sample.py

CMD ["bash"]
