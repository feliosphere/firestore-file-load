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


def get_fields(row: dict) -> dict:
    """Transforms a raw CSV row (dict) into a typed Firestore-ready dict."""
    fields = {}

    for header, value in row.items():
        field_name, type_hint = _parse_column_header(header)

        if field_name == 'DocumentId':
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


def process_and_upload_csv(
    # csv_file_path: str,
    # collection_name: str,
    spec: CollectionSpec,
):
    """
    Reads CSV with Pandas, groups by DocumentId, applies schema, and uploads.
    """
    csv_file_path = spec.file_path
    repository = FirestoreRepository()

    # if not collection_name:
    #     base_filename = os.path.basename(csv_file_path)
    #     collection_name = os.path.splitext(base_filename)[0]

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
                clean_row = get_fields(raw_row)

                # Schema Application
                if schema:
                    key_col = schema.get('key_column', 'id')

                    if key_col in clean_row and clean_row[key_col]:
                        doc_key = str(clean_row[key_col])
                        nested_data = apply_schema_mapping(
                            clean_row, schema['structure']
                        )
                        firestore_doc[doc_key] = nested_data
                    else:
                        logger.warning(
                            f"Skipping row in {doc_id_str}: Missing key column '{key_col}'"
                        )

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
