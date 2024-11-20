#!/bin/bash

# Check if at least two arguments are passed (at least one input file)
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 file1.csv file2.csv [file3.csv ...]"
  exit 1
fi

# Ensure the "data" directory exists
output_dir="data"
mkdir -p "$output_dir"

# Define the output file path
output_file="$output_dir/pima_records.csv"

# Combine CSV files
awk '(NR == 1) || (FNR > 1)' "$@" >"$output_file"

# Notify user
echo "CSV files combined into '$output_file'"
