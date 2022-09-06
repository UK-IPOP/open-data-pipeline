# Use this script to load the original data into the database for the FIRST time
# this is only really useful for testing the "update" feature where we add new records only

from sqlmodel import create_engine, Session, SQLModel
from rich import print

import models


def load_original_cook_county_records() -> list[models.CookCountyRecord]:
    with open("data/db/cook_county.jsonl", "r") as f:
        data = [models.CookCountyRecord.parse_raw(row) for row in f]
    return data


def load_original_san_diego_county_records() -> list[models.SanDiegoCountyRecord]:
    with open("data/db/san_diego_county.jsonl", "r") as f:
        data = [models.SanDiegoCountyRecord.parse_raw(row) for row in f]
    return data


if __name__ == "__main__":
    sql_lite_db = "data/database.db"
    engine = create_engine(f"sqlite:///{sql_lite_db}")
    SQLModel.metadata.create_all(engine)
    cook_county_records = load_original_cook_county_records()
    san_diego_county_records = load_original_san_diego_county_records()
    with Session(engine) as session:
        print("[cyan]Adding Cook County Records")
        session.add_all(cook_county_records)
        print("[cyan]Adding San Diego County Records")
        session.add_all(san_diego_county_records)
        print("[cyan]Committing Records to DB...")
        session.commit()
    print("[green]Done")
