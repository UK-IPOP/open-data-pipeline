FROM rust:1.62 as builder

RUN cargo install drug-extraction-cli

# arcgis requires python 3.9
FROM python:3.9

# install pipx because its great
RUN python3 -m pip install pipx
# validate install
RUN python3 -m pipx ensurepath

# install poetry
RUN pipx install poetry

# copy files
COPY ./ /app

# set dir
WORKDIR /app

# poetry install no dev
RUN poetry install --no-dev

# copy the binary from the builder
COPY --from=builder /usr/local/cargo/bin/extract-drugs /usr/bin/extract-drugs

# run the cli
# initialize folders
RUN opendata-pipeline init

# fetch datasets
RUN opendata-pipeline fetch

# extract drugs
RUN opendata-pipeline extract-drugs

# skip geocoding because no auth
# RUN opendata-pipeline geocode

# skip geospatial join because no spatial
# RUN opendata-pipeline geospatial-join

# analyze
RUN opendata-pipeline analyze

# teardown
RUN opendata-pipeline teardown

