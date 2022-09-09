#! /bin/bash

# use this script to run the CLI from test pypi

pipx run \
    --python $(which python) \
    --index-url "https://test.pypi.org" \
    opendata-pipeline --help