"""This module manages the config.json file.

It is used to update the config.json file on GitHub.

The config.json file is used to store the configuration for the pipeline.

It can also update a local config.json file.
"""

from datetime import date
import json
from pathlib import Path
import orjson
import requests
import base64

from opendata_pipeline import models
from opendata_pipeline.utils import console


def get_local_config() -> models.Settings:
    """Get the config.json file from the project's root."""
    console.log("Getting local config.json file")
    return models.Settings.parse_file("config.json")


def get_remote_config() -> models.Settings:
    """Get the config.json file from the project's root on GitHub."""
    url = (
        "https://raw.githubusercontent.com/UK-IPOP/open-data-pipeline/main/config.json"
    )
    console.log("Getting remote config.json file")
    resp = requests.get(url)
    if resp.status_code != 200:
        raise ValueError(resp.content)
    return models.Settings.parse_raw(resp.content)


def update_local_config(config: models.Settings):
    """Update the local config.json file."""
    console.log("Updating local config.json file")
    data = config.dict(exclude={"arcgis_api_key", "github_token"})
    with open(Path("config.json"), "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def update_remote_config(config: models.Settings):
    """Update the remote config.json file using the GitHub API."""
    if config.github_token is None:
        raise ValueError("github_token is required to update remote config")
    url = "https://api.github.com/repos/UK-IPOP/open-data-pipeline/contents/config.json"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {config.github_token}",
    }
    get_file = requests.get(url, headers=headers)
    if get_file.status_code != 200:
        raise ValueError(get_file.content)
    file_sha = get_file.json()["sha"]

    data = {}
    today = date.today().strftime("%Y-%m-%d")
    data["message"] = f"Update config.json -- {today}"
    data["sha"] = file_sha

    # encode the file contents
    encoded = orjson.dumps(
        config.dict(exclude={"arcgis_api_key", "github_token"}),
        option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
    )
    data["content"] = base64.b64encode(encoded).decode("utf-8")

    console.log("Updating remote config.json file")
    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code != 200:
        raise ValueError(resp.content)
