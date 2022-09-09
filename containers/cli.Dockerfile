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
ENTRYPOINT ["opendata-pipeline"]

# default command provided to cli
CMD ["--help"]
