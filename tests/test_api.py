import json
import os
import unittest
from unittest.mock import patch

from ckanapi.errors import CKANAPIError
from fastapi.testclient import TestClient

from dhal_api.main import app
from dhal_api.utils import tag_search_string_complex


DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

client = TestClient(app, raise_server_exceptions=False)


@patch('dhal_api.main.CKAN_API_URL', 'https://data.naturalcapitalalliance.stanford.edu')
@patch('dhal_api.main.PLACE_VOCAB_ID', '08e541f5-0f71-4931-bfc8-30bf66801146')
@patch('dhal_api.main.COLLECTION_VOCAB_ID', '94023b63-78d9-46fb-b688-154d0cd2a8ef')
class APITests(unittest.TestCase):

    def test_search_dataset(self):
        """Simple test case where CKAN returns one Package."""
        with open(f'{DATA_DIR}/ckan_response_data_simple.json') as f:
            success_resp = json.load(f)
        with patch('dhal_api.main.RemoteCKAN.call_action') as mock_ckan:
            mock_ckan.return_value = success_resp

            params = {
                "tags": ["DEM"],
                "datatype": "raster"
            }
            resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 1)

        with open(f'{DATA_DIR}/formatted_payload_simple.json') as test_resp:
            expected_data = json.load(test_resp)
            self.assertEqual(data, expected_data)

    def test_search_dataset_multiple_valid_filetypes(self):
        """Test returning Resources of multiple valid file types."""
        with open(f'{DATA_DIR}/ckan_response_vector_formats.json') as f:
            success_resp = json.load(f)
        with patch('dhal_api.main.RemoteCKAN.call_action') as mock_ckan:
            mock_ckan.return_value = success_resp

            params = {
                "tags": ["WATERSHEDS"],
                "datatype": "vector"
            }
            resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 2)

        with open(f'{DATA_DIR}/formatted_payload_vector_formats.json') as test_resp:
            expected_data = json.load(test_resp)
            self.assertEqual(data, expected_data)

    def test_search_dataset_no_results(self):
        """Test response when no matching datasets found."""
        with patch('dhal_api.main.RemoteCKAN.call_action') as mock_ckan:
            mock_ckan.return_value = {'count': 0, 'results': []}

            params = {
                "tags": ["DEM"],
                "datatype": "vector"
            }
            resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data, {'count': 0, 'datasets': []})

    def test_search_dataset_filter_no_matching_resource(self):
        """Filter out Package where Resource is ambiguous: no matching filetype."""
        with open(f'{DATA_DIR}/ckan_response_no_resource_match.json') as f:
            success_resp = json.load(f)
        with patch('dhal_api.main.RemoteCKAN.call_action') as mock_ckan:
            mock_ckan.return_value = success_resp

            params = {
                "tags": ["COASTLINE"],
                "datatype": "vector"
            }
            resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 1)

        with open(f'{DATA_DIR}/formatted_payload_no_resource_match.json') as test_resp:
            expected_data = json.load(test_resp)
            self.assertEqual(data, expected_data)

    def test_search_dataset_filter_multiple_matching_resources(self):
        """Filter out Package where Resource is ambiguous: multiple matches."""
        with open(f'{DATA_DIR}/ckan_response_multiple_resource_match.json') as f:
            success_resp = json.load(f)
        with patch('dhal_api.main.RemoteCKAN.call_action') as mock_ckan:
            mock_ckan.return_value = success_resp

            params = {
                "tags": ["LULC"],
                "datatype": "raster"
            }
            resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Only one dataset should be returned; the one with ambiguous Resources
        # should be filtered out
        self.assertEqual(data['count'], 1)

        with open(f'{DATA_DIR}/formatted_payload_multiple_resource_match.json') as test_resp:
            expected_data = json.load(test_resp)
            self.assertEqual(data, expected_data)

    def test_search_dataset_bad_query_missing_key(self):
        """Test API handles bad query parameters: missing required key."""
        params = {
            "tags": ["DEM"],
        }
        resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 422)
        self.assertIn('datatype', resp.json()['detail'][0]['loc'])

    def test_search_dataset_bad_query_invalid_extent(self):
        """Test API handles bad query parameters: extent list len < 4."""
        params = {
            "tags": ["DEM"],
            "datatype": "raster",
            "extent": [-126.56, 25.19, -92.11]
        }
        resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 422)
        self.assertIn('extent', resp.json()['detail'][0]['loc'])

    def test_search_dataset_bad_query_infinity_extent(self):
        """Test API handles bad query parameters: extent includes infinity."""
        params = {
            "tags": ["DEM"],
            "datatype": "raster",
            "extent": [float('inf'), -126.56, 25.19, -92.11]
        }
        resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 422)
        self.assertIn('extent', resp.json()['detail'][0]['loc'])

    def test_handle_ckan_payload_missing_count_results(self):
        """Handle case where CKAN payload lacks `count` or `results`."""
        with patch('dhal_api.main.RemoteCKAN.call_action') as mock_ckan:
            mock_ckan.return_value = {'error': 'Something went wrong'}

            params = {
                "tags": ["DEM"],
                "datatype": "raster"
            }
            resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertIn("error_message", data.keys())

    def test_handle_ckan_error(self):
        """Test handling CKANAPIError."""
        with patch('dhal_api.main.RemoteCKAN.call_action') as mock_ckan:
            mock_ckan.side_effect = Exception(CKANAPIError)

            params = {
                "tags": ["DEM"],
                "datatype": "raster"
            }
            resp = client.get("/search_dataset/", params=params)

        self.assertEqual(resp.status_code, 500)
        data = resp.json()
        self.assertIn("error_message", data.keys())


class UtilsTests(unittest.TestCase):

    def test_complex_query_string_multiple_index_tags(self):
        index_tags = ['LULC', 'LAND USE LAND COVER']
        # LULC repeated in tags -- should be de-duplicated
        tags = ['LULC', 'USLE C FACTOR', 'USLE P FACTOR']
        expected_string = 'tags:(("LULC" OR "LAND USE LAND COVER") AND ("USLE C FACTOR" OR "USLE P FACTOR"))'
        actual_string = tag_search_string_complex(index_tags, tags)
        self.assertEqual(expected_string, actual_string)

    def test_complex_query_string_single_index_tag(self):
        index_tags = ['LAND USE LAND COVER']
        tags = ['USLE C FACTOR', 'USLE P FACTOR']
        expected_string = 'tags:(("LAND USE LAND COVER") AND ("USLE C FACTOR" OR "USLE P FACTOR"))'
        actual_string = tag_search_string_complex(index_tags, tags)
        self.assertEqual(expected_string, actual_string)
