from pathlib import Path
import pandas as pd
import geopandas
from opendata_pipeline import manage_config, models
from opendata_pipeline.utils import console


def read_records(config: models.DataSource) -> pd.DataFrame:
    """Read the records from the wide-form dataset.

    Args:
        config: The data source config.

    Returns:
        df: The wide-form joined records.
    """
    df: pd.DataFrame = pd.read_csv(Path("data") / config.csv_filename, low_memory=False)
    return df


def apply_composite_lat_long(
    row, config: models.GeoConfig
) -> tuple[str | None, str | None]:
    """Apply the composite latitude and longitude to the dataframe."""
    lat_val = row[config.lat_field.lower()]
    lon_val = row[config.lon_field.lower()]
    if lat_val and lon_val:
        return lat_val, lon_val
    # fields that may exist in the data
    elif row["geocoded_latitude"] and row["geocoded_longitude"]:
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


def fetch_counties_and_tracts() -> tuple[
    geopandas.GeoDataFrame, geopandas.GeoDataFrame
]:
    """Fetch Counties and Census Tracts geodataframes

    Order returned:
        county, census
    """
    urls = [
        "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_17_cousub_500k.zip",  # county
        "https://www2.census.gov/geo/tiger/TIGER2021/TRACT/tl_2021_17_tract.zip",  # census tracts
    ]
    dataset1: geopandas.GeoDataFrame = geopandas.read_file(urls[0]).to_crs("EPSG:4326")
    dataset2: geopandas.GeoDataFrame = geopandas.read_file(urls[1]).to_crs("EPSG:4326")
    return dataset1, dataset2


def run(config: models.Settings) -> None:
    """Run the spatial join.
    Args:
        config (models.Settings): The settings for the app.
    """
    county_geodf, census_geodf = fetch_counties_and_tracts()
    for data_source in config.sources:
        if data_source.spatial_config is None:
            continue
        console.log(f"Spatially joining {data_source.name}")
        records = read_records(data_source)
        df = pd.DataFrame(records)
        df = configure_source_data(df, data_source.spatial_config)
        geo_df = convert_to_geodataframe(df)
        console.log(
            f"Starting shape -> Rows: {geo_df.shape[0]} Columns: {geo_df.shape[1]}"
        )
        for geo_source in [county_geodf, census_geodf]:
            geo_df = geopandas.sjoin(geo_df, geo_source, how="left", predicate="within")
            geo_df.drop(columns=["index_right"], inplace=True, errors="ignore")
            console.log(
                f"Updated shape -> Rows: {geo_df.shape[0]} Columns: {geo_df.shape[1]}"
            )

        console.log("Writing to file...")
        geo_df.to_csv(Path("data") / data_source.spatial_join_filename, index=False)
        console.log("Done!")


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    run(config=settings)
