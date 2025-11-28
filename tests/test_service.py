# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

"""Tests for service layer functionality in firebase_uploader."""

from firebase_uploader.service import get_fields


class TestGetFields:
    """Tests for get_fields function."""

    def test_excludes_document_id(self):
        """Test that DocumentId field is excluded from output."""
        row = {'DocumentId': 'doc1', 'name': 'John', 'age': '30'}
        fields = get_fields(row)
        assert 'DocumentId' not in fields
        assert 'name' in fields
        assert 'age' in fields

    def test_simple_field_conversion(self):
        """Test basic field conversion without type hints."""
        row = {
            'DocumentId': 'doc1',
            'name': 'Alice',
            'age': '25',
            'score': '95.5',
        }
        fields = get_fields(row)
        assert fields['name'] == 'Alice'
        assert fields['age'] == 25
        assert fields['score'] == 95.5

    def test_header_type_hint_parsing(self):
        """Test parsing type hints from column headers."""
        row = {
            'DocumentId': 'doc1',
            'name': 'Bob',
            'age:int': '30',
            'code:str': '00123',
        }
        fields = get_fields(row)
        assert fields['age'] == 30
        assert fields['code'] == '00123'
        assert isinstance(fields['code'], str)
        # Check that the field name doesn't include the type hint
        assert 'age' in fields
        assert 'age:int' not in fields
        assert 'code' in fields
        assert 'code:str' not in fields

    def test_mixed_type_specifications(self):
        """Test row with mixed type specification methods."""
        row = {
            'DocumentId': 'doc1',
            'field1': '100',  # Auto-detect
            'field2:str': '200',  # Header hint
            'field3': 'int: 300',  # Value prefix
            'field4': '"400"',  # Quoted
        }
        fields = get_fields(row)
        assert fields['field1'] == 100
        assert fields['field2'] == '200'
        assert fields['field3'] == 300
        assert fields['field4'] == '400'
        assert isinstance(fields['field2'], str)
        assert isinstance(fields['field4'], str)

    def test_empty_row(self):
        """Test handling of row with only DocumentId."""
        row = {'DocumentId': 'doc1'}
        fields = get_fields(row)
        assert fields == {}

    def test_boolean_fields(self):
        """Test boolean field handling."""
        row = {
            'DocumentId': 'doc1',
            'active': 'true',
            'verified:bool': 'yes',
            'deleted': 'false',
        }
        fields = get_fields(row)
        assert fields['active'] is True
        assert fields['verified'] is True
        assert fields['deleted'] is False

    def test_empty_type_hint_falls_back_to_auto_detection(self):
        """Test that empty type hint (e.g., 'age:') falls back to auto-detection."""
        row = {
            'DocumentId': 'doc3',
            'age:': '35',  # Empty type hint, should auto-detect to int
            'name': 'Bob',
        }
        fields = get_fields(row)
        assert fields == {'age': 35, 'name': 'Bob'}

    def test_value_prefix_overrides_header_type_hint(self):
        """Test that value-level prefix overrides header type hint."""
        row = {
            'DocumentId': 'doc4',
            'age:int': 'str: 40',  # Value prefix overrides header hint
            'id:str': '123',
        }
        fields = get_fields(row)
        assert fields == {'age': '40', 'id': '123'}
        assert isinstance(fields['age'], str)

    def test_quoted_values_override_header_type_hints(self):
        """Test that quoted values override header type hints."""
        row = {
            'DocumentId': 'doc5',
            'age:int': '"45"',  # Quoted value overrides int hint
            'score:float': '"99.9"',  # Quoted value overrides float hint
        }
        fields = get_fields(row)
        assert fields == {'age': '45', 'score': '99.9'}
        assert isinstance(fields['age'], str)
        assert isinstance(fields['score'], str)

    def test_backward_compatibility_without_type_hints(self):
        """Test that CSV format without header type hints still works (backward compatibility)."""
        row = {
            'DocumentId': 'doc1',
            'age': '25',  # Auto-detect to int
            'name': 'John',  # Auto-detect to string
            'score': '95.5',  # Auto-detect to float
            'active': 'true',  # Auto-detect to bool
            'id': 'str: 123',  # Value prefix still works
        }
        fields = get_fields(row)
        assert fields == {
            'age': 25,
            'name': 'John',
            'score': 95.5,
            'active': True,
            'id': '123',
        }
