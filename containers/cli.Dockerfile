FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app
RUN uv sync --frozen

# run the cli
ENTRYPOINT ["uv", "run", "opendata-pipeline"]

# # default command provided to cli
CMD ["--help"]
