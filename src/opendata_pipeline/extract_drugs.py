"""This module extracts drugs from the records.

It utilizes the drug columns (in order) listed in the config file (config.json).

It also requires you to have the [drug extraction tool](https://github.com/UK-IPOP/drug-extraction) installed.
"""
from __future__ import annotations
import csv
from pathlib import Path

from typing import Any, Generator
import orjson
import requests
import subprocess
import pandas as pd

from opendata_pipeline import manage_config, models
from opendata_pipeline.utils import console


def fetch_drug_search_terms() -> None:
    """Fetch drug search terms from the remote github repo.

    Returns:
        dict[str, str]: a dictionary of search terms and their tags
    """
    console.log("Fetching drug search terms from GitHub")
    url = "https://raw.githubusercontent.com/UK-IPOP/drug-extraction/main/data/search_terms.csv"
    resp = requests.get(url)
    data = resp.json()
    Path("search_terms.csv").write_text(resp.text)


def command(input_fpath: str, target_column: str) -> list[str]:
    """Build the command to run the drug extraction tool.

    Args:
        input_fpath (str): path to the input file
        target_column (str): the column to search

    Returns:
        list[str]: the command (list) to run
    """
    return [
        "extract-drugs",
        "search",
        "--data-file",
        input_fpath,
        "--search-cols",
        target_column,
        "--id-col",
        # we made this column when we fetched the data
        "CaseIdentifier",
    ]


def read_drug_output() -> Generator[dict[str, str], None, None]:
    """Read the drug output file and yield each record."""
    with open(Path().cwd() / "output.csv", "r") as f:
        reader = csv.DictReader(f)
        for line in reader:
            yield line


def run_drug_tool(config: models.DataSource) -> list[dict[str, Any]]:
    """Run the drug extraction tool.

    Args:
        config (models.DataSource): the data source config

    Returns:
        list[dict[str, Any]]: the drug results
    """
    drug_results: list[dict[str, Any]] = []

    for column_level, target_column in enumerate(config.drug_columns):
        # TODO: adjust this when we can read jsonlines in drug tool
        in_file = Path("data") / config.drug_prep_filename
        cmd = command(
            input_fpath=in_file.as_posix(),
            target_column=target_column,
        )
        # output is written to file

        console.log(
            f"Running drug extraction tool on {target_column} for {config.name}"
        )
        subprocess.run(cmd)
        # so now we read the file using generators
        # could code this better
        for record in read_drug_output():
            drug_results.append(record)

    return drug_results


def export_drug_output(drug_results: list[dict[str, Any]]) -> None:
    """Export the drug output to a file."""
    with open(Path("data") / "drug_data.jsonl", "w") as f:
        for record in drug_results:
            f.write(orjson.dumps(record).decode("utf-8") + "\n")

    (
        pd.DataFrame(drug_results)
        .rename(columns={"row_id": "CaseIdentifier"})
        .drop(columns=["source_col_index"])
        .to_csv(Path("data") / "drug_output.csv", index=False)
    )


def run(settings: models.Settings) -> None:
    """Run the drug extraction tool."""
    search_terms = fetch_drug_search_terms()

    drug_results: list[dict[str, Any]] = []
    for data_source in settings.sources:
        results = run_drug_tool(config=data_source)
        drug_results.extend(results)

    console.log("Exporting drug data...")
    export_drug_output(drug_results=drug_results)


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    run(settings=settings)
