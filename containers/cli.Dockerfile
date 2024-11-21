# Step 1: Clone the source code
FROM alpine:3.18 AS builder
RUN apk add --no-cache git
WORKDIR /app

# clone latest source code
RUN git clone https://github.com/UK-IPOP/open-data-pipeline.git .

# Step 2: Build the final image
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY --from=builder /app /app

# Sync the project into a new environment, using the frozen lockfile
RUN uv sync --frozen

# run the cli
ENTRYPOINT ["uv", "run", "opendata-pipeline"]

# # default command provided to cli
CMD ["--help"]
