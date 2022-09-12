from __future__ import annotations

from pathlib import Path
import typing
import requests
import pandas as pd
import aiohttp
import asyncio
from rich.progress import track


from opendata_pipeline import manage_config, models


# this pattern of accessing "value" is common to all opendata api responses
def get_open_data_records(
    opts: models.DataSource,
) -> list[dict[str, typing.Any]]:
    """Get records from open data portal."""
    # we add 1000 assuming there were more records than last week
    payload = {"$top": opts.total_records + 1_000}
    response = requests.get(opts.url, params=payload)
    data: dict[str, typing.Any] = response.json()
    if "value" not in data:
        raise ValueError(
            f"Unable to get records from {opts.url}, `value` key not in response"
        )
    return data["value"]


def build_url(offset: int, base_url: str) -> str:
    """Build url for pagination."""
    # add 1000 record limit and offset params
    return f"{base_url}&resultRecordCount=1000&resultOffset={offset}"


# this pattern of accessing "features" and "attributes" is specific to MIL
# it may be common to other ARC GIS APIs but until we have more examples
# we will keep this function here
async def get_record_set(
    session: aiohttp.ClientSession, url: str
) -> list[dict[str, typing.Any]]:
    async with session.get(url) as resp:
        # if returns error, try again
        if resp.status != 200:
            return await get_record_set(session, url)
        resp_data: dict[str, typing.Any] = await resp.json()
        if "features" in resp_data:
            if len(resp_data["features"]) == 0:
                return []
            return [r["attributes"] for r in resp_data["features"]]
    return await get_record_set(session, url)


def make_df_with_identifier(
    records: list[dict[str, typing.Any]], current_index: int
) -> pd.DataFrame:
    """Make dataframe with case identifier."""
    df = pd.DataFrame(records)
    df["CaseIdentifier"] = df.index + current_index
    return df


# TODO: remove this when we can read jsonlines in drug tool
def export_drug_df(df: pd.DataFrame, opts: models.DataSource) -> None:
    """Export drug dataframe to csv."""
    target_cols = ["CaseIdentifier"] + opts.drug_columns
    out_path = Path("data") / opts.drug_prep_filename
    df.loc[:, target_cols].to_csv(out_path, index=False)


def export_jsonlines_from_df(df: pd.DataFrame, opts: models.DataSource) -> None:
    """Export jsonlines from dataframe."""
    out_path = Path("data") / opts.records_filename
    df.to_json(out_path, orient="records", lines=True)


async def get_async_records(opts: models.DataSource, current_index: int) -> int:
    async with aiohttp.ClientSession() as session:
        tasks = []
        # we add 2000 assuming there were more records than last week
        for offset in range(0, opts.total_records + 2000, 1000):
            url = build_url(base_url=opts.url, offset=offset)
            tasks.append(asyncio.ensure_future(get_record_set(session, url)))

        records = []
        for task in track(
            asyncio.as_completed(tasks),
            description="Fetching async records...",
            total=len(tasks),
        ):
            record_set = await task
            records.extend(record_set)

        print(f"Fetched {len(records):,} records asynchronously from {opts.url}")

        df = make_df_with_identifier(records, current_index)
        export_drug_df(df, opts)
        export_jsonlines_from_df(df, opts)
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


def get_sync_records(opts: models.DataSource, current_index: int) -> int:
    records = get_open_data_records(opts)
    df = make_df_with_identifier(records, current_index)
    if opts.name == "Cook County":
        # create composite drug column
        df = cook_county_drug_col(df)
    export_drug_df(df, opts)
    export_jsonlines_from_df(df, opts)
    return len(records)


async def run(settings: models.Settings, update_remote: bool = False) -> None:
    """Fetch records from open data portal."""
    total_records = 0
    for data_source in settings.sources:
        print(data_source)
        if data_source.is_async:
            record_count = await get_async_records(
                opts=data_source, current_index=total_records
            )
            data_source.total_records = record_count
            total_records += record_count
        else:
            record_count = get_sync_records(
                opts=data_source, current_index=total_records
            )
            data_source.total_records = record_count
            total_records += record_count

    print(f"Total records fetched: {total_records:,}")

    if update_remote:
        manage_config.update_remote_config(config=settings)
    else:
        manage_config.update_local_config(config=settings)


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    asyncio.run(run(settings=settings))
