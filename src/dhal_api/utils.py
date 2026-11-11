from dhal_api.models import DataType


# Mapping of DataTypes to the values stored in the `sources_res_formats` extra
# of datasets on the Hub
HUB_DATATYPE_MAP = {
    DataType.raster: ['tif'],
    DataType.vector: ['shp', 'gpkg', 'geojson'],
    DataType.table: ['csv']
}

# Mapping of DataTypes to relevant file extensions, for extracting the correct
# Resource from a Data Hub Package
EXTENSION_MAP = {
    DataType.vector: ['SHP', 'GEOJSON', 'GPKG'],
    DataType.raster: ['TIF', 'TIFF'],
    DataType.table: ['CSV']
}


def resource_type_matches(url, datatype):
    """Check a Resource file extension against the expected datatype."""
    extension = url.rsplit('.', 1)[-1].upper()
    if extension in EXTENSION_MAP[datatype]:
        return True


def resource_type_search_string(datatype):
    matching_types = HUB_DATATYPE_MAP[datatype]
    if len(matching_types) == 1:
        return f'extras_sources_res_formats:{matching_types[0]}'
    else:
        datatype_str = '" OR "'.join(t for t in matching_types)
        return f'extras_sources_res_formats:("{datatype_str}")'


def tag_search_string_and(tags):
    """Format a search string for tags using AND syntax.

    All tags must be wrapped in double quotes in case they contain whitespace.
    """
    tag_str = '" AND "'.join(tag for tag in tags)
    return f'tags:("{tag_str}")'


def tag_search_string_or(tags):
    """Format a search string for tags using OR syntax.

    All tags must be wrapped in double quotes in case they contain whitespace.
    """
    tag_str = '" OR "'.join(tag for tag in tags)
    return f'tags:("{tag_str}")'


def tag_search_string_complex(index_tags, tags):
    """Format a search string for tags using a combination of AND and OR syntax.

    Each tag must be wrapped in double quotes in case it contains whitespace.
    """
    # Ensure none of the `index_tags` also appear in `tags`
    non_index_tags = [tag for tag in tags if tag not in index_tags]

    index_tag_str = '("' + '" OR "'.join(tag for tag in index_tags) + '")'
    tag_str = '("' + '" OR "'.join(tag for tag in non_index_tags) + '")'

    return f'tags:({index_tag_str} AND {tag_str})'
