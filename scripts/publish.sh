#! /bin/bash

# you need to export GH_TOKEN 

echo $GH_TOKEN | docker login ghcr.io -u nanthony007 --password-stdin

echo "Building container..."
docker build -f containers/cli.Dockerfile -t opendata-pipeline:0.2 .

# you also need to custom edit this tag

echo "Tagging container..."
# tag for ghcr.io
docker tag bdc5d9c4e064 ghcr.io/uk-ipop/opendata-pipeline:0.2

echo "Publishing container..."
# push to ghcr.io
docker push ghcr.io/uk-ipop/opendata-pipeline:0.2

echo "Publishing PyPI package..."
uv publish --build 

echo "Publishing new docs..."
uv run mkdocs gh-deploy
