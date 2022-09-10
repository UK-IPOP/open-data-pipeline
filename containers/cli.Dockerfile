FROM rust:1.62 as builder

RUN cargo install drug-extraction-cli

# arcgis requires python 3.9
FROM python:3.10-slim-bullseye

RUN python3 -m pip install poetry

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

# poetry install no dev
RUN poetry config virtualenvs.in-project false

COPY ./ /app

RUN poetry install --only main


# copy the binary from the builder
COPY --from=builder /usr/local/cargo/bin/extract-drugs /usr/bin/extract-drugs

# run the cli
ENTRYPOINT ["poetry", "run", "opendata-pipeline"]

# # default command provided to cli
CMD ["--help"]
