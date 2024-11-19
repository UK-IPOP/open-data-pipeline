"""This is the most important module in the package and contains the
settings models and functions for loading and saving settings.

The settings are stored in a JSON file in the user's home directory.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SpatialReference(BaseModel):
    """The spatial reference for a dataset."""

    wkid: int = Field(..., alias="wkid")
    """The wkid for the spatial reference."""


class GeoBounds(BaseModel):
    """The geographic bounds for a dataset."""

    xmin: float = Field(..., description="Minimum longitude")
    """Minimum longitude."""
    xmax: float = Field(..., description="Maximum longitude")
    """Maximum longitude."""
    ymin: float = Field(..., description="Minimum latitude")
    """Minimum latitude."""
    ymax: float = Field(..., description="Maximum latitude")
    """Maximum latitude."""
    spatial_reference: SpatialReference = Field(..., description="Spatial reference")
    """The spatial reference for the bounds."""


class AddressFields(BaseModel):
    """The address fields for a dataset."""

    street: Optional[str] = Field(..., description="Street address")
    """Street address."""
    city: Optional[str] = Field(..., description="City")
    """City."""
    state: Optional[str] = Field(..., description="State")
    """State."""
    zip: Optional[str] = Field(..., description="Zip code")
    """Zip code."""


class GeoConfig(BaseModel):
    """The geocoding configuration for a dataset."""

    lat_field: str = Field(..., description="Name of latitude field")
    """Name of latitude field."""
    lon_field: str = Field(..., description="Name of longitude field")
    """Name of longitude field."""
    address_fields: AddressFields = Field(..., description="List of address fields")
    """List of address fields."""
    bounds: GeoBounds = Field(..., description="Bounding box for geocoding")
    """Bounding box for geocoding."""
    spatial_join: bool = Field(
        ...,
        description="Should this dataset be spatially joined to the county and census tract boundaries?",
    )
    """Should this dataset be spatially joined to the county and census tract boundaries?"""


class DataSource(BaseModel):
    """The data source configuration."""

    name: str = Field(..., description="Name of the data source")
    """Name of the data source."""

    url: str = Field(..., description="URL to the data source")
    """URL to the data source. Used to download the data."""
    total_records: int = Field(
        ...,
        description="Total number of records in the data source as of last run. ",
    )
    """Total number of records in the data source as of last run"""

    # only one of the below two can be true
    needs_pagination: bool = Field(
        ..., description="Whether or not the data source needs to be paginated"
    )
    """Whether or not the data source needs to be paginated"""
    is_open_data: bool = Field(
        ..., description="Whether or not the data source is OData compliant"
    )
    """Whether or not the data source is OData compliant"""

    drug_columns: list[str] = Field(
        ..., description="Columns containing text data to search"
    )
    """Columns containing text data to search (enumerated in order of priority)"""

    needs_geocoding: bool = Field(..., description="Does this dataset need geocoding?")
    """Does this dataset need geocoding?"""
    spatial_config: Optional[GeoConfig] = Field(
        ..., description="Configuration for geocoding this dataset"
    )
    """Configuration for geocoding this dataset"""

    date_field: str = Field(
        ..., description="Date field, usually death-date, to analyze for timeseries"
    )
    """Date column to analyze for timeseries"""

    state_fips_code: str = Field(..., description="The Census FIPS code for this state")
    """The Census FIPS code (with leading zeros when needed) for this State.

    Example: Illinois=17, Arizona=04

    Can find easily via Google search.
    """

    @validator("is_open_data")
    def validate_pagination_and_open_data(cls, v, values):
        """Validate that only one of the pagination and open data flags is set."""
        if v and values["needs_pagination"]:
            raise ValueError(
                "Only one of needs_pagination and is_open_data can be True"
            )
        return v

    @validator("spatial_config")
    def validate_spatial_config(cls, v, values):
        """Validate that the spatial config is set if geocoding is needed."""
        if values["needs_geocoding"] and v is None:
            raise ValueError(
                "`spatial_config` must be provided if geocoding is set to True"
            )
        return v

    @property
    def is_async(self) -> bool:
        """Whether or not the data source should be processed using async."""
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
        """The filename for the records file."""
        return f"{self.name.replace(' ', '_').lower()}_records.jsonl"

    # TODO: remove this when we can read jsonlines in drug tool
    @property
    def drug_prep_filename(self) -> str:
        """The filename for the drug prep file."""
        return f"{self.name.replace(' ', '_').lower()}_drug_prep.csv"

    @property
    def temp_wide_filename(self) -> str:
        """The filename for the wide-form CSV file."""
        return f"{self.name.replace(' ', '_').lower()}_temp.csv"

    @property
    def wide_form_filename(self) -> str:
        """The filename for the spatial join file."""
        return f"{self.name.replace(' ', '_').lower()}_wide_form.csv"


class Settings(BaseSettings):
    """The settings for the package."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    arcgis_api_key: Optional[str] = Field(None, alias="ARCGIS_API_KEY")
    """The ArcGIS API key for geocoding.

    Read from .env file or environment variable using `ARCGIS_API_KEY` variable.

    Required for geocoding.
    """
    github_token: Optional[str] = Field(None, alias="GH_TOKEN")
    """The GitHub token for uploading the data.

    Read from .env file or environment variable using `GH_TOKEN` variable.

    Required for updating remote config.
    """

    sources: list[DataSource] = Field(..., description="List of data sources")
    """List of data sources."""


if __name__ == "__main__":
    # tests local
    print(Settings.parse_file("config.json"))
