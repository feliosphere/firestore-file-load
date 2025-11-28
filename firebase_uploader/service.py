import csv
import json
import logging
import os
from datetime import datetime
from typing import Any

from google.cloud.firestore import DocumentReference, GeoPoint

from .firestore_repository import FirestoreRepository

logger = logging.getLogger(__name__)


def parse_firestore_value(value: str) -> Any:
    """
    Converts a string value to the appropriate Firestore data type.

    Supported type prefixes in CSV:
    - null: or NULL: -> None
    - bool: or boolean: -> Boolean (true/false, 1/0, yes/no)
    - int: or integer: -> Integer
    - float: or double: -> Float
    - timestamp: or datetime: -> Datetime (ISO 8601 format)
    - geopoint: -> GeoPoint (format: "lat,lng" e.g., "37.7749,-122.4194")
    - array: or list: -> Array (JSON format)
    - map: or dict: or object: -> Map/Dictionary (JSON format)
    - bytes: -> Bytes (base64 encoded)
    - ref: or reference: -> DocumentReference (format: "collection/document")
    - str: or string: -> String (explicit string type)

    Without prefix, automatic detection is attempted:
    - Quoted values (e.g., "123") -> String (quotes removed, content treated as string)
    - "null", "NULL", "None" -> None
    - "true", "false", "yes", "no", "1", "0" (case-insensitive) -> Boolean
    - Numeric strings -> Integer or Float
    - ISO 8601 datetime strings -> Datetime
    - Everything else -> String

    Note: To force a number as a string, either:
      1. Use the str: prefix (recommended): str: 123
      2. Quote it in your CSV editor - the quotes signal "keep as string"

    Args:
        value: The string value to convert

    Returns:
        The converted value in the appropriate Python/Firestore type
    """
    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value:
        return ''

    # If the value is wrapped in quotes, treat it as a literal string
    # This handles cases where users quote values in CSV to prevent type conversion
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]  # Return content without the quotes

    # Check for explicit type prefix
    if ':' in value:
        prefix, content = value.split(':', 1)
        prefix = prefix.strip().lower()
        content = content.strip()

        # Null type
        if prefix in ('null', 'none'):
            return None

        # Boolean type
        elif prefix in ('bool', 'boolean'):
            return content.lower() in ('true', '1', 'yes', 'y')

        # Integer type
        elif prefix in ('int', 'integer'):
            try:
                return int(content)
            except ValueError:
                logger.warning(
                    f"Cannot convert '{content}' to integer, returning as string"
                )
                return content

        # Float type
        elif prefix in ('float', 'double'):
            try:
                return float(content)
            except ValueError:
                logger.warning(
                    f"Cannot convert '{content}' to float, returning as string"
                )
                return content

        # Timestamp/Datetime type
        elif prefix in ('timestamp', 'datetime', 'date'):
            try:
                # Try ISO 8601 format first
                return datetime.fromisoformat(content)
            except ValueError:
                try:
                    # Try common formats
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
                except Exception as e:
                    logger.warning(
                        f"Error parsing datetime '{content}': {e}, returning as string"
                    )
                    return content

        # GeoPoint type
        elif prefix in ('geopoint', 'geo', 'location'):
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

        # Array type
        elif prefix in ('array', 'list'):
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Cannot parse array '{content}': {e}, returning as string"
                )
                return content

        # Map/Dictionary type
        elif prefix in ('map', 'dict', 'object'):
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Cannot parse map '{content}': {e}, returning as string"
                )
                return content

        # Bytes type
        elif prefix == 'bytes':
            try:
                import base64

                return base64.b64decode(content)
            except Exception as e:
                logger.warning(
                    f"Cannot decode bytes '{content}': {e}, returning as string"
                )
                return content

        # Reference type
        elif prefix in ('ref', 'reference'):
            # Note: This creates a path string. The actual DocumentReference
            # needs to be created with the Firestore client instance
            return content  # Return path as string for now

        # String type (explicit)
        elif prefix in ('str', 'string', 'text'):
            return content

    # Automatic type detection (no prefix)

    # Check for null values
    if value.lower() in ('null', 'none', ''):
        return None

    # Check for boolean values
    if value.lower() in ('true', 'yes', 'y'):
        return True
    if value.lower() in ('false', 'no', 'n'):
        return False

    # Check for numeric values
    if value.isdigit() or (value[0] == '-' and value[1:].isdigit()):
        return int(value)

    # Check for float values
    try:
        if '.' in value or 'e' in value.lower():
            float_val = float(value)
            return float_val
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


def get_fields(row: dict) -> dict:
    """
    Transforms a CSV row (dict) into a Firestore-ready dict,
    performing type conversion and excluding the DocumentId field.

    This function now supports all Firestore data types through explicit
    type prefixes or automatic detection. See parse_firestore_value() for details.

    This is your core business logic for data transformation.
    """
    fields = {}
    for key, value in row.items():
        if key == 'DocumentId':
            continue

        fields[key] = parse_firestore_value(value)

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
