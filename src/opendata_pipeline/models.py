from __future__ import annotations

from pydantic import BaseSettings, Field, BaseModel, validator
import orjson
from pathlib import Path
from typing import Any, Optional


def json_config_settings_source(_: BaseSettings) -> dict[str, Any]:
    """
    A simple settings source that loads variables from a JSON file
    at the project's root.
    """
    return orjson.loads(Path("config.json").read_bytes())


class SpatialReference(BaseModel):
    wkid: int = Field(..., alias="wkid")


class GeoBounds(BaseModel):
    xmin: float = Field(..., description="Minimum longitude")
    xmax: float = Field(..., description="Maximum longitude")
    ymin: float = Field(..., description="Minimum latitude")
    ymax: float = Field(..., description="Maximum latitude")
    spatial_reference: SpatialReference = Field(..., description="Spatial reference")


class AddressFields(BaseModel):
    street: Optional[str] = Field(..., description="Street address")
    city: Optional[str] = Field(..., description="City")
    state: Optional[str] = Field(..., description="State")
    zip: Optional[str] = Field(..., description="Zip code")


class GeoConfig(BaseModel):
    lat_field: str = Field(..., description="Name of latitude field")
    lon_field: str = Field(..., description="Name of longitude field")
    address_fields: AddressFields = Field(..., description="List of address fields")
    bounds: GeoBounds = Field(..., description="Bounding box for geocoding")


class DataSource(BaseModel):
    name: str = Field(..., description="Name of the data source")

    url: str = Field(..., description="URL to the data source")
    total_records: int = Field(
        ...,
        description="Total number of records in the data source as of last run. ",
    )
    # only one of the below two can be true
    needs_pagination: bool = Field(
        ..., description="Whether or not the data source needs to be paginated"
    )
    is_open_data: bool = Field(
        ..., description="Whether or not the data source is OData compliant"
    )

    drug_columns: list[str] = Field(
        ..., description="Columns containing text data to search"
    )

    needs_geocoding: bool = Field(..., description="Does this dataset need geocoding?")
    spatial_config: Optional[GeoConfig] = Field(
        ..., description="Configuration for geocoding this dataset"
    )

    @validator("is_open_data")
    def validate_pagination_and_open_data(cls, v, values):
        if v and values["needs_pagination"]:
            raise ValueError(
                "Only one of needs_pagination and is_open_data can be True"
            )
        return v

    @validator("spatial_config")
    def validate_spatial_config(cls, v, values):
        if values["needs_geocoding"] and v is None:
            raise ValueError(
                "`spatial_config` must be provided if geocoding is set to True"
            )
        return v

    @property
    def is_async(self) -> bool:
        if self.needs_pagination:
            return True
        elif self.is_open_data:
            return False
        else:
            raise ValueError(
                f"Data source {self.name} is not supported. Must need pagination or be open data source"
            )

    @property
    def records_filename(self) -> str:
        return f"{self.name.replace(' ', '_').lower()}_records.jsonl"

    # TODO: remove this when we can read jsonlines in drug tool
    @property
    def drug_prep_filename(self) -> str:
        return f"{self.name.replace(' ', '_').lower()}_drug_prep.csv"

    @property
    def csv_filename(self) -> str:
        return f"{self.name.replace(' ', '_').lower()}_wide_form.csv"


# This should model config.yaml
class Settings(BaseSettings):
    arcgis_api_key: Optional[str] = Field(..., env="ARCGIS_API_KEY", read_only=True)
    github_token: Optional[str] = Field(..., env="GH_TOKEN", read_only=True)

    sources: list[DataSource] = Field(..., description="List of data sources")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

        # this is a typo in pydantic source code
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                env_settings,
                json_config_settings_source,
                init_settings,
                file_secret_settings,
            )


if __name__ == "__main__":
    print(Settings())  # type: ignore
