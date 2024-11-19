"""This module handles geocoding of records.

It utilizes the ArcGIS geocoding API and asyncio to speed up the process.
"""

from __future__ import annotations

import asyncio
import urllib.parse
from pathlib import Path
from typing import Any

import httpx
import orjson
from rich.progress import track

from opendata_pipeline import manage_config, models
from opendata_pipeline.utils import console


def read_records(config: models.DataSource) -> list[dict[str, Any]]:
    """Read records from file.

    Only reads records that have not been geocoded.

    Only return fields that are needed for geocoding.
    """
    console.log(f"Reading records from file for {config.name}")
    if config.spatial_config is None:
        raise ValueError("spatial_config is required for geocoding")
    fields: list[str | None] = [
        "CaseIdentifier",
        config.spatial_config.lat_field,
        config.spatial_config.lon_field,
        config.spatial_config.address_fields.street,
        config.spatial_config.address_fields.city,
        config.spatial_config.address_fields.state,
        config.spatial_config.address_fields.zip,
    ]

    records: list[dict[str, Any]] = []
    with open(Path("data") / config.records_filename, "r") as f:
        for line in f:
            line_data = orjson.loads(line)
            filtered_data = {
                k: v
                for k, v in line_data.items()
                if k in {f for f in fields if f is not None}
            }
            lat_value = filtered_data[config.spatial_config.lat_field]
            lon_value = filtered_data[config.spatial_config.lon_field]
            street_value = filtered_data[config.spatial_config.address_fields.street]
            # if value is 0 or None, we need to geocode
            # otherwise we can skip
            if (
                lat_value == 0
                or lon_value == 0
                or lat_value is None
                or lon_value is None
                or street_value is None
            ):
                records.append(filtered_data)
    return records


def clean_address_string(s: str) -> str | None:
    """Clean street.

    Removes any non-alphanumeric characters.

    Returns None if the string is empty after cleaning.

    Args:
        s (str): The string to clean.

    Returns:
        str | None: The cleaned string or None if the string is empty.
    """
    if s is None:
        return None
    s = s.lower().strip()
    if (
        "unk" in s
        or "n/a" in s
        or s == "same"
        or s == "none"
        or s == "undetermined"
        or s == "no scene"
    ):
        return None
    return s


def prepare_address(
    record: dict[str, Any], config: models.DataSource
) -> tuple[Any, dict[str, Any]] | None:
    """Prepare address for geocoding.

    Args:
        record (dict[str, Any]): The record to prepare.

    Returns:
        tuple[Any, dict[str, Any]] | None: The id and address data or None if the address is invalid.
    """
    if config.spatial_config is None:
        raise ValueError("spatial_config is required for geocoding")

    address_config = config.spatial_config.address_fields
    if address_config.street is None:
        raise ValueError("street field is required for geocoding")
    if address_config.city is None and address_config.zip is None:
        raise ValueError("city or zip field is required for geocoding")

    clean_street = clean_address_string(record[address_config.street])
    if clean_street is None:
        return None
    address_dict: dict[str, Any] = {}
    address_dict["Address"] = clean_street
    address_dict["City"] = (
        record[address_config.city] if address_config.city is not None else None
    )
    address_dict["State"] = (
        record[address_config.state] if address_config.state is not None else None
    )
    address_dict["ZIP"] = (
        record[address_config.zip] if address_config.zip is not None else None
    )
    return record["CaseIdentifier"], address_dict


def export_geocoded_results(data: list[dict[str, Any]]) -> None:
    """Export geocoded results to file."""
    with open(Path("data") / "geocoded_data.jsonl", "w") as f:
        for record in data:
            f.write(orjson.dumps(record).decode("utf-8") + "\n")


def build_url(
    bounds: models.GeoBounds, address_data: dict[str, str | int | None], key: str
) -> str:
    """Build the geocoding url.

    This uses the hardcoded `fat_url` and inserts the token (`key`) and then encodes the bounds and address data.

    Args:
        bounds (models.GeoBounds): The (rectangular) bounds to use for the geocoding.
        address_data (dict[str, str | int | None]): The address data to use for the geocoding.
        key (str): The ArcGIS token.

    Returns:
        str: The geocoding url.
    """
    fat_url = f"https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?f=json&outFields=none&outSR=4326&token={key}&forStorage=false&locationType=street&sourceCountry=USA&maxLocations=1&maxOutOfRange=false"

    # combines values that we have
    address_string = " ".join([str(v) for v in address_data.values() if v])

    # the string will get url encoded by requests, we needed to handle the data
    url_string = f"{fat_url}&searchExtent={urllib.parse.quote_plus(bounds.json())}&SingleLine={urllib.parse.quote_plus(address_string)}"
    return url_string


async def get_geo_result(
    client: httpx.AsyncClient,
    url: str,
    id_: int,
    data_source_name: str,
    retry_number: int = 0,
    max_retries: int = 5,
) -> dict[str, Any] | None:
    """Get the geocoding result from an async web request to ArcGIS.

    If the request returns 200, will retry.

    Will return None otherwise.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (str): The url to use for the request.
        id_ (int): The id of the record being geocoded.
        data_source_name (str): The name of the data source being geocoded.

    Returns:
        dict[str, Any] | None: The geocoding result or None if the request failed.
    """
    try:
        response = await client.get(url)
        # if returns error, try again
        if response.status_code != 200:
            if retry_number > max_retries:
                raise ValueError("Exceeded max_retries")
            print(
                f"Bad response code: {response.status_code} Retry: {retry_number}/{max_retries} ID: {id_} URL: {url}"
            )
            await asyncio.sleep(10)
            return await get_geo_result(
                client,
                url,
                id_,
                data_source_name,
                retry_number=retry_number + 1,
            )
        json_data = response.json()
        if results := json_data.get("candidates", None):
            best = results[0]
            return {
                "CaseIdentifier": id_,
                "latitude": best["location"]["y"],
                "longitude": best["location"]["x"],
                "score": best["score"],
                "matched_address": best["address"],
                "data_source": data_source_name,
            }
    except httpx.TimeoutException as te:
        print(
            f"Failed with timeout: {te} Retry: {retry_number}/{max_retries} ID: {id_}"
        )
        if retry_number > max_retries:
            raise ValueError("Exceeded max_retries")
        await asyncio.sleep(retry_number + 1 * 10)
        return await get_geo_result(
            client,
            url,
            id_,
            data_source_name,
            retry_number + 1,
            max_retries,
        )


async def geocode_records(config: models.DataSource, key: str) -> list[dict[str, Any]]:
    """Geocode records for the data source.

    Args:
        config (models.DataSource): The data source config.
        key (str): The ArcGIS token.

    Returns:
        list[dict[str, Any]]: The geocoded records.
    """
    records = read_records(config)
    if config.spatial_config is None:
        raise ValueError("spatial_config is required for geocoding")

    console.log(f"Geocoding {len(records)} records from {config.name}...")
    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(20)) as client:
        for record in track(records):
            data = prepare_address(record, config)
            if data is None:
                continue
            id_, address_data = data
            url = build_url(
                bounds=config.spatial_config.bounds, address_data=address_data, key=key
            )
            result: dict[str, Any] | None = await get_geo_result(
                client=client,
                url=url,
                id_=id_,
                data_source_name=config.name,
            )
            if result is not None:
                results.append(result)

    # this difference is due to cleaning
    print(f"Geocoded {len(results)} records out of {len(records)}")
    return results


async def run(settings: models.Settings, alternate_key: str | None) -> None:
    """Run the geocoding process."""
    if settings.arcgis_api_key is None and alternate_key is None:
        raise ValueError(
            "arcgis_api_key is required for geocoding. Consider using the --alternate-key flag"
        )
    # initialize ARCGIS
    if settings.arcgis_api_key is not None:
        key = settings.arcgis_api_key
    elif alternate_key is not None:
        key = alternate_key
    else:
        raise ValueError("arcgis_api_key is required for geocoding")

    geocoded_results: list[dict[str, Any]] = []
    for data_source in settings.sources:
        if data_source.needs_geocoding:
            source_set = await geocode_records(data_source, key)
            geocoded_results.extend(source_set)

    console.log(f"Exporting {len(geocoded_results)} geocoded records")
    export_geocoded_results(geocoded_results)


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    asyncio.run(run(settings, alternate_key=None))
