from datetime import date
import json
from pathlib import Path
import orjson
import requests
import base64

from opendata_pipeline import models

# functions to update local and remote data


def get_local_config() -> models.Settings:
    """Get the config.json file from the project's root."""
    return models.Settings.parse_file("config.json")


def get_remote_config() -> models.Settings:
    """Get the config.json file from the project's root on GitHub."""
    url = (
        "https://raw.githubusercontent.com/UK-IPOP/open-data-pipeline/main/config.json"
    )
    resp = requests.get(url)
    if resp.status_code != 200:
        raise ValueError(resp.content)
    return models.Settings.parse_raw(resp.content)


def update_local_config(config: models.Settings):
    """Update the local config.json file."""
    data = config.dict(exclude={"arcgis_api_key", "github_token"})
    with open(Path("config.json"), "w") as f:
        json.dump(data, f, indent=4)


def update_remote_config(config: models.Settings):
    """Update the remote config.json file."""
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
    encoded = orjson.dumps(config.dict(exclude={"arcgis_api_key", "github_token"}))
    data["content"] = base64.urlsafe_b64encode(encoded).decode()

    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code != 200:
        raise ValueError(resp.content)
