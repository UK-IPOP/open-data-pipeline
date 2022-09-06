# use this script to update the database with new records

import enum
import requests
from sqlmodel import create_engine, Session, SQLModel, select
from rich import print

import models


class TableNames(enum.Enum):
    COOK_COUNTY = "cook_county_records"
    SAN_DIEGO_COUNTY = "san_diego_county_records"


def fetch_new_cook_county_records():
    url = "https://datacatalog.cookcountyil.gov/resource/3trz-enys.json"
    payload = {
        "$limit": 100,
        "$order": "death_date DESC",
    }
    resp = requests.get(url, params=payload)
    data = [models.CookCountyRecord.parse_obj(row) for row in resp.json()]
    return data


def fetch_new_san_diego_county_records():
    url = "https://data.sandiegocounty.gov/resource/jkvb-n4p7.json"
    payload = {
        "$limit": 100,
        "$order": "death_date DESC",
    }
    resp = requests.get(url, params=payload)
    data = [models.SanDiegoCountyRecord.parse_obj(row) for row in resp.json()]
    return data


# we can make this a lot better
# 1. query db for ids before hand and only append NEW records
# 2. use config file to specify name of table
def update_records(db_conn, table_name: TableNames):
    match table_name:
        case TableNames.COOK_COUNTY:
            records = fetch_new_cook_county_records()
            with Session(db_conn) as session:
                current_records = (
                    session.exec(select(models.CookCountyRecord.casenumber))
                    .unique()
                    .all()
                )
                new_records = [
                    r for r in records if r.casenumber not in current_records
                ]
                if new_records:
                    session.add_all(new_records)
                    session.commit()
                    print(
                        f"[green]Added {len(new_records)} new records to {table_name}"
                    )
                else:
                    print(f"[yellow]No new records to add to {table_name.value}")
            return
        case TableNames.SAN_DIEGO_COUNTY:
            records = fetch_new_san_diego_county_records()
            with Session(db_conn) as session:
                current_records = (
                    session.exec(select(models.SanDiegoCountyRecord.row_number))
                    .unique()
                    .all()
                )
                new_records = [
                    r for r in records if r.row_number not in current_records
                ]
                if new_records:
                    session.add_all(new_records)
                    session.commit()
                    print(
                        f"[green]Added {len(new_records)} new records to {table_name}"
                    )
                else:
                    print(f"[yellow]No new records to add to {table_name.value}")
            return
        case _:
            raise ValueError("Invalid table name")


if __name__ == "__main__":
    sql_lite_db = "data/database.db"
    engine = create_engine(
        "postgresql://postgres:USA61kilos!@db.aesbbmdzdsvqzjjjtkrn.supabase.co:5432/postgres",
        echo=True,
    )
    SQLModel.metadata.create_all(engine)
    update_records(engine, TableNames.COOK_COUNTY)
    update_records(engine, TableNames.SAN_DIEGO_COUNTY)
