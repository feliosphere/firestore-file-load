# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

"""
Type conversion utilities for Firestore value parsing.

This module contains helper functions to convert CSV string values
to appropriate Firestore data types.
"""

import json
import logging
from datetime import datetime
from typing import Any

from google.cloud.firestore import GeoPoint

logger = logging.getLogger(__name__)

# Known type prefixes/hints
KNOWN_TYPES = {
    'null',
    'none',
    'bool',
    'boolean',
    'int',
    'integer',
    'float',
    'double',
    'timestamp',
    'datetime',
    'date',
    'geopoint',
    'geo',
    'location',
    'array',
    'list',
    'map',
    'dict',
    'object',
    'bytes',
    'ref',
    'reference',
    'str',
    'string',
    'text',
}


def _is_quoted_string(value: str) -> bool:
    """
    Check if value is wrapped in quotes.

    Args:
        value: The string value to check

    Returns:
        True if value is wrapped in double quotes, False otherwise
    """
    return len(value) >= 2 and value[0] == '"' and value[-1] == '"'


def _extract_type_prefix(value: str) -> tuple[str | None, str]:
    """
    Extract type prefix from value string.

    Args:
        value: The string value (e.g., "int: 123")

    Returns:
        Tuple of (type_prefix, content) or (None, original_value)

    Examples:
        "int: 123" -> ("int", "123")
        "hello" -> (None, "hello")
    """
    if ':' not in value:
        return None, value

    prefix, content = value.split(':', 1)
    prefix = prefix.strip().lower()
    content = content.strip()

    # Validate it's a known type prefix
    if prefix in KNOWN_TYPES:
        return prefix, content

    return None, value


def _parse_column_header(header: str) -> tuple[str, str | None]:
    """
    Parse column header to extract field name and optional type hint.

    Supports format: "field_name:type"

    Args:
        header: Column header string (e.g., "age:int" or "name")

    Returns:
        Tuple of (field_name, type_hint)

    Examples:
        "age:int" → ("age", "int")
        "age:" → ("age", None)  # Empty type hint
        "age" → ("age", None)   # No type hint
        "age:unknown" → ("age", None) + warning logged
        "DocumentId" → ("DocumentId", None)
    """
    if ':' not in header:
        return header, None

    # Split only on first colon to handle edge cases
    parts = header.split(':', 1)
    if len(parts) != 2:
        return header, None

    field_name = parts[0].strip()
    type_hint = parts[1].strip().lower()

    # Handle empty type hint (e.g., "age:")
    if not type_hint:
        return field_name, None

    # Validate type hint is recognized
    if type_hint not in KNOWN_TYPES:
        logger.warning(
            f"Unknown type hint '{type_hint}' in header '{header}', "
            f"will use auto-detection for field '{field_name}'"
        )
        return field_name, None

    return field_name, type_hint


def _convert_to_null(content: str) -> None:
    """Convert to None/null type."""
    return None


def _convert_to_bool(content: str) -> bool:
    """
    Convert string to boolean.

    Args:
        content: String content to convert

    Returns:
        Boolean value
    """
    return content.lower() in ('true', '1', 'yes', 'y')


def _convert_to_int(content: str) -> int | str:
    """
    Convert string to integer with graceful degradation.

    Args:
        content: String content to convert

    Returns:
        Integer on success, original string on failure with warning
    """
    try:
        return int(content)
    except ValueError:
        logger.warning(
            f"Cannot convert '{content}' to integer, returning as string"
        )
        return content


def _convert_to_float(content: str) -> float | str:
    """
    Convert string to float with graceful degradation.

    Args:
        content: String content to convert

    Returns:
        Float on success, original string on failure with warning
    """
    try:
        return float(content)
    except ValueError:
        logger.warning(
            f"Cannot convert '{content}' to float, returning as string"
        )
        return content


def _convert_to_datetime(content: str) -> datetime | str:
    """
    Convert string to datetime with multiple format support.

    Tries ISO 8601 first, then common formats.

    Args:
        content: String content to convert

    Returns:
        Datetime on success, original string on failure with warning
    """
    try:
        return datetime.fromisoformat(content)
    except ValueError:
        for fmt in (
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
        ):
            try:
                return datetime.strptime(content, fmt)
            except ValueError:
                continue

        logger.warning(
            f"Cannot parse datetime '{content}', returning as string"
        )
        return content


def _convert_to_geopoint(content: str) -> GeoPoint | str:
    """
    Convert string to GeoPoint.

    Expected format: "lat,lng" (e.g., "37.7749,-122.4194")

    Args:
        content: String content to convert

    Returns:
        GeoPoint on success, original string on failure with warning
    """
    try:
        parts = content.split(',')
        if len(parts) == 2:
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
            return GeoPoint(lat, lng)
        logger.warning(
            f"Invalid GeoPoint format '{content}', expected 'lat,lng'"
        )
        return content
    except (ValueError, IndexError) as e:
        logger.warning(f"Cannot parse GeoPoint '{content}': {e}")
        return content


def _convert_to_array(content: str) -> list | str:
    """
    Convert JSON string to array/list.

    Args:
        content: String content to convert (JSON format)

    Returns:
        List on success, original string on failure with warning
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(
            f"Cannot parse array '{content}': {e}, returning as string"
        )
        return content


def _convert_to_map(content: str) -> dict | str:
    """
    Convert JSON string to map/dictionary.

    Args:
        content: String content to convert (JSON format)

    Returns:
        Dict on success, original string on failure with warning
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(
            f"Cannot parse map '{content}': {e}, returning as string"
        )
        return content


def _convert_to_bytes(content: str) -> bytes | str:
    """
    Convert base64 string to bytes.

    Args:
        content: String content to convert (base64 encoded)

    Returns:
        Bytes on success, original string on failure with warning
    """
    try:
        import base64

        return base64.b64decode(content)
    except Exception as e:
        logger.warning(
            f"Cannot decode bytes '{content}': {e}, returning as string"
        )
        return content


def _convert_to_reference(content: str) -> str:
    """
    Handle document reference.

    Note: Returns path as string. Actual DocumentReference needs Firestore client.

    Args:
        content: String content representing a document path

    Returns:
        String path
    """
    logger.info(
        'This creates a path string. The actual DocumentReference needs '
        'to be created with the Firestore client instance'
    )
    return content


def _convert_by_type_prefix(prefix: str, content: str) -> Any:
    """
    Convert content to appropriate type based on prefix.

    Args:
        prefix: Type prefix (lowercase, validated)
        content: Content to convert

    Returns:
        Converted value in appropriate type
    """
    if prefix in ('null', 'none'):
        return _convert_to_null(content)
    elif prefix in ('bool', 'boolean'):
        return _convert_to_bool(content)
    elif prefix in ('int', 'integer'):
        return _convert_to_int(content)
    elif prefix in ('float', 'double'):
        return _convert_to_float(content)
    elif prefix in ('timestamp', 'datetime', 'date'):
        return _convert_to_datetime(content)
    elif prefix in ('geopoint', 'geo', 'location'):
        return _convert_to_geopoint(content)
    elif prefix in ('array', 'list'):
        return _convert_to_array(content)
    elif prefix in ('map', 'dict', 'object'):
        return _convert_to_map(content)
    elif prefix == 'bytes':
        return _convert_to_bytes(content)
    elif prefix in ('ref', 'reference'):
        return _convert_to_reference(content)
    elif prefix in ('str', 'string', 'text'):
        return content
    else:
        logger.warning(f"Unknown type prefix '{prefix}', returning as string")
        return content


def _auto_detect_type(value: str) -> Any:
    """
    Automatically detect and convert value type.

    Detection order:
    1. Null values
    2. Boolean values
    3. Integer values
    4. Float values
    5. ISO 8601 datetime
    6. String (fallback)

    Args:
        value: String value to analyze

    Returns:
        Value converted to detected type
    """
    # Check for null values
    if value.lower() in ('null', 'none', ''):
        return None

    # Check for boolean values
    if value.lower() in ('true', 'yes', 'y'):
        return True
    if value.lower() in ('false', 'no', 'n'):
        return False

    # Check for integer values
    if value.isdigit() or (value[0] == '-' and value[1:].isdigit()):
        return int(value)

    # Check for float values
    try:
        if '.' in value or 'e' in value.lower():
            return float(value)
    except ValueError:
        pass

    # Check for ISO 8601 datetime (automatic detection)
    if 'T' in value or value.count('-') >= 2:
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            pass

    # Default to string
    return value
