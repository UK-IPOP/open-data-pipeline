from __future__ import annotations

from pathlib import Path
from typing import Any
from arcgis import GIS
from arcgis.geocoding import geocode
from rich.progress import track
import orjson

from . import manage_config, models

# TODO: do we want to add average distance to other points?
# - this could be some sort of analysis of the data that is produced but not put in the file
# descriptive of distances

# FURTHER:
# the arcgis module seems to have the ability to do geocoding, spatial joins, and I'm sure distances
# should we just use this for everything?
# we also have the option of ArcPy
# let's just focus on geocoding for now

# each place needs a unique reader and cleaner since they have different column for the addresses
# we could read this in from a config file but that seems like overkill for now

# we would also ideally want batch geocoding to work
# # only returns 1 geocoder (without indexing) -- ArcGIS World GeoCoding Service
# geocoder = get_geocoders(gis)[0]

# # generally seems MAX batch size is 1000
# # but we can use `suggested` for now
# suggested_batch_size: int = geocoder.properties.locatorProperties.SuggestedBatchSize
# city sub???


def read_records(opts: models.DataSource) -> list[dict[str, Any]]:
    if opts.spatial_config is None:
        raise ValueError("spatial_config is required for geocoding")
    fields: list[str | None] = [
        "CaseIdentifier",
        opts.spatial_config.lat_field,
        opts.spatial_config.lon_field,
        opts.spatial_config.address_fields.street,
        opts.spatial_config.address_fields.city,
        opts.spatial_config.address_fields.state,
        opts.spatial_config.address_fields.zip,
    ]

    records: list[dict[str, Any]] = []
    with open(Path("data") / opts.records_filename, "r") as f:
        for line in f:
            line_data = orjson.loads(line)
            filtered_data = {
                k: v
                for k, v in line_data.items()
                if k in {f for f in fields if f is not None}
            }
            lat_value = filtered_data[opts.spatial_config.lat_field]
            lon_value = filtered_data[opts.spatial_config.lon_field]
            street_value = filtered_data[opts.spatial_config.address_fields.street]
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
    """Clean street."""
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
    record: dict[str, Any], opts: models.DataSource
) -> tuple[Any, dict[str, Any]] | None:
    if opts.spatial_config is None:
        raise ValueError("spatial_config is required for geocoding")

    address_config = opts.spatial_config.address_fields
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
    with open(Path("data") / "geocoded_data.jsonl", "w") as f:
        for record in data:
            f.write(orjson.dumps(record).decode("utf-8") + "\n")


def run(settings: models.Settings, alternate_key: str | None) -> None:
    if settings.arcgis_api_key is None and alternate_key is None:
        raise ValueError(
            "arcgis_api_key is required for geocoding. Consider using the --alternate-key flag"
        )
    # initialize ARCGIS
    if settings.arcgis_api_key is not None:
        GIS(api_key=settings.arcgis_api_key)
    elif alternate_key is not None:
        GIS(api_key=alternate_key)
    else:
        raise ValueError("arcgis_api_key is required for geocoding")

    geocoded_results: list[dict[str, Any]] = []
    for data_source in settings.sources:
        print(data_source)

        if data_source.needs_geocoding:
            if data_source.spatial_config is None:
                raise ValueError("spatial_config is required for geocoding")
            records = read_records(data_source)
            for record in track(
                records,
                description=f"Geocoding {data_source.name}",
                total=len(records),
            ):
                address_data = prepare_address(record, data_source)
                if address_data is None:
                    continue
                case_id, address_dict = address_data
                geocoded_resp = geocode(
                    address_dict,
                    search_extent=data_source.spatial_config.bounds.dict(),  # type: ignore
                    location_type="rooftop",
                    match_out_of_range=False,
                )
                if geocoded_resp:
                    best_result = geocoded_resp[0]  # type: ignore
                    geo_data = {
                        "CaseIdentifier": case_id,
                        "Latitude": best_result["location"]["y"],
                        "Longitude": best_result["location"]["x"],
                        "Score": best_result["score"],
                        "MatchAddress": best_result["address"],
                    }
                    geocoded_results.append(geo_data)

            # this diffrence is due to cleaning
            print(f"geocoded {len(geocoded_results)} records out of {len(records)}")

    export_geocoded_results(geocoded_results)


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    run(settings=settings, alternate_key=None)
