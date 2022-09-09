from pathlib import Path
import pandas as pd

from opendata_pipeline import manage_config, models


def read_geocoded_data(source: models.DataSource) -> pd.DataFrame:
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
    df = (
        pd.read_json(
            Path("data") / "drug_data.jsonl",
            lines=True,
            orient="records",
            typ="frame",
        )
        .rename(columns={"record_id": "CaseIdentifier"})
        .set_index("CaseIdentifier")
    )
    # column we set to data source name --> `data_source`
    filt_df = df[df["data_source"] == source.name].copy()
    return filt_df


def join_geocoded_data(base_df: pd.DataFrame, geo_df: pd.DataFrame) -> pd.DataFrame:
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
    df = pd.read_json(
        Path("data") / f"{source.records_filename}",
        lines=True,
        orient="records",
        typ="frame",
    ).set_index("CaseIdentifier")
    return df


def make_wide(df: pd.DataFrame) -> pd.DataFrame:
    # expects drug_df to have CaseIdentifier as index
    records: dict[str, dict[str, int]] = {}
    for row in df.reset_index().to_dict(orient="records"):
        case_id = row["CaseIdentifier"]
        if case_id not in records.keys():
            records[case_id] = {}

        # this encode the source column index (primary = 1, secondary = 2, etc)
        # and combines it with the search term (drug name)
        column_name = f"{row['search_term'].lower()}_{row['source_col_index'] + 1}"
        # set to 1 because we found it
        records[case_id][column_name] = 1

        for tag in row["tags"].split("|"):
            # set to 1 because we found it
            records[case_id][f"{tag}_tag"] = 1

    flat_records = [{"CaseIdentifier": k, **v} for k, v in records.items()]
    wide_df = pd.DataFrame(flat_records).set_index("CaseIdentifier")
    return wide_df


def merge_wide_drugs_to_records(
    base_df: pd.DataFrame, wide_drug_df: pd.DataFrame
) -> pd.DataFrame:
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
    wide_drug_df = make_wide(df=drug_df)
    records_wide_drugs = merge_wide_drugs_to_records(
        base_df=base_df, wide_drug_df=wide_drug_df
    )
    joined_df = join_geocoded_data(base_df=records_wide_drugs, geo_df=geo_df)
    return joined_df


def cleanup_columns(df: pd.DataFrame):
    # drop columns we don't need?
    # lowercase columns
    return df.rename(columns={col: col.lower().replace(" ", "_") for col in df.columns})


def extract_plot_data(df: pd.DataFrame):
    # extract data for plotting
    # expects combined df BEFORE cleanup_columns
    # return a list of dicts in chartjs format... expecting to write to json

    # return df
    pass


def run(settings: models.Settings, update_remote: bool) -> None:
    for data_source in settings.sources:
        print(data_source.name)

        records_df = read_records(source=data_source)
        print(records_df.shape)
        drug_df = read_drug_data(source=data_source)
        print(drug_df.shape)
        geocoded_df = read_geocoded_data(source=data_source)
        print(geocoded_df.shape)

        combined_df = combine(
            base_df=records_df,
            geo_df=geocoded_df,
            drug_df=drug_df,
        )
        print(combined_df.shape)

        # extract_plot_data(df=combined_df)
        # write plot_data

        cleaned_df = cleanup_columns(df=combined_df)
        # should be same as above
        print(cleaned_df.shape)

        # write to csv
        cleaned_df.reset_index().to_csv(
            Path("data") / data_source.csv_filename, index=False
        )


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    run(settings=settings, update_remote=False)
