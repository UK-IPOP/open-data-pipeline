#! /bin/bash

echo "Publishing container..."

# you need to export GH_TOKEN 

echo $GH_TOKEN | docker login ghcr.io -u nanthony007 --password-stdin

docker build -f containers/cli.Dockerfile -t opendata-pipeline:0.2 .

# you also need to custom edit this tag

# tag for ghcr.io
docker tag bdc5d9c4e064 ghcr.io/uk-ipop/opendata-pipeline:0.2

# push to ghcr.io
docker push ghcr.io/uk-ipop/opendata-pipeline:0.2

echo "Publishing PyPI package..."

# publish to poetry
poetry publish --build 