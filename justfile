default:
    @just --list

init:
    @uv run opendata-pipeline init

fetch:
    @uv run opendata-pipeline fetch

drugs:
    @uv run opendata-pipeline extract-drugs

geocode:
    @uv run opendata-pipeline geocode

analyze:
    @uv run opendata-pipeline analyze

spatial:
    @uv run opendata-pipeline spatial-join

teardown:
    @uv run opendata-pipeline teardown

run-all:
    @uv run opendata-pipeline init
    @uv run opendata-pipeline fetch
    @uv run opendata-pipeline extract-drugs
    @uv run opendata-pipeline geocode
    @uv run opendata-pipeline analyze
    @uv run opendata-pipeline spatial-join
    @uv run opendata-pipeline teardown

release MAJOR|MINOR|PATCH:
    # Check if a valid argument is passed
    if test (argc) != 1
        echo "Usage: just bump-version MAJOR|MINOR|PATCH"
        exit 1
    end

    @./scripts/bump_version.sh $1
    @./scripts/publish.sh
