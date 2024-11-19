"""This module contains the logic for analyzing the data.

It is responsible for combining the data from the different sources and
converting into wide format for analysis.

You can actually run this as a script directly from the command line if you cloned the repo.
"""

from collections import defaultdict
from pathlib import Path

import pandas as pd

from opendata_pipeline import manage_config, models
from opendata_pipeline.utils import console


def read_geocoded_data(source: models.DataSource) -> pd.DataFrame:
    """Reads the geocoded data from the data directory.

    Sets the index to `CaseIdentifier`, and handles some minor column renaming.

    Only returns the data for the given source (i.e. filtered).

    Args:
        source (models.DataSource): The source to read.

    Returns:
        pd.DataFrame: The geocoded data.
    """
    # expects geocoding to be done and file to be in
    # data/geocoded_data.jsonl
    # returns filtered data to save memory
    df = pd.read_json(
        Path("data") / "geocoded_data.jsonl",
        lines=True,
        orient="records",
        typ="frame",
    ).set_index("CaseIdentifier")
    # column we set to data source name --> `data_source`
    filt_df = df[df["data_source"] == source.name].drop(columns=["data_source"])
    dff = filt_df.rename(columns={col: f"geocoded_{col}" for col in filt_df.columns})
    return dff


def read_drug_data(source: models.DataSource) -> pd.DataFrame:
    """Reads the drug data from the data directory.

    Sets the index to `CaseIdentifier`/`record_id`, and handles some minor column renaming.

    Only returns the data for the given source (i.e. filtered).

    Args:
        source (models.DataSource): The source to read.

    Returns:
        pd.DataFrame: The drug data.
    """
    df = (
        pd.read_json(
            Path("data") / "drug_data.jsonl",
            lines=True,
            orient="records",
            typ="frame",
        )
        .rename(columns={"row_id": "CaseIdentifier"})
        .set_index("CaseIdentifier")
    )
    # column we set to data source name --> `data_source`
    filt_df = df[df["data_source"] == source.name].copy()
    return filt_df


def join_geocoded_data(base_df: pd.DataFrame, geo_df: pd.DataFrame) -> pd.DataFrame:
    """Joins the geocoded data to the base data.

    Merges on index

    Args:
        base_df (pd.DataFrame): The base data.
        geo_df (pd.DataFrame): The geocoded data.

    Returns:
        pd.DataFrame: The joined data.
    """
    # merge on index
    # expects CaseIdentifier to be the index
    merged_df = pd.merge(
        left=base_df,
        right=geo_df,
        how="left",
        left_index=True,
        right_index=True,
    )
    return merged_df


def read_records(source: models.DataSource) -> pd.DataFrame:
    """Reads the records from the data directory, sets index to `CaseIdentifier`."""
    df = pd.read_json(
        Path("data") / f"{source.records_filename}",
        lines=True,
        orient="records",
        typ="frame",
    ).set_index("CaseIdentifier")
    return df


def add_death_date_breakdowns(
    df: pd.DataFrame, source: models.DataSource
) -> pd.DataFrame:
    """Adds death date breakdowns to the data IN PLACE.

    Args:
        df (pd.DataFrame): The records dataframe.
        source (models.DataSource): The source config

    Returns:
        pd.DataFrame: The records dataframe with death date breakdowns added.
    """
    date_col = source.date_field
    # some sources are Unix timestamps
    if source.name in ("Milwaukee County", "Sacramento County"):
        df[date_col] = pd.to_datetime(df[date_col], unit="ms")
    else:
        df[date_col] = pd.to_datetime(df[date_col])

    # now add breakdowns with appropriate names
    df["death_day"] = df[date_col].dt.day
    df["death_month"] = df[date_col].dt.month_name()
    df["death_month_num"] = df[date_col].dt.month
    df["death_year"] = df[date_col].dt.year
    df["death_day_of_week"] = df[date_col].dt.day_name()
    df["death_day_is_weekend"] = df[date_col].dt.day_of_week > 4
    df["death_day_week_of_year"] = df[date_col].dt.isocalendar().week
    return df


def make_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Converts the drug data from long to wide format.

    Args:
        df (pd.DataFrame): The drug data.

    Returns:
        pd.DataFrame: The drug data in wide format.
    """
    # expects drug_df to have CaseIdentifier as index
    records: dict[str, dict[str, int]] = {}
    for row in df.reset_index().to_dict(orient="records"):
        # binary flag for each search term
        if row["CaseIdentifier"] not in records:
            records[row["CaseIdentifier"]] = defaultdict(int)
        records[row["CaseIdentifier"]][row["search_term"]] = 1
        # binary flag for search field
        # need to rename so doesn't overwrite on joining to source data
        records[row["CaseIdentifier"]][
            f"{row['search_field'].replace(' ', '_')}_matched"
        ] = 1
        # metadata binary flags, assumes metadata is pipe delimited
        # uses "group" to avoid potential column name conflicts
        if row["metadata"]:
            for meta in row["metadata"].split("|"):
                records[row["CaseIdentifier"]][f"{meta.upper()}_meta"] = 1

    flat_records = [{"CaseIdentifier": k, **v} for k, v in records.items()]
    wide_df = pd.DataFrame(flat_records).set_index("CaseIdentifier")
    return wide_df


def merge_wide_drugs_to_records(
    base_df: pd.DataFrame, wide_drug_df: pd.DataFrame
) -> pd.DataFrame:
    """Merges the wide drug data to the base data (on index).

    Args:
        base_df (pd.DataFrame): The base data.
        wide_drug_df (pd.DataFrame): The wide drug data.

    Returns:
        pd.DataFrame: The joined data.
    """
    # merge on index
    # expects CaseIdentifier to be the index for BOTH
    return pd.merge(
        left=base_df,
        right=wide_drug_df,
        left_index=True,
        right_index=True,
        how="left",
    )


def combine(
    base_df: pd.DataFrame,
    geo_df: pd.DataFrame,
    drug_df: pd.DataFrame,
) -> pd.DataFrame:
    """Combines the data into a single dataframe.

    This function calls `make_wide`, `merge_wide_drugs_to_records`, and `join_geocoded_data`.

    Args:
        base_df (pd.DataFrame): The base data.
        geo_df (pd.DataFrame): The geocoded data.
        drug_df (pd.DataFrame): The drug data.

    Returns:
        pd.DataFrame: The combined data.
    """
    wide_drug_df = make_wide(df=drug_df)
    records_wide_drugs = merge_wide_drugs_to_records(
        base_df=base_df, wide_drug_df=wide_drug_df
    )
    if geo_df.empty:
        return records_wide_drugs
    else:
        joined_df = join_geocoded_data(base_df=records_wide_drugs, geo_df=geo_df)
        return joined_df


def cleanup_columns(df: pd.DataFrame):
    """Cleans up the column names.

    Args:
        df (pd.DataFrame): The data.
    """
    # drop columns we don't need?
    # lowercase columns
    return df.rename(columns={col: col.lower().replace(" ", "_") for col in df.columns})


def handle_mil_eventdate(x: str):
    if pd.isna(x):
        return None
    else:
        try:
            return pd.to_datetime(x).strftime("%Y-%m-%d")
        except:
            try:
                return pd.to_datetime(x.split(" ")[0].strip()).strftime("%Y-%m-%d")
            except:
                return None


def run(settings: models.Settings) -> None:
    """Runs the data processing.

    Args:
        settings (models.Settings): The settings.
    """
    for data_source in settings.sources:
        records_df = read_records(source=data_source)
        console.log(
            f"Read {len(records_df)} records from {data_source.records_filename}"
        )

        add_death_date_breakdowns(df=records_df, source=data_source)
        # a little hard coding needed
        if data_source.name == "Milwaukee County":
            # overwrite column with cleaned up version
            records_df["EventDate"] = records_df["EventDate"].apply(
                handle_mil_eventdate
            )
        console.log("Added death date breakdowns to records")

        drug_df = read_drug_data(source=data_source)
        console.log(f"Read {len(drug_df)} drug records for {data_source.name}")

        geocoded_df = read_geocoded_data(source=data_source)
        if not geocoded_df.empty:
            console.log(
                f"Read {len(geocoded_df)} geocoded records for {data_source.name}"
            )

        # write a file for each analysis step for the data source
        # written into a folder for the data source so that we can zip
        data_dir = Path("data") / data_source.name.replace(" ", "_")
        data_dir.mkdir(exist_ok=True)
        records_df.reset_index().to_csv(data_dir / "records.csv", index=False)
        drug_df.reset_index().to_csv(data_dir / "drug.csv", index=False)
        if not geocoded_df.empty:
            geocoded_df.reset_index().to_csv(data_dir / "geocoded.csv", index=False)
        # eventually add spatial

        console.log("Combining data...")
        combined_df = combine(
            base_df=records_df,
            geo_df=geocoded_df,
            drug_df=drug_df,
        )
        console.log(f"Combined data has {combined_df.shape} shape")

        cleaned_df = cleanup_columns(df=combined_df)

        console.log("Writing combined data to csv...")
        cleaned_df.reset_index().to_csv(
            Path("data") / data_source.temp_wide_filename, index=False
        )


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    run(settings=settings)
