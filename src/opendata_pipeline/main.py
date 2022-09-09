from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional
import typer


# use a lot of aliases for these imports
from opendata_pipeline import (
    models,
    manage_config,
    extract_drugs as drug_extractor,
    geocode as geocoder,
    fetch as fetcher,
    analyze as analyzer,
    spatial_join as spatial_joiner,
    utils,
)

APP_NAME = "opendata-pipeline"

app = typer.Typer(
    name=APP_NAME,
    help="A command line tool for running the UK-IPOP Medical Examiner's Open Data Pipeline.",
    rich_markup_mode="rich",
)


def get_settings(remote: bool) -> models.Settings:
    if remote:
        return manage_config.get_remote_config()
    return manage_config.get_local_config()


@app.command("init")
def init():
    """Initialize the project"""
    utils.setup()


@app.command("fetch")
def fetch(
    use_remote: bool = typer.Option(
        False,
        help="Whether to use the remote configuration or not. Default is False (i.e. use local config.json)",
    ),
    update_remote: bool = typer.Option(
        False,
        help="Whether to update the remote configuration or not. Default is False (i.e. update local config.json)",
    ),
) -> None:
    """:warning: Fetch data from data sources.

    This command will fetch data from data sources and save it to the data directory.

    If `use_remote`/`update_remote` are True, the remote configuration will be used/updated. Otherwise, the local configuration will be used.

    If you are not me, you cannot `update_remote` because you do not have the correct permissions.

    Expects the project to be initialized before running this command.

    Example: opendata-pipeline fetch --use-remote
    """
    settings = get_settings(remote=use_remote)
    asyncio.run(fetcher.run(settings=settings, update_remote=update_remote))


@app.command("extract-drugs")
def extract_drugs(
    use_remote: bool = typer.Option(
        False,
        help="Whether to use the remote configuration or not. Default is False (i.e. use local config.json)",
    )
) -> None:
    """Extract drugs from data sources.

    This command will extract drugs from data sources and save it to the data directory.

    ** You will need the `extract-drugs` CLI program installed and in your PATH for this command to work.
    You can get it here: https://github.com/UK-IPOP/drug-extraction

    If `use_remote` is True, the remote configuration will be used. Otherwise, the local configuration will be used.

    Expects the data to be fetched before running this command.

    Example: opendata-pipeline extract-drugs --use-remote
    """
    settings = get_settings(remote=use_remote)
    drug_extractor.run(settings=settings)


@app.command("geocode")
def geocode(
    use_remote: bool = typer.Option(
        False,
        help="Whether to use the remote configuration or not. Default is False (i.e. use local config.json)",
    ),
    custom_key: Optional[str] = typer.Option(
        None, help="Your own ArcGIS API key, geocoding not possible otherwise."
    ),
) -> None:
    """:warning: Geocode data sources.

    This command will geocode data sources and save it to the data directory.

    If `use_remote` is True, the remote configuration will be used. Otherwise, the local configuration will be used.

    Expects the data to be fetched before running this command.

    If you are not me, you must provide your own ArcGIS API key using the `custom_key` option.

    Example: opendata-pipeline geocode --use-remote
    """
    settings = get_settings(remote=use_remote)
    asyncio.run(geocoder.run(settings=settings, alternate_key=custom_key))


@app.command()
def spatial_join():
    """Spatially join data sources.

    Currently this command is a placeholder. It will be implemented in the future.
    """
    spatial_joiner.run()


@app.command("analyze")
def analyze(
    use_remote: bool = typer.Option(
        False,
        help="Whether to use the remote configuration or not. Default is False (i.e. use local config.json)",
    ),
    update_remote: bool = typer.Option(
        False,
        help="Whether to update the remote configuration or not. Default is False (i.e. update local config.json)",
    ),
) -> None:
    """:warning: Analyze the data.

    This command takes the various output files and joins them to the original data for
    a "wide-form" datafile that is commonly used in data analysis.

    This command will geocode data sources and save it to the data directory.

    If `use_remote` is True, the remote configuration will be used. Otherwise, the local configuration will be used.
    Configuration file required for

    Unless you are me, you cannot `update_remote` because you do not have the correct permissions.

    Expects the data to be fetched before running this command.
    Expects the drugs to be extracted before running this command.
    Expects the data to be geocoded before running this command.

    Example: opendata-pipeline analyze --use-remote
    """
    settings = get_settings(remote=use_remote)
    analyzer.run(settings=settings)


@app.command("teardown")
def teardown():
    """Teardown the project, deleting all data files."""
    utils.teardown()


if __name__ == "__main__":
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / "config.json"
    if not config_path.is_file():
        print("Config file doesn't exist yet, make sure to use remote config.")
    app()
