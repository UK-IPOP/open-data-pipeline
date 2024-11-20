FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the project into the image
ADD . /app

# we don't need all these datafiles
RUN rm -r /app/data
RUN mkdir /app/data
ADD data/pima_records.csv /app/data/pima_records.csv

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app
RUN uv sync --frozen

# run the cli
ENTRYPOINT ["uv", "run", "opendata-pipeline"]

# # default command provided to cli
CMD ["--help"]
