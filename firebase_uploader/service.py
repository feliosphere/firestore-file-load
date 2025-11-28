# firebase_uploader/service.py
import csv
import logging
import os

from .firestore_repository import FirestoreRepository

logger = logging.getLogger(__name__)


def get_fields(row: dict) -> dict:
    """
    Transforms a CSV row (dict) into a Firestore-ready dict,
    performing type conversion and excluding the DocumentId field.

    This is your core business logic for data transformation.
    """
    fields = {}
    for key, value in row.items():
        if key == 'DocumentId':
            continue

        if isinstance(value, str):
            value = value.strip()
            if value.isdigit():
                fields[key] = int(value)
            elif value.replace('.', '', 1).isdigit():
                fields[key] = float(value)
            else:
                fields[key] = value
        else:
            fields[key] = value  # Preserve non-string types

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
