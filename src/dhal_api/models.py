from enum import Enum

from pydantic import BaseModel, field_validator


class DataType(str, Enum):
    """Class for dataset formats InVEST can request."""
    raster = 'raster'
    vector = 'vector'
    table = 'table'


class LicenseInfo(BaseModel):
    """Class for a dataset's license information."""
    id: str | None = None
    title: str | None = None
    url: str | None = None


class SearchParams(BaseModel):
    """Class for an InVEST input search."""
    tags: list[str]
    """List of keywords from a shared vocabulary between InVEST and the Data Hub."""
    datatype: DataType
    """The file format. One of: raster, vector, or table."""
    extent: list[float] | None = None
    """A 4-element iterable of [minx, miny, maxx, maxy] in EPSG:4326.
    Extent must not include inf or -inf.
    """
    sibling: str | None = None
    """The relation tag linking two inputs."""

    @field_validator('extent')
    def validate_extent_length(cls, v):
        if len(v) != 4:
            raise ValueError('extent must be a list of length 4')
        return v

    @field_validator('extent')
    def validate_extent_infinity(cls, v):
        # CKAN spatial search 404s on infinity, after a long wait.
        if float('inf') in v or -float('inf') in v:
            raise ValueError('extent cannot include infinity')
        return v


class DatasetSearchResult(BaseModel):
    """Class containing details of a Data Hub dataset."""
    dataset_url: str
    """The URL of the dataset."""
    source_catalog_url: str
    """The URL to the Package containing the dataset on the Hub."""
    name: str
    """The dataset name."""
    description: str
    """The dataset description."""
    extent: list[float] | None = None
    """A 4-element iterable of [minx, miny, maxx, maxy] in EPSG:4326"""
    pixel_size: list[float] | None = None
    """A 2-element iterable representing the width and height of a pixel in crs_units.
    This value will always be None for non-raster datasets.
    """
    crs_wkt: str | None = None
    """The Well-Known Text string representation of the dataset's CRS."""
    crs_units: str | None = None
    """Units of measure for coordinates in the CRS."""
    tags: list[str]
    """All non-vocabulary tags associated with the dataset."""
    places: list[str]
    """Place vocabulary tags associated with the dataset."""
    collection: list[str]
    """The Collections the dataset is a part of. To be used as the
    `sibling` input in a related search, when relevant.
    """
    license: LicenseInfo
    """Dict containing the license id, title, and url."""
    author: str
    """The dataset author."""
    created: str
    """The dataset's ``metadata_created`` date."""
    last_updated: str
    """The dataset's ``metadata_modified`` date."""


class SearchResponse(BaseModel):
    """Class for search results, including both result count and datasets."""
    count: int
    """The number of returned search results."""
    datasets: list[DatasetSearchResult]
    """List of DatasetSearchResult objects representing relevant search results."""
