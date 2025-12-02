# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

import logging
from typing import Any

import pandas as pd

from .collection_spec import CollectionSpec
from .firestore_repository import FirestoreRepository
from .type_converters import (
    _auto_detect_type,
    _convert_by_type_prefix,
    _extract_type_prefix,
    _is_quoted_string,
    _parse_column_header,
)

logger = logging.getLogger(__name__)


def parse_firestore_value(value: Any, type_hint: str | None = None) -> Any:
    """Converts a string value to the appropriate Firestore data type."""
    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value:
        return ''

    if _is_quoted_string(value):
        return value[1:-1]

    prefix, content = _extract_type_prefix(value)
    if prefix is not None:
        return _convert_by_type_prefix(prefix, content)

    if type_hint is not None:
        type_hint = type_hint.strip().lower()
        return _convert_by_type_prefix(type_hint, value)

    return _auto_detect_type(value)


def get_fields(row: dict, include_document_id: bool = False) -> dict:
    """
    Transforms a raw CSV row (dict) into a typed Firestore-ready dict.

    Args:
        row: Raw CSV row dictionary
        include_document_id: If True, includes DocumentId in the result
                            (useful when DocumentId is referenced in schema)

    Returns:
        Dictionary with typed Firestore values
    """
    fields = {}

    for header, value in row.items():
        field_name, type_hint = _parse_column_header(header)

        if field_name == 'DocumentId' and not include_document_id:
            continue

        fields[field_name] = parse_firestore_value(value, type_hint=type_hint)

    return fields


def _is_effectively_empty(data: Any, schema: Any) -> bool:
    """
    Recursively checks if 'data' is empty.

    Crucial Logic:
    1. Primitives (Strings/Nulls) are empty if they are '' or None.
    2. Dictionaries are empty if ALL their non-literal values are empty.
    3. Lists are empty if ALL their items are empty.
    """
    if data is None:
        return True
    if isinstance(data, str) and data.strip() == '':
        return True

    if isinstance(data, dict) and isinstance(schema, dict):
        for key, value in data.items():
            field_schema = schema.get(key)

            if isinstance(field_schema, str) and field_schema.startswith(
                'literal:'
            ):
                continue

            if not _is_effectively_empty(value, field_schema):
                return False

        return True

    if isinstance(data, list):
        return all(_is_effectively_empty(v, schema) for v in data)

    return False


def apply_schema_mapping(row_data: dict, schema_structure: Any) -> Any:
    """
    Recursively transforms a flat row dictionary into a nested dictionary
    or list based on the provided schema structure.
    """
    if isinstance(schema_structure, dict):
        result = {}
        for target_key, source_mapping in schema_structure.items():
            # Recursively build the value
            val = apply_schema_mapping(row_data, source_mapping)
            result[target_key] = val
        return result

    elif isinstance(schema_structure, list):
        result_list = []
        for item_schema in schema_structure:
            candidate = apply_schema_mapping(row_data, item_schema)

            if not _is_effectively_empty(candidate, item_schema):
                result_list.append(candidate)

        return result_list

    elif isinstance(schema_structure, str):
        if schema_structure.startswith('literal:'):
            return schema_structure.split(':', 1)[1]

        return row_data.get(schema_structure)

    return None


def _apply_keyed_nesting(
    row_data: dict, schema: dict, current_level: dict
) -> None:
    """
    Recursively applies key-column-based nesting to build nested maps.

    This function handles schemas with nested key_column definitions,
    allowing for map-within-map structures (e.g., {world_a: {1: {...}, 2: {...}}}).

    Args:
        row_data: The processed row data (after type conversion)
        schema: Schema definition containing 'key_column' and 'structure'
        current_level: The current level dict to populate (modified in place)

    The function works by:
    1. Extracting the key value from row_data using schema['key_column']
    2. Checking if schema['structure'] contains another 'key_column' (deeper nesting)
    3. If yes: recurse to create nested maps
    4. If no: apply schema mapping to create final data structure
    """
    if 'key_column' not in schema:
        logger.warning('Schema missing key_column, cannot apply keyed nesting')
        return

    key_col = schema['key_column']
    structure = schema['structure']

    if key_col not in row_data:
        logger.warning(f"Missing key column '{key_col}' in row data")
        return

    doc_key = row_data[key_col]
    if doc_key is None or (isinstance(doc_key, str) and not doc_key):
        logger.warning(f"Empty key column '{key_col}' in row data")
        return

    # Convert key to string for Firestore compatibility
    # Firestore map keys must be strings
    doc_key_str = str(doc_key)

    if isinstance(structure, dict) and 'key_column' in structure:
        if doc_key_str not in current_level:
            current_level[doc_key_str] = {}

        _apply_keyed_nesting(row_data, structure, current_level[doc_key_str])
    else:
        nested_data = apply_schema_mapping(row_data, structure)
        current_level[doc_key_str] = nested_data


def process_and_upload_csv(
    spec: CollectionSpec,
):
    """
    Reads CSV with Pandas, groups by DocumentId, applies schema, and uploads.
    """
    csv_file_path = spec.file_path
    repository = FirestoreRepository()

    # LOAD THE SCHEMA
    schema = spec.get_schema()
    try:
        logger.info(f'Processing file: {csv_file_path}')

        # LOAD DATA
        df = pd.read_csv(csv_file_path, dtype=str, keep_default_na=False)

        if 'DocumentId' not in df.columns:
            raise ValueError("The CSV file is missing the 'DocumentId' column.")

        grouped = df.groupby('DocumentId')
        logger.info(f'Found {len(grouped)} unique documents to process.')

        # PROCESS GROUPS
        for document_id, group_df in grouped:
            doc_id_str = str(document_id)

            raw_rows = group_df.to_dict('records')
            firestore_doc = {}

            # Process each row in the group
            for raw_row in raw_rows:
                # Type Conversion
                clean_row = get_fields(
                    raw_row, include_document_id=bool(schema)
                )

                # Schema Application
                if schema:
                    _apply_keyed_nesting(clean_row, schema, firestore_doc)

                else:
                    # Fallback (No Schema)
                    if 'items' not in firestore_doc:
                        firestore_doc['items'] = []
                    firestore_doc['items'].append(clean_row)

            repository.upload_document(
                spec.name, doc_id_str, firestore_doc, spec.merge
            )

    except FileNotFoundError:
        logger.error(f'CSV file not found at path: {csv_file_path}')
        raise
    except Exception as e:
        logger.error(f'An error occurred: {e}')
        raise

    logger.info('Data added to Firestore successfully!')
