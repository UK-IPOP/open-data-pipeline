from pathlib import Path

import geopandas
import pandas as pd

from opendata_pipeline import manage_config, models
from opendata_pipeline.utils import console


def read_records(config: models.DataSource) -> pd.DataFrame:
    """Read the records from the wide-form dataset.

    Args:
        config: The data source config.

    Returns:
        df: The wide-form joined records.
    """
    df: pd.DataFrame = pd.read_csv(
        Path("data") / config.temp_wide_filename, low_memory=False
    )
    return df


def apply_composite_lat_long(
    row, config: models.GeoConfig
) -> tuple[str | None, str | None]:
    """Apply the composite latitude and longitude to the dataframe."""
    lat_val = row[config.lat_field.lower().replace(" ", "_")]
    lon_val = row[config.lon_field.lower().replace(" ", "_")]
    if pd.notna(lat_val) and pd.notna(lon_val):
        if isinstance(lat_val, str):
            x = lat_val.replace(" ", "", -1)
            if "," in x:
                lat, lon = x.split(",")
                return lat, lon
            else:
                return None, None
        else:
            return lat_val, lon_val
    # fields that may exist in the data
    if "geocoded_latitude" not in row or "geocoded_longitude" not in row:
        return None, None
    elif pd.notna(row["geocoded_latitude"]) and pd.notna(row["geocoded_longitude"]):
        return row["geocoded_latitude"], row["geocoded_longitude"]
    else:
        return None, None


def configure_source_data(df: pd.DataFrame, config: models.GeoConfig) -> pd.DataFrame:
    """Configure the source data for the spatial joins."""
    coordinates = df.apply(lambda row: apply_composite_lat_long(row, config), axis=1)
    dff = df.copy()
    dff["composite_latitude"] = coordinates.apply(lambda x: x[0])
    dff["composite_longitude"] = coordinates.apply(lambda x: x[1])
    return dff


def convert_to_geodataframe(df: pd.DataFrame) -> geopandas.GeoDataFrame:
    """Convert the dataframe to a geodataframe using lat/long."""
    geo_df = geopandas.GeoDataFrame(
        data=df,
        geometry=geopandas.points_from_xy(
            df["composite_longitude"],
            df["composite_latitude"],
            crs="EPSG:4326",
        ),
    )
    return geo_df


def fetch_tracts(fips_code: str) -> geopandas.GeoDataFrame:
    """Fetch Census Tracts geodataframes

    Args:
        fips_code (str): The Census FIPS Code (i.e. 17 for Illinois)

    Returns:
        geopandas.GeoDataFrame: The census tracts geodataframe
    """
    url = f"https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_{fips_code}_tract.zip"
    dataset: geopandas.GeoDataFrame = geopandas.read_file(url).to_crs("EPSG:4326")
    return dataset


def run(config: models.Settings) -> None:
    """Run the spatial join.
    Args:
        config (models.Settings): The settings for the app.
    """
    for data_source in config.sources:
        tracts_geodf = fetch_tracts(fips_code=data_source.state_fips_code)
        if data_source.spatial_config is None:
            console.log(f"{data_source.name} needs no spatial joining")
            console.log("Writing to file...")
            pd.read_csv(
                Path("data") / data_source.temp_wide_filename, low_memory=False
            ).to_csv(Path("data") / data_source.wide_form_filename, index=False)
            continue
        console.log(f"Spatially joining {data_source.name}")
        records = read_records(data_source)
        df = pd.DataFrame(records)
        df = configure_source_data(df, data_source.spatial_config)
        geo_df = convert_to_geodataframe(df)
        console.log(
            f"Starting shape -> Rows: {geo_df.shape[0]} Columns: {geo_df.shape[1]}"
        )
        geo_df = geopandas.sjoin(geo_df, tracts_geodf, how="left", predicate="within")
        console.log(
            f"Updated shape -> Rows: {geo_df.shape[0]} Columns: {geo_df.shape[1]}"
        )

        console.log("Writing to file...")
        geo_df.to_csv(Path("data") / data_source.wide_form_filename, index=False)
        console.log("Done!")


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    run(config=settings)
