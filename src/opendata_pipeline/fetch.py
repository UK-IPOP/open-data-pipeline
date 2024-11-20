"""This module contains functions for fetching data from the open data portal or other sources.

It uses async requests if not using the open data portal to speed things up.
"""

from __future__ import annotations

import asyncio
import typing
from pathlib import Path

import httpx
import pandas as pd
import requests
from rich.progress import track

from opendata_pipeline import manage_config, models
from opendata_pipeline.utils import console


# this pattern of accessing "value" is common to all opendata api responses
def get_open_data_records(
    config: models.DataSource,
) -> list[dict[str, typing.Any]]:
    """Get records from open data portal.

    This is a synchronous request.

    It sets the total to 1000 + the data source current total.

    Args:
        config: DataSource object

    Returns:
        list[dict[str, typing.Any]]: list of records
    """
    # we add 1000 assuming there were more records than last week
    console.log(f"Fetching {config.name} records...")
    payload = {"$top": config.total_records + 1_000}
    response = requests.get(config.url, params=payload)
    data: dict[str, typing.Any] = response.json()
    if "value" not in data:
        raise ValueError(
            f"Unable to get records from {config.url}, `value` key not in response"
        )
    return data["value"]


def build_url(offset: int, base_url: str) -> str:
    """Build url for pagination.

    Adds resultOffset and resultRecordCount to url.

    Args:
        offset: int
        base_url: str

    Returns:
        str: url
    """
    # add 1000 record limit and offset params
    return f"{base_url}&resultRecordCount=1000&resultOffset={offset}"


# this pattern of accessing "features" and "attributes" is specific to MIL
# it may be common to other ARC GIS APIs but until we have more examples
# we will keep this function here
async def get_record_set(
    client: httpx.AsyncClient, url: str
) -> list[dict[str, typing.Any]]:
    """Get record set from url.

    An async function to get a record set from a url.

    If fails, retries.

    Args:
        client: httpx.AsyncClient
        url: str

    Returns:
        list[dict[str, typing.Any]]: list of records
    """
    resp = await client.get(url)
    # if returns error, try again
    if resp.status_code != 200:
        return await get_record_set(client, url)
    resp_data: dict[str, typing.Any] = resp.json()
    if "features" in resp_data:
        if len(resp_data["features"]) == 0:
            return []
        return [r["attributes"] for r in resp_data["features"]]
    return await get_record_set(client, url)


def make_df_with_identifier(
    records: list[dict[str, typing.Any]], current_index: int
) -> pd.DataFrame:
    """Make dataframe with case identifier.

    Uses the current index to label records with a global identifier.

    Args:
        records: list[dict[str, typing.Any]]
        current_index: int

    Returns:
        pd.DataFrame: dataframe with case identifier
    """
    df = pd.DataFrame(records)
    df["CaseIdentifier"] = df.index + current_index
    return df


# TODO: remove this when we can read jsonlines in drug tool
def export_drug_df(df: pd.DataFrame, config: models.DataSource) -> None:
    """Export drug dataframe to csv.

    This is a temporary function to export a csv for the drug tool.

    Args:
        df (pd.DataFrame): Drug Output dataframe
        config (models.DataSource): DataSource object
    """
    target_cols = ["CaseIdentifier"] + config.drug_columns
    out_path = Path("data") / config.drug_prep_filename
    df.loc[:, target_cols].to_csv(out_path, index=False)


def export_jsonlines_from_df(df: pd.DataFrame, config: models.DataSource) -> None:
    """Export jsonlines from dataframe."""
    console.log(f"Exporting {config.name} jsonlines...")
    out_path = Path("data") / config.records_filename
    df.to_json(out_path, orient="records", lines=True)


async def get_async_records(config: models.DataSource, current_index: int) -> int:
    """Get records from url.

    This is an async function to get records from a url for each dataset.

    Args:
        config: DataSource object
        current_index: int

    Returns:
        int: newly updated index
    """
    console.log(f"Fetching {config.name} records...")
    records = []
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(20),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    ) as client:
        # we add 2000 assuming there were more records than last week
        ranges = list(range(0, config.total_records + 2000, 1000))
        for offset in track(ranges):
            url = build_url(base_url=config.url, offset=offset)
            record_set = await get_record_set(client, url)
            records.extend(record_set)

    console.log(f"Fetched {len(records):,} records asynchronously from {config.url}")

    df = make_df_with_identifier(records, current_index)
    export_drug_df(df, config)
    export_jsonlines_from_df(df, config)
    return len(records)


def cook_county_drug_col(df: pd.DataFrame) -> pd.DataFrame:
    """Create composite drug column for Cook County."""
    # a custom handler for this primary cause of death
    # taken from STACKOVERFLOW
    dff = df.copy()
    dff["primary_cod"] = (
        dff["primarycause"]
        .combine(
            dff["primarycause_linea"],
            lambda x, y: ((x or "") + " " + (y or "")) or None,
            None,
        )
        .combine(
            dff["primarycause_lineb"],
            lambda x, y: ((x or "") + " " + (y or "")) or None,
            None,
        )
        .combine(
            dff["primarycause_linec"],
            lambda x, y: ((x or "") + " " + (y or "")) or None,
            None,
        )
    ).apply(lambda x: x.strip() if x else None)
    return dff


def get_sacramento_records(config: models.DataSource) -> list[dict[str, typing.Any]]:
    """Get records from Sacramento.

    We use this custom function since we are able to get the records directly via
    a URL, but we need to parse the structure after and the url is not in the
    open data portal format.
    """
    console.log(f"Fetching {config.name} records...")
    response = requests.get(config.url)
    data: dict[str, typing.Any] = response.json()
    if "features" not in data:
        raise ValueError(
            f"Unable to get records from {config.url}, `features` key not in response"
        )
    if len(data["features"]) == 0:
        raise ValueError(f"No records found in {config.url}")
    return [r["attributes"] for r in data["features"]]


def get_pima_records(config: models.DataSource) -> list[dict[str, typing.Any]]:
    """Get records from Pima.

    We use this function to load the locally saved Pima records.
    """
    console.log(f"Fetching {config.name} records...")
    df = pd.read_csv(
        Path().cwd() / "data" / "pima_records.csv", low_memory=False
    ).drop_duplicates()

    return df.to_dict(orient="records")


def get_sync_records(config: models.DataSource, current_index: int) -> int:
    """Get records from url synchronously.

    This is a synchronous function to get records from a url for each dataset.

    Args:
        config: DataSource object

    Returns:
        int: newly updated index
    """
    if config.name == "Sacramento County":
        records = get_sacramento_records(config)
    elif config.name == "Pima County":
        records = get_pima_records(config)
    else:
        records = get_open_data_records(config)
    df = make_df_with_identifier(records, current_index)
    if config.name == "Cook County":
        # create composite drug column
        df = cook_county_drug_col(df)
    export_drug_df(df, config)
    export_jsonlines_from_df(df, config)
    return len(records)


async def run(settings: models.Settings, update_remote: bool = False) -> None:
    """Fetch records from open data portal.

    Args:
        settings (models.Settings): Settings object
        update_remote (bool): whether to update the remote config.json or not

    """
    total_records = 0
    for data_source in settings.sources:
        if data_source.is_async:
            record_count = await get_async_records(
                config=data_source, current_index=total_records
            )
            data_source.total_records = record_count
            total_records += record_count
        else:
            record_count = get_sync_records(
                config=data_source, current_index=total_records
            )
            data_source.total_records = record_count
            total_records += record_count

    console.log(f"Total records fetched: {total_records:,}")

    if update_remote:
        manage_config.update_remote_config(config=settings)
    else:
        manage_config.update_local_config(config=settings)


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    asyncio.run(run(settings=settings))
