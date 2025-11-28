# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

import csv
import logging
import os
from typing import Any

from .firestore_repository import FirestoreRepository
from .type_converters import (
    _auto_detect_type,
    _convert_by_type_prefix,
    _extract_type_prefix,
    _is_quoted_string,
    _parse_column_header,
)

logger = logging.getLogger(__name__)


def parse_firestore_value(value: str, type_hint: str | None = None) -> Any:
    """
    Converts a string value to the appropriate Firestore data type.

    Type resolution priority (cascade):
    1. Quoted values (forces string) - highest priority
    2. Value-level type prefix (e.g., "int: 123")
    3. Header-level type hint parameter
    4. Automatic type detection - lowest priority

    Supported type prefixes/hints:
    - null, none → None
    - bool, boolean → Boolean (true/false, 1/0, yes/no)
    - int, integer → Integer
    - float, double → Float
    - timestamp, datetime, date → Datetime (ISO 8601 format)
    - geopoint, geo, location → GeoPoint (format: "lat,lng")
    - array, list → Array (JSON format)
    - map, dict, object → Map/Dictionary (JSON format)
    - bytes → Bytes (base64 encoded)
    - ref, reference → DocumentReference (format: "collection/document")
    - str, string, text → String (explicit string type)

    Without prefix or type hint, automatic detection is attempted:
    - Quoted values (e.g., "123") -> String (quotes removed)
    - "null", "NULL", "None" -> None
    - "true", "false", "yes", "no" (case-insensitive) -> Boolean
    - Numeric strings -> Integer or Float
    - ISO 8601 datetime strings -> Datetime
    - Everything else -> String

    Note: To force a number as a string:
      1. Use the str: prefix (recommended): str: 123
      2. Use str type hint in column header: column_name:str
      3. Quote it in your CSV editor: "123"

    Args:
        value: The string value to convert
        type_hint: Optional type hint from column header (e.g., "int")

    Returns:
        The converted value in the appropriate Python/Firestore type

    Examples:
        >>> parse_firestore_value('123')
        123
        >>> parse_firestore_value('123', type_hint='str')
        "123"
        >>> parse_firestore_value('"123"')  # Quoted
        "123"
        >>> parse_firestore_value('str: 123')  # Value prefix overrides
        "123"
    """
    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value:
        return ''

    # Priority 1: Quoted values → force string
    if _is_quoted_string(value):
        return value[1:-1]  # Return content without quotes

    # Priority 2: Value-level type prefix
    prefix, content = _extract_type_prefix(value)
    if prefix is not None:
        return _convert_by_type_prefix(prefix, content)

    # Priority 3: Header-level type hint
    if type_hint is not None:
        type_hint = type_hint.strip().lower()
        return _convert_by_type_prefix(type_hint, value)

    # Priority 4: Automatic type detection
    return _auto_detect_type(value)


def get_fields(row: dict) -> dict:
    """
    Transforms a CSV row (dict) into a Firestore-ready dict,
    performing type conversion and excluding the DocumentId field.

    Supports type hints in column headers (e.g., "age:int").

    Type resolution priority:
    1. Quoted values in cells → force string
    2. Value-level type prefixes → explicit type
    3. Header-level type hints → column-wide type
    4. Automatic detection → infer from value

    This is your core business logic for data transformation.

    Args:
        row: Dictionary representing a CSV row with column headers as keys

    Returns:
        Dictionary with field names and typed values ready for Firestore

    Examples:
        Input: {"DocumentId": "doc1", "age:int": "25", "name": "John"}
        Output: {"age": 25, "name": "John"}

        Input: {"DocumentId": "doc2", "age": "str: 30", "score:float": "95.5"}
        Output: {"age": "30", "score": 95.5}
    """
    fields = {}

    for header, value in row.items():
        # Parse header to extract field name and optional type hint
        field_name, type_hint = _parse_column_header(header)

        # Skip DocumentId field
        if field_name == 'DocumentId':
            continue

        # Convert value using type hint if present
        fields[field_name] = parse_firestore_value(value, type_hint=type_hint)

    return fields


def process_and_upload_csv(csv_file_path: str, collection_name: str, mode: str):
    """
    Orchestrates the process of reading the CSV, transforming data, and uploading.

    Args:
        csv_file_path: Path to the source CSV file.
        collection_name: The target collection ID (will be ignored in 'document' mode).
        mode: The upload strategy ('collection' or 'document').
    """
    if mode == 'document':
        raise NotImplementedError(
            'Document upload mode is not yet implemented.'
        )

    repository = FirestoreRepository()

    # The collection name argument takes priority, but use filename if not provided
    if not collection_name:
        base_filename = os.path.basename(csv_file_path)
        collection_name = os.path.splitext(base_filename)[0]

    logger.info(f'Targeting Firestore Collection: {collection_name}')

    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)

            for i, row in enumerate(reader, start=1):
                if 'DocumentId' not in row:
                    logger.warning(
                        f"Skipping row {i}: 'DocumentId' field missing."
                    )
                    continue

                document_id = row['DocumentId']
                fields = get_fields(row)

                repository.upload_document(collection_name, document_id, fields)

    except FileNotFoundError:
        logger.error(f'CSV file not found at path: {csv_file_path}')
        raise
    except Exception as e:
        logger.error(f'An error occurred during CSV processing:{e}')
        raise

    logging.info('Data added to Firestore successfully!')
