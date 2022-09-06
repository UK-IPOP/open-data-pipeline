from __future__ import annotations
import csv

import datetime
import enum
from typing import Optional
from pydantic import validator
from sqlmodel import Field, SQLModel
import orjson


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


def is_sealed(x: str) -> bool:
    if x.upper() == "SEALED CASE":
        return True
    return False


class CookCountyRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    objectid: Optional[int]
    casenumber: str = Field(..., index=True)
    incident_date: Optional[datetime.datetime]
    death_date: Optional[datetime.datetime]
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
        return value

    def text_for_search(self, primary: bool) -> str:
        if primary:
            pc = self.primarycause or ""
            pc_linea = self.primarycause_linea or ""
            pc_lineb = self.primarycause_lineb or ""
            pc_linec = self.primarycause_linec or ""
            return f"{pc} {pc_linea} {pc_lineb} {pc_linec}".strip()
        else:
            sc = self.secondarycause or ""
            return sc.strip()


class SanDiegoCountyRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    row_number: int = Field(..., index=True)
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
        return value

    @validator("res_city")
    def parse_res_city(cls, value: str):
        return value.title()

    @validator("death_zip", pre=True)
    def parse_death_zip(cls, value: str):
        if not value.isnumeric():
            return None
        if int(value) < 0:
            return None
        return value

    # i can't remember but this needs the trailing underscore for some reason
    @validator("coronado_bridge_related_suicide_cases_", pre=True)
    def parse_coronado_bridge(cls, value: str):
        if is_sealed(value):
            return None
        return value

    def text_for_search(self, primary: bool) -> str:
        if primary:
            return f"{self.cod_string or ''}".strip()
        else:
            return f"{self.how_injury_occurred or ''}".strip()


class Source(enum.Enum):
    COOK_COUNTY = "cook_county"
    SAN_DIEGO = "san_diego"


class DrugRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    record_id: str = Field(..., index=True)
    edits: int
    similarity: float
    search_term: str
    matched_term: str
    tags: str
    # can try to add primary flag eventually

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


# the point of this is to take data from the various records and unify the format
# for the drug tool
class DrugInput(SQLModel):
    case_identifier: str | int
    text: str
    data_source: Source

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        use_enum_values = True


class GeocodeResult(SQLModel):
    latitude: float
    longitude: float
    address: str
    score: float
    status: str
    record_id: str
