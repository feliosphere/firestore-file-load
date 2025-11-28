# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

"""Tests for type conversion functionality in firebase_uploader."""

import pytest

from firebase_uploader.service import parse_firestore_value


class TestParseFirestoreValue:
    """Tests for parse_firestore_value function."""

    @pytest.mark.parametrize(
        'input_value,expected',
        [
            ('"123"', '123'),
            ('"true"', 'true'),
            ('"null"', 'null'),
        ],
    )
    def test_quoted_string_forces_string_type(self, input_value, expected):
        """Test that quoted values are always treated as strings."""
        assert parse_firestore_value(input_value) == expected

    @pytest.mark.parametrize(
        'prefix,value,expected_type',
        [
            ('int', '123', int),
            ('integer', '456', int),
        ],
    )
    def test_value_level_type_prefix_int(self, prefix, value, expected_type):
        """Test integer type prefix at value level."""
        input_str = f'{prefix}: {value}'
        result = parse_firestore_value(input_str)
        assert isinstance(result, expected_type)
        assert result == int(value)

    @pytest.mark.parametrize(
        'prefix,value',
        [
            ('str', '123'),
            ('string', '456'),
            ('text', '789'),
        ],
    )
    def test_value_level_type_prefix_string(self, prefix, value):
        """Test string type prefix at value level."""
        input_str = f'{prefix}: {value}'
        result = parse_firestore_value(input_str)
        assert result == value
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        'prefix,value,expected',
        [
            ('float', '123.45', 123.45),
            ('double', '678.90', 678.90),
        ],
    )
    def test_value_level_type_prefix_float(self, prefix, value, expected):
        """Test float type prefix at value level."""
        input_str = f'{prefix}: {value}'
        result = parse_firestore_value(input_str)
        assert result == expected
        assert isinstance(result, float)

    @pytest.mark.parametrize(
        'input_value,expected',
        [
            ('bool: true', True),
            ('bool: false', False),
            ('bool: 1', True),
            ('bool: 0', False),
            ('boolean: yes', True),
            ('boolean: no', False),
        ],
    )
    def test_value_level_type_prefix_bool(self, input_value, expected):
        """Test boolean type prefix at value level."""
        assert parse_firestore_value(input_value) is expected

    @pytest.mark.parametrize(
        'input_value',
        [
            'null: anything',
            'none: something',
        ],
    )
    def test_value_level_type_prefix_null(self, input_value):
        """Test null type prefix at value level."""
        assert parse_firestore_value(input_value) is None

    @pytest.mark.parametrize(
        'value,type_hint,expected_type',
        [
            ('456', 'int', int),
            ('789', 'integer', int),
        ],
    )
    def test_header_level_type_hint_int(self, value, type_hint, expected_type):
        """Test type hint parameter for integer."""
        result = parse_firestore_value(value, type_hint=type_hint)
        assert result == int(value)
        assert isinstance(result, expected_type)

    @pytest.mark.parametrize(
        'value,type_hint',
        [
            ('789', 'str'),
            ('123', 'string'),
            ('456', 'text'),
        ],
    )
    def test_header_level_type_hint_string(self, value, type_hint):
        """Test type hint parameter for string."""
        result = parse_firestore_value(value, type_hint=type_hint)
        assert result == value
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        'value,type_hint,expected',
        [
            ('12.34', 'float', 12.34),
            ('56.78', 'double', 56.78),
        ],
    )
    def test_header_level_type_hint_float(self, value, type_hint, expected):
        """Test type hint parameter for float."""
        result = parse_firestore_value(value, type_hint=type_hint)
        assert result == expected
        assert isinstance(result, float)

    @pytest.mark.parametrize(
        'value,expected',
        [
            ('42', 42),
            ('-42', -42),
            ('0', 0),
        ],
    )
    def test_auto_detect_integer(self, value, expected):
        """Test automatic detection of integer values."""
        result = parse_firestore_value(value)
        assert result == expected
        assert isinstance(result, int)

    @pytest.mark.parametrize(
        'value,expected',
        [
            ('3.14', 3.14),
            ('1e5', 100000.0),
            ('-2.5', -2.5),
        ],
    )
    def test_auto_detect_float(self, value, expected):
        """Test automatic detection of float values."""
        result = parse_firestore_value(value)
        assert result == expected
        assert isinstance(result, float)

    @pytest.mark.parametrize(
        'value,expected',
        [
            ('true', True),
            ('false', False),
            ('yes', True),
            ('no', False),
            ('TRUE', True),
            ('FALSE', False),
            ('Yes', True),
            ('No', False),
        ],
    )
    def test_auto_detect_boolean(self, value, expected):
        """Test automatic detection of boolean values."""
        assert parse_firestore_value(value) is expected

    @pytest.mark.parametrize(
        'value',
        [
            'null',
            'NULL',
            'None',
            'none',
        ],
    )
    def test_auto_detect_null(self, value):
        """Test automatic detection of null values."""
        assert parse_firestore_value(value) is None

    def test_auto_detect_string_fallback(self):
        """Test that unknown values default to string."""
        result = parse_firestore_value('hello world')
        assert result == 'hello world'
        assert isinstance(result, str)

    def test_priority_quoted_over_prefix(self):
        """Test that quoted values take priority over type prefixes."""
        result = parse_firestore_value('"int: 123"')
        assert result == 'int: 123'
        assert isinstance(result, str)

    def test_priority_prefix_over_hint(self):
        """Test that value prefix takes priority over header hint."""
        result = parse_firestore_value('str: 999', type_hint='int')
        assert result == '999'
        assert isinstance(result, str)

    def test_priority_hint_over_auto(self):
        """Test that header hint takes priority over auto-detection."""
        result = parse_firestore_value('123', type_hint='str')
        assert result == '123'
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        'value,expected',
        [
            ('', ''),
            ('   ', ''),
            ('\t', ''),
        ],
    )
    def test_empty_string(self, value, expected):
        """Test handling of empty strings."""
        assert parse_firestore_value(value) == expected

    @pytest.mark.parametrize(
        'prefix,json_value,expected',
        [
            ('array', '[1, 2, 3]', [1, 2, 3]),
            ('list', '["a", "b", "c"]', ['a', 'b', 'c']),
            ('array', '[]', []),
        ],
    )
    def test_array_type(self, prefix, json_value, expected):
        """Test array/list type conversion."""
        input_str = f'{prefix}: {json_value}'
        result = parse_firestore_value(input_str)
        assert result == expected
        assert isinstance(result, list)

    @pytest.mark.parametrize(
        'prefix,json_value,expected',
        [
            ('map', '{"key": "value"}', {'key': 'value'}),
            ('dict', '{"a": 1, "b": 2}', {'a': 1, 'b': 2}),
            ('object', '{}', {}),
        ],
    )
    def test_map_type(self, prefix, json_value, expected):
        """Test map/dict type conversion."""
        input_str = f'{prefix}: {json_value}'
        result = parse_firestore_value(input_str)
        assert result == expected
        assert isinstance(result, dict)
