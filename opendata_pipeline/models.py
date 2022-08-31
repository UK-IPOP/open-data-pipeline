from __future__ import annotations
import csv

import datetime
from typing import Optional
from pydantic import BaseModel, validator
import orjson


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


def is_sealed(x: str) -> bool:
    if x.upper() == "SEALED CASE":
        return True
    return False


class CookLocation(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]
    needs_recoding: bool


class Cook(BaseModel):
    objectid: Optional[int]
    casenumber: str
    incident_date: Optional[datetime.datetime]
    death_date: Optional[datetime.datetime]
    location: Optional[CookLocation]
    longitude: Optional[float]
    latitude: Optional[float]
    commissioner_district: Optional[int]
    primarycause: Optional[str]
    primarycause_linea: Optional[str]
    primarycause_lineb: Optional[str]
    primarycause_linec: Optional[str]
    secondarycause: Optional[str]
    manner: Optional[str]
    race: Optional[str]
    gender: Optional[str]
    age: Optional[int]
    latino: Optional[bool]
    incident_street: Optional[str]
    incident_city: Optional[str]
    incident_zip: Optional[int]
    residence_city: Optional[str]
    residence_zip: Optional[int]
    opioids: Optional[bool]
    covid_related: Optional[bool]
    gunrelated: Optional[bool]
    chi_commarea: Optional[str]
    chi_ward: Optional[float]
    is_processed: bool = False

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps

    @validator("incident_zip", pre=True)
    def parse_incident_zip(cls, value: str):
        if not value.isnumeric():
            return None


class SanDiego(BaseModel):
    row_number: int
    year: Optional[int]
    quarter: Optional[str]
    age_in_years: Optional[int]
    death_date: Optional[datetime.datetime]
    security_status: Optional[str]
    gender: Optional[str]
    race: Optional[str]
    ethnic_group: Optional[str]
    manner: Optional[str]
    manner_type_standardized_: Optional[str]
    opioid_related: Optional[str]
    coronado_bridge_related_suicide_cases_: Optional[bool]
    cod_string: Optional[str]
    how_injury_occurred: Optional[str]
    event_date: Optional[datetime.date]
    event_time: Optional[datetime.time]
    event_place: Optional[str]
    event_place_type: Optional[str]
    death_place: Optional[str]
    death_place_type: Optional[str]
    death_city: Optional[str]
    death_zip: Optional[int]
    res_city: Optional[str]
    res_zip: Optional[int]
    age_group_option_1: Optional[str]
    age_group_option_2: Optional[str]
    age_group_option_3: Optional[str]
    is_processed: bool = False

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps

    @validator("event_date", pre=True)
    def parse_event_date(cls, value: str):
        if is_sealed(value):
            return None
        return datetime.datetime.strptime(value, "%m/%d/%Y").date()

    @validator("event_time", pre=True)
    def parse_event_time(cls, value: str):
        if is_sealed(value):
            return None
        return datetime.datetime.strptime(value, "%I:%M:%S %p").time()

    @validator("res_zip", pre=True)
    def parse_res_zip(cls, value: str):
        if not value.isnumeric():
            return None
        if int(value) < 0:
            return None

    @validator("res_city")
    def parse_res_city(cls, value: str):
        return value.title()

    @validator("death_zip", pre=True)
    def parse_death_zip(cls, value: str):
        if not value.isnumeric():
            return None
        if int(value) < 0:
            return None

    @validator("coronado_bridge_related_suicide_cases_", pre=True)
    def parse_coronado_bridge(cls, value: str):
        if is_sealed(value):
            return None


class Milwaukee(BaseModel):
    ...


class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    address: str
    score: float
    status: str
    record_id: str


class DrugResult(BaseModel):
    record_id: str | int
    edits: int
    similarity: float
    search_term: str
    matched_term: str
    tags: str


class DrugInput(BaseModel):
    # these will become cols in a csv
    case_identifier: str | int
    text: str
    data_source: str
    # can add col to distinguish between primary/secondary search if wanted/needed


def prepare_drug_input(record: SanDiego | Cook) -> list[DrugInput] | None:
    if isinstance(record, SanDiego):
        results: list[DrugInput] = []
        if record.cod_string:
            results.append(
                DrugInput(
                    case_identifier=record.row_number,
                    text=record.cod_string,
                    data_source="sandiego",
                )
            )
        if record.how_injury_occurred:
            results.append(
                DrugInput(
                    case_identifier=record.row_number,
                    text=record.how_injury_occurred,
                    data_source="sandiego",
                )
            )
        return results if results else None
    elif isinstance(record, Cook):
        results: list[DrugInput] = []
        primary_text = " ".join(
            [
                x
                for x in [
                    record.primarycause,
                    record.primarycause_linea,
                    record.primarycause_lineb,
                    record.primarycause_linec,
                ]
                if x
            ]
        ).strip()
        if primary_text:
            results.append(
                DrugInput(
                    case_identifier=record.casenumber,
                    text=primary_text,
                    data_source="cook",
                )
            )
        if record.secondarycause:
            results.append(
                DrugInput(
                    case_identifier=record.casenumber,
                    text=record.secondarycause,
                    data_source="cook",
                )
            )
        return results if results else None
    else:
        raise ValueError(f"Unexpected type for record: {type(record)}")


def drug_input_to_csv(data: list[DrugInput], filename: str):
    records = [d.dict() for d in data if d]
    with open(filename, "w") as f:
        csvwriter = csv.DictWriter(f, fieldnames=records[0].keys())
        csvwriter.writeheader()
        for record in records:
            csvwriter.writerow(record)
