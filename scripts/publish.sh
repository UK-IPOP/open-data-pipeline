#!/bin/bash

set -e          # Exit immediately if a command exits with a non-zero status
set -o pipefail # Catch errors in pipelines

source .env

# Ensure GH_TOKEN is set
if [ "$GH_TOKEN" = "" ]; then
    echo "Error: GH_TOKEN is not set. Please export GH_TOKEN."
    exit 1
fi

# Login to GitHub container registry
echo "$GH_TOKEN" | docker login ghcr.io -u nanthony007 --password-stdin

# Extract the version from pyproject.toml
VERSION=$(awk -F'"' '/^version = / {print $2}' pyproject.toml)

if [ "$VERSION" = "" ]; then
    echo "Error: Unable to extract version from pyproject.toml."
    exit 1
fi

echo "Detected version: $VERSION"

# Build the Docker container
echo "Building container..."
docker build -f containers/cli.Dockerfile -t opendata-pipeline:"$VERSION" .

# Get the image ID
IMAGE_ID=$(docker inspect --format='{{.Id}}' opendata-pipeline:"$VERSION")
CLEAN_IMAGE_ID=${IMAGE_ID#sha256:}

# Tag and push the container to GitHub Container Registry
echo "Tagging container..."
docker tag "$CLEAN_IMAGE_ID" "ghcr.io/uk-ipop/opendata-pipeline:$VERSION"

echo "Publishing container..."
docker push "ghcr.io/uk-ipop/opendata-pipeline:$VERSION"

# Build and publish the Python package
# remove previous versions
echo "Building Python package..."
rm -r dist
uv build

echo "Publishing PyPI package..."
uv publish --token "$PYPI_KEY"

# Deploy the updated documentation
echo "Publishing new docs..."
uv run mkdocs gh-deploy

echo "All steps completed successfully!"
