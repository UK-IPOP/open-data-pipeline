#!/bin/bash

# Usage: ./bump_version.sh MAJOR|MINOR|PATCH

# Check if an argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 MAJOR|MINOR|PATCH"
    exit 1
fi

# Read the current version from pyproject.toml using awk
version=$(awk -F' = "' '/^version = / {print $2}' pyproject.toml | tr -d '"')

# Check if the version was found
if [ "$version" = "" ]; then
    echo "No version found in pyproject.toml"
    exit 1
fi

# Split the version into components (MAJOR, MINOR, PATCH)
IFS='.' read -r major minor patch <<<"$version"

# Bump the version based on the argument
case $1 in
MAJOR)
    major=$((major + 1))
    minor=0
    patch=0
    ;;
MINOR)
    minor=$((minor + 1))
    patch=0
    ;;
PATCH)
    patch=$((patch + 1))
    ;;
*)
    echo "Invalid argument. Use MAJOR, MINOR, or PATCH."
    exit 1
    ;;
esac

# Construct the new version
new_version="$major.$minor.$patch"

# Update the version in pyproject.toml using awk
awk -F' = "' -v new_version="$new_version" '{
    if ($1 == "version") {
        print "version = \"" new_version "\""
    } else {
        print $0
    }
}' pyproject.toml >pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml

echo "Version bumped to $new_version"
