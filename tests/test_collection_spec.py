# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

"""Tests for CollectionSpec dataclass."""

import json
import tempfile
from pathlib import Path

import pytest

from firebase_uploader.collection_spec import CollectionSpec


@pytest.fixture
def temp_csv_file():
    """
    Fixture that creates a temporary CSV file.

    Yields:
        Path object for the temporary CSV file
    """
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False
    ) as f:
        csv_path = Path(f.name)
        f.write('DocumentId,name\ndoc1,test\n')

    yield csv_path

    # Cleanup
    if csv_path.exists():
        csv_path.unlink()


@pytest.fixture
def temp_schema_file():
    """
    Fixture that creates a temporary schema JSON file.

    Yields:
        Path object for the temporary schema file
    """
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False
    ) as f:
        schema_path = Path(f.name)
        json.dump(
            {
                'key_column': 'id',
                'structure': {'question': 'question', 'answer': 'answer'},
            },
            f,
        )

    yield schema_path

    # Cleanup
    if schema_path.exists():
        schema_path.unlink()


class TestCollectionSpecProperties:
    """Tests for CollectionSpec property accessors."""

    def test_file_path_property(self, temp_csv_file):
        """Test that file_path property returns the CSV file path."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
        )
        assert spec.file_path == temp_csv_file
        assert isinstance(spec.file_path, Path)

    def test_merge_property_true(self, temp_csv_file):
        """Test that merge property returns True when set."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
        )
        assert spec.merge is True

    def test_merge_property_false(self, temp_csv_file):
        """Test that merge property returns False when set."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=False,
        )
        assert spec.merge is False

    def test_name_default_uses_file_stem(self, temp_csv_file):
        """Test that name defaults to CSV filename without extension."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
        )
        expected_name = temp_csv_file.stem
        assert spec.name == expected_name

    def test_name_custom_override(self, temp_csv_file):
        """Test that custom name overrides default."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
            _name='custom_collection',
        )
        assert spec.name == 'custom_collection'

    def test_schema_path_default_uses_json_extension(self, temp_csv_file):
        """Test that schema_path defaults to CSV filename with .json extension."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
        )
        expected_schema_path = temp_csv_file.with_suffix('.json')
        assert spec.schema_path == expected_schema_path

    def test_schema_path_custom_override(self, temp_csv_file, temp_schema_file):
        """Test that custom schema path overrides default."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
            _schema_path=temp_schema_file,
        )
        assert spec.schema_path == temp_schema_file


class TestCollectionSpecGetSchema:
    """Tests for CollectionSpec.get_schema() method."""

    def test_get_schema_file_not_found_returns_none(self, temp_csv_file):
        """Test that get_schema returns None when schema file doesn't exist."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
        )
        # Schema file doesn't exist (default would be temp_csv_file.json)
        schema = spec.get_schema()
        assert schema is None

    def test_get_schema_loads_valid_json(self, temp_csv_file):
        """Test that get_schema loads valid JSON schema file."""
        # Create a schema file that matches the CSV filename
        schema_path = temp_csv_file.with_suffix('.json')
        schema_data = {
            'key_column': 'id',
            'structure': {
                'question': 'question',
                'options': [
                    {'id': 'literal:a', 'text': 'option_a'},
                    {'id': 'literal:b', 'text': 'option_b'},
                ],
            },
        }
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        try:
            spec = CollectionSpec(
                _file_path=temp_csv_file,
                _merge=True,
            )
            schema = spec.get_schema()
            assert schema is not None
            assert schema == schema_data
            assert schema['key_column'] == 'id'
            assert 'structure' in schema
        finally:
            # Cleanup
            if schema_path.exists():
                schema_path.unlink()

    def test_get_schema_caches_result(self, temp_csv_file):
        """Test that get_schema caches the schema on first load."""
        # Create schema file
        schema_path = temp_csv_file.with_suffix('.json')
        schema_data = {'key_column': 'id', 'structure': {'name': 'name'}}
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        try:
            spec = CollectionSpec(
                _file_path=temp_csv_file,
                _merge=True,
            )

            # First call loads and caches
            schema1 = spec.get_schema()
            assert schema1 == schema_data

            # Modify the file
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump({'key_column': 'modified'}, f)

            # Second call should return cached version
            schema2 = spec.get_schema()
            assert schema2 is not None  # Ensure it's not None for type checker
            assert schema2 == schema_data  # Still the original
            assert schema2['key_column'] == 'id'  # Not 'modified'

        finally:
            if schema_path.exists():
                schema_path.unlink()

    def test_get_schema_invalid_json_raises_error(self, temp_csv_file):
        """Test that get_schema raises ValueError for invalid JSON."""
        # Create invalid JSON file
        schema_path = temp_csv_file.with_suffix('.json')
        with open(schema_path, 'w', encoding='utf-8') as f:
            f.write('{invalid json content}')

        try:
            spec = CollectionSpec(
                _file_path=temp_csv_file,
                _merge=True,
            )
            with pytest.raises(ValueError, match='Invalid JSON'):
                spec.get_schema()
        finally:
            if schema_path.exists():
                schema_path.unlink()

    def test_get_schema_custom_path(self, temp_csv_file, temp_schema_file):
        """Test that get_schema uses custom schema path when provided."""
        schema_data = {
            'key_column': 'id',
            'structure': {'question': 'question', 'answer': 'answer'},
        }

        # Re-write the schema file with known content
        with open(temp_schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
            _schema_path=temp_schema_file,
        )

        schema = spec.get_schema()
        assert schema is not None
        assert schema == schema_data


class TestCollectionSpecIntegration:
    """Integration tests for CollectionSpec with real file scenarios."""

    def test_complete_spec_with_all_options(
        self, temp_csv_file, temp_schema_file
    ):
        """Test CollectionSpec with all options specified."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _schema_path=temp_schema_file,
            _name='my_collection',
            _merge=False,
        )

        assert spec.file_path == temp_csv_file
        assert spec.schema_path == temp_schema_file
        assert spec.name == 'my_collection'
        assert spec.merge is False

        schema = spec.get_schema()
        assert schema is not None
        assert 'key_column' in schema

    def test_spec_with_defaults(self, temp_csv_file):
        """Test CollectionSpec with minimal options (using defaults)."""
        spec = CollectionSpec(
            _file_path=temp_csv_file,
            _merge=True,
        )

        # Defaults should be applied
        assert spec.file_path == temp_csv_file
        assert spec.name == temp_csv_file.stem
        assert spec.schema_path == temp_csv_file.with_suffix('.json')
        assert spec.merge is True

        # Schema should be None (file doesn't exist)
        assert spec.get_schema() is None

    def test_different_csv_filenames(self):
        """Test that different CSV filenames produce correct defaults."""
        test_cases = [
            ('data.csv', 'data', 'data.json'),
            ('questions.csv', 'questions', 'questions.json'),
            ('my_collection.csv', 'my_collection', 'my_collection.json'),
        ]

        for csv_name, expected_name, expected_schema_name in test_cases:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.csv',
                delete=False,
                prefix=csv_name.split('.')[0],
            ) as f:
                csv_path = Path(f.name)

            try:
                spec = CollectionSpec(_file_path=csv_path, _merge=True)
                # Name should match stem
                assert csv_path.stem in spec.name
                # Schema should have .json extension
                assert spec.schema_path.suffix == '.json'
                assert spec.schema_path.stem == csv_path.stem
            finally:
                if csv_path.exists():
                    csv_path.unlink()
