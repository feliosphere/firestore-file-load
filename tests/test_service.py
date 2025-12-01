# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

"""Tests for service layer functionality in firebase_uploader."""

from firebase_uploader.service import (
    _is_effectively_empty,
    apply_schema_mapping,
    get_fields,
    parse_firestore_value,
)


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


class TestParseFirestoreValue:
    """Tests for parse_firestore_value function."""

    def test_non_string_value_returns_as_is(self):
        """Test that non-string values are returned unchanged."""
        assert parse_firestore_value(123) == 123
        assert parse_firestore_value(45.6) == 45.6
        assert parse_firestore_value(True) is True
        assert parse_firestore_value(None) is None

    def test_empty_string_returns_empty_string(self):
        """Test that empty strings remain empty strings."""
        assert parse_firestore_value('') == ''
        assert parse_firestore_value('   ') == ''

    def test_quoted_string_extraction(self):
        """Test that quoted strings are unquoted."""
        assert parse_firestore_value('"hello"') == 'hello'
        assert parse_firestore_value('"123"') == '123'
        assert parse_firestore_value('"true"') == 'true'

    def test_value_prefix_conversion(self):
        """Test type conversion using value-level prefixes."""
        assert parse_firestore_value('int: 42') == 42
        assert parse_firestore_value('float: 3.14') == 3.14
        assert parse_firestore_value('bool: true') is True
        assert parse_firestore_value('str: 123') == '123'

    def test_type_hint_conversion(self):
        """Test type conversion using header type hints."""
        assert parse_firestore_value('100', type_hint='int') == 100
        assert parse_firestore_value('3.14', type_hint='float') == 3.14
        assert parse_firestore_value('yes', type_hint='bool') is True
        assert parse_firestore_value('456', type_hint='str') == '456'

    def test_auto_detection(self):
        """Test automatic type detection."""
        assert parse_firestore_value('123') == 123
        assert parse_firestore_value('45.6') == 45.6
        assert parse_firestore_value('true') is True
        assert parse_firestore_value('false') is False
        assert parse_firestore_value('hello') == 'hello'

    def test_value_prefix_overrides_type_hint(self):
        """Test that value prefix takes precedence over type hint."""
        assert parse_firestore_value('str: 100', type_hint='int') == '100'
        assert isinstance(
            parse_firestore_value('str: 100', type_hint='int'), str
        )

    def test_quoted_value_overrides_type_hint(self):
        """Test that quoted values override type hints."""
        assert parse_firestore_value('"100"', type_hint='int') == '100'
        assert isinstance(parse_firestore_value('"100"', type_hint='int'), str)

    def test_whitespace_handling(self):
        """Test that leading/trailing whitespace is stripped."""
        assert parse_firestore_value('  123  ') == 123
        assert parse_firestore_value('  hello  ') == 'hello'


class TestIsEffectivelyEmpty:
    """Tests for _is_effectively_empty function."""

    def test_none_is_empty(self):
        """Test that None values are considered empty."""
        assert _is_effectively_empty(None, None) is True

    def test_empty_string_is_empty(self):
        """Test that empty strings are considered empty."""
        assert _is_effectively_empty('', None) is True
        assert _is_effectively_empty('   ', None) is True

    def test_non_empty_string_is_not_empty(self):
        """Test that non-empty strings are not empty."""
        assert _is_effectively_empty('hello', None) is False
        assert _is_effectively_empty('0', None) is False

    def test_empty_dict_is_empty(self):
        """Test that dictionaries with all empty values are empty."""
        schema = {'name': 'name_field', 'age': 'age_field'}
        data = {'name': '', 'age': None}
        assert _is_effectively_empty(data, schema) is True

    def test_dict_with_non_empty_value_is_not_empty(self):
        """Test that dictionaries with any non-empty value are not empty."""
        schema = {'name': 'name_field', 'age': 'age_field'}
        data = {'name': 'John', 'age': None}
        assert _is_effectively_empty(data, schema) is False

    def test_dict_with_literal_fields_ignores_literals(self):
        """Test that literal fields are ignored when checking emptiness."""
        schema = {'id': 'literal:a', 'text': 'text_field'}
        # Even though 'id' has a value, if it's a literal in schema, check 'text'
        data = {'id': 'a', 'text': ''}
        assert _is_effectively_empty(data, schema) is True

        data = {'id': 'a', 'text': 'Some text'}
        assert _is_effectively_empty(data, schema) is False

    def test_empty_list_is_empty(self):
        """Test that empty lists are considered empty."""
        assert _is_effectively_empty([], None) is True

    def test_list_with_all_empty_items_is_empty(self):
        """Test that lists with all empty items are empty."""
        data = ['', None, '   ']
        assert _is_effectively_empty(data, None) is True

    def test_list_with_non_empty_item_is_not_empty(self):
        """Test that lists with any non-empty item are not empty."""
        data = ['', 'hello', None]
        assert _is_effectively_empty(data, None) is False

    def test_nested_empty_structures(self):
        """Test deeply nested empty structures."""
        schema = {'options': [{'id': 'literal:a', 'text': 'text_field'}]}
        data = {'options': [{'id': 'a', 'text': ''}, {'id': 'b', 'text': None}]}
        # The list has items, so the dict is not empty
        # (even though the items themselves might have empty non-literal fields)
        assert _is_effectively_empty(data, schema) is False

        # However, a dict with an empty list should be empty
        data_with_empty_list = {'options': []}
        assert _is_effectively_empty(data_with_empty_list, schema) is True

    def test_non_empty_values(self):
        """Test that various non-empty values return False."""
        assert _is_effectively_empty(0, None) is False
        assert _is_effectively_empty(False, None) is False
        assert _is_effectively_empty(123, None) is False
        assert _is_effectively_empty({'key': 'value'}, {}) is False


class TestApplySchemaMapping:
    """Tests for apply_schema_mapping function."""

    def test_simple_string_mapping(self):
        """Test mapping a simple string field."""
        row_data = {'question': 'What is 2+2?', 'answer': '4'}
        schema = 'question'
        result = apply_schema_mapping(row_data, schema)
        assert result == 'What is 2+2?'

    def test_literal_string_mapping(self):
        """Test mapping a literal string value."""
        row_data = {'question': 'What is 2+2?'}
        schema = 'literal:a'
        result = apply_schema_mapping(row_data, schema)
        assert result == 'a'

    def test_dict_mapping(self):
        """Test mapping to a dictionary structure."""
        row_data = {
            'q_text': 'What is the capital?',
            'ans': 'Paris',
            'pts': '10',
        }
        schema = {'question': 'q_text', 'answer': 'ans', 'points': 'pts'}
        result = apply_schema_mapping(row_data, schema)
        assert result == {
            'question': 'What is the capital?',
            'answer': 'Paris',
            'points': '10',
        }

    def test_list_mapping(self):
        """Test mapping to a list structure."""
        row_data = {
            'opt_a': 'Option A',
            'opt_b': 'Option B',
            'opt_c': 'Option C',
        }
        schema = [
            {'id': 'literal:a', 'text': 'opt_a'},
            {'id': 'literal:b', 'text': 'opt_b'},
            {'id': 'literal:c', 'text': 'opt_c'},
        ]
        result = apply_schema_mapping(row_data, schema)
        assert result == [
            {'id': 'a', 'text': 'Option A'},
            {'id': 'b', 'text': 'Option B'},
            {'id': 'c', 'text': 'Option C'},
        ]

    def test_list_mapping_filters_empty_items(self):
        """Test that empty items are filtered from lists."""
        row_data = {
            'opt_a': 'Option A',
            'opt_b': '',
            'opt_c': 'Option C',
            'opt_d': None,
        }
        schema = [
            {'id': 'literal:a', 'text': 'opt_a'},
            {'id': 'literal:b', 'text': 'opt_b'},
            {'id': 'literal:c', 'text': 'opt_c'},
            {'id': 'literal:d', 'text': 'opt_d'},
        ]
        result = apply_schema_mapping(row_data, schema)
        # Only items with non-empty text should remain
        assert len(result) == 2
        assert result == [
            {'id': 'a', 'text': 'Option A'},
            {'id': 'c', 'text': 'Option C'},
        ]

    def test_nested_structure_mapping(self):
        """Test mapping to a complex nested structure."""
        row_data = {
            'q': 'What is Python?',
            'a': 'Answer A',
            'b': 'Answer B',
            'correct': 'a',
            'tag1': 'programming',
            'tag2': 'python',
        }
        schema = {
            'question_text': 'q',
            'options': [
                {'id': 'literal:a', 'text': 'a'},
                {'id': 'literal:b', 'text': 'b'},
            ],
            'correct_option': 'correct',
            'tags': ['tag1', 'tag2'],
        }
        result = apply_schema_mapping(row_data, schema)
        assert result == {
            'question_text': 'What is Python?',
            'options': [
                {'id': 'a', 'text': 'Answer A'},
                {'id': 'b', 'text': 'Answer B'},
            ],
            'correct_option': 'a',
            'tags': ['programming', 'python'],
        }

    def test_missing_field_returns_none(self):
        """Test that missing fields return None."""
        row_data = {'name': 'John'}
        schema = 'age'
        result = apply_schema_mapping(row_data, schema)
        assert result is None

    def test_complex_filtering_scenario(self):
        """Test a realistic scenario with partial data."""
        row_data = {
            'id': '1',
            'question': 'Sample question',
            'opt_a': 'First option',
            'opt_b': 'Second option',
            'opt_c': '',  # Empty
            'opt_d': '',  # Empty
            'elem_1': 'img_001',
            'elem_2': '',  # Empty
        }
        schema = {
            'question': 'question',
            'options': [
                {'id': 'literal:a', 'text': 'opt_a'},
                {'id': 'literal:b', 'text': 'opt_b'},
                {'id': 'literal:c', 'text': 'opt_c'},
                {'id': 'literal:d', 'text': 'opt_d'},
            ],
            'content_elements': ['elem_1', 'elem_2'],
        }
        result = apply_schema_mapping(row_data, schema)

        # Should only have 2 options (a and b)
        assert len(result['options']) == 2
        assert result['options'] == [
            {'id': 'a', 'text': 'First option'},
            {'id': 'b', 'text': 'Second option'},
        ]

        # content_elements is a list of strings (not dicts)
        # Empty strings ARE filtered even in simple string lists
        assert len(result['content_elements']) == 1
        assert result['content_elements'] == ['img_001']

    def test_all_empty_list_returns_empty_list(self):
        """Test that a list with all empty items returns an empty list."""
        row_data = {'opt_a': '', 'opt_b': None, 'opt_c': '   '}
        schema = [
            {'id': 'literal:a', 'text': 'opt_a'},
            {'id': 'literal:b', 'text': 'opt_b'},
            {'id': 'literal:c', 'text': 'opt_c'},
        ]
        result = apply_schema_mapping(row_data, schema)
        assert result == []

    def test_none_schema_returns_none(self):
        """Test that None schema returns None."""
        row_data = {'name': 'John'}
        result = apply_schema_mapping(row_data, None)
        assert result is None
