"""This module extracts drugs from the records.

It utilizes the drug columns (in order) listed in the config file (config.json).

It also requires you to have the [drug extraction tool](https://github.com/UK-IPOP/drug-extraction) installed.
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path
from typing import Any, Generator

import orjson
import pandas as pd
import requests

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
    # data = resp.json()
    Path("search_terms.csv").write_text(resp.text)


def command(input_fpath: str, target_columns: list[str] | str) -> list[str]:
    """Build the command to run the drug extraction tool.

    Args:
        input_fpath (str): path to the input file
        target_columns (list[str] | str): the column(s) to search

    Returns:
        list[str]: the command (list) to run
    """
    cmd = [
        "uvx",
        "extract-drugs",
        "search",
        "--data-file",
        input_fpath,
        "--id-col",
        # we made this column when we fetched the data
        "CaseIdentifier",
    ]
    if isinstance(target_columns, str):
        cmd.extend(["--search-cols", target_columns])
    else:
        for col in target_columns:
            cmd.extend(["--search-cols", col])
    return cmd


def read_drug_output(source: str) -> Generator[dict[str, str], None, None]:
    """Read the drug output file and yield each record."""
    with open(Path().cwd() / "output.csv", "r") as f:
        reader = csv.DictReader(f)
        for line in reader:
            line["data_source"] = source
            yield line


def run_drug_tool(config: models.DataSource) -> list[dict[str, Any]]:
    """Run the drug extraction tool.

    Args:
        config (models.DataSource): the data source config

    Returns:
        list[dict[str, Any]]: the drug results
    """
    drug_results: list[dict[str, Any]] = []

    in_file = Path("data") / config.drug_prep_filename
    cmd = command(
        input_fpath=in_file.as_posix(),
        target_columns=config.drug_columns,
    )
    console.log(
        f"Running drug extraction tool on {config.drug_columns} for {config.name}"
    )
    # output is written to file
    subprocess.run(cmd)
    # so now we read the file using generators
    # could code this better
    for record in read_drug_output(config.name):
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
        .to_csv(Path("data") / "drug_output.csv", index=False)
    )


def run(settings: models.Settings) -> None:
    """Run the drug extraction tool."""
    fetch_drug_search_terms()

    drug_results: list[dict[str, Any]] = []
    for data_source in settings.sources:
        results = run_drug_tool(config=data_source)
        drug_results.extend(results)

    console.log("Exporting drug data...")
    export_drug_output(drug_results=drug_results)


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    run(settings=settings)
