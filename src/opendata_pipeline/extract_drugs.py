from __future__ import annotations
from pathlib import Path

from typing import Any, Generator
import orjson
import requests
import subprocess

from opendata_pipeline import manage_config, models


def fetch_drug_search_terms() -> dict[str, str]:
    url = "https://raw.githubusercontent.com/UK-IPOP/drug-extraction/main/de-workflow/data/drug_info.json"
    resp = requests.get(url)
    data = resp.json()
    return {k: "|".join(v) for k, v in data.items()}


def command(input_fpath: str, target_column: str, search_words: str) -> list[str]:
    return [
        "extract-drugs",
        "simple-search",
        input_fpath,
        "--target-column",
        target_column,
        "--id-column",
        # we made this column when we fetched the data
        "CaseIdentifier",
        "--search-words",
        search_words,
        "--algorithm",
        "osa",
        "--threshold",
        "0.9",
        "--format",
        "jsonl",
    ]


def read_drug_output() -> Generator[dict[str, Any], None, None]:
    with open("extracted_drugs.jsonl", "r") as f:
        for line in f:
            yield orjson.loads(line)


def enhance_drug_output(
    record: dict,
    target_column: str,
    column_level: int,
    data_source: str,
    tag_lookup: dict[str, str],
) -> Generator[dict[str, Any], None, None]:
    """Enhance drug output with additional columns."""
    record["data_source"] = data_source
    record["source_column"] = target_column
    record["source_col_index"] = column_level
    record["tags"] = tag_lookup[record["search_term"].lower()]
    yield record


def run_drug_tool(
    opts: models.DataSource, tag_lookup: dict[str, str]
) -> list[dict[str, Any]]:
    # mostly this is replicating de-workflow code but we don't want ALL of those features
    # and the added dependencies so we just rewrite it here
    terms = "|".join(tag_lookup.keys())

    drug_results: list[dict[str, Any]] = []

    for column_level, target_column in enumerate(opts.drug_columns):
        # TODO: adjust this when we can read jsonlines in drug tool
        in_file = Path("data") / opts.drug_prep_filename
        cmd = command(
            input_fpath=in_file.as_posix(),
            target_column=target_column,
            search_words=terms,
        )
        # output is written to file
        subprocess.run(cmd)
        # so now we read the file using generators
        # could code this better
        for record in read_drug_output():
            enhanced_records = enhance_drug_output(
                record=record,
                data_source=opts.name,
                target_column=target_column,
                column_level=column_level,
                tag_lookup=tag_lookup,
            )
            # consume generator
            for enhanced_record in enhanced_records:
                drug_results.append(enhanced_record)

    return drug_results


def export_drug_output(drug_results: list[dict[str, Any]]) -> None:
    with open(Path("data") / "drug_data.jsonl", "w") as f:
        for record in drug_results:
            f.write(orjson.dumps(record).decode("utf-8") + "\n")


def run(settings: models.Settings) -> None:
    search_terms = fetch_drug_search_terms()

    drug_results: list[dict[str, Any]] = []
    for data_source in settings.sources:
        print(data_source)
        results = run_drug_tool(opts=data_source, tag_lookup=search_terms)
        drug_results.extend(results)

    export_drug_output(drug_results=drug_results)


if __name__ == "__main__":
    settings = manage_config.get_local_config()
    run(settings=settings)
