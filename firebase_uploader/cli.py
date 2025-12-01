# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

import argparse
import logging
import os
import sys
from pathlib import Path

from firebase_uploader import collection_spec

from . import service

logger = logging.getLogger(__name__)


def parse_args():
    """Defines and parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description='CLI tool to upload CSV to Firestore.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # File Inputs
    files_group = parser.add_argument_group('File Inputs')

    files_group.add_argument(
        'csv_file_path',
        type=Path,
        help='Path to the source CSV file.',
    )

    files_group.add_argument(
        '-s',
        '--schema',
        type=Path,
        default=None,
        help='Path to JSON Schema. Defaults to [csv_filename].json if not set.',
    )

    # Collection Configuration
    collection_group = parser.add_argument_group('Collection Options')

    collection_group.add_argument(
        '-c',
        '--collection',
        type=str,
        dest='collection_name',
        default=None,
        help='Override Firestore collection name.',
    )

    collection_group.add_argument(
        '--merge',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='Merge with existing docs. Use --no-merge to overwrite.',
    )

    # Connection / Environment
    conn_group = parser.add_argument_group('Connection Options')

    conn_group.add_argument(
        '--local',
        action='store_true',
        help='Connect to Firestore Emulator instead of Cloud.',
    )

    # Group 4
    logging_group = parser.add_argument_group('Logging and Debugging Options')
    logging_exclusive = logging_group.add_mutually_exclusive_group()

    logging_exclusive.add_argument(
        '-d',
        '--debug',
        help='Print debug messages.',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
    )
    logging_exclusive.add_argument(
        '-v',
        '--verbose',
        help='Verbose output (INFO level).',
        action='store_const',
        dest='loglevel',
        const=logging.INFO,
    )
    parser.set_defaults(loglevel=logging.WARNING)

    return parser.parse_args()


def cli_entrypoint():
    """The main entry point function for the CLI."""
    args = parse_args()

    # Configure logging based on CLI arguments
    logging.basicConfig(
        level=args.loglevel,
        format='{asctime} - {levelname} :\t{message}',
        style='{',
        datefmt='%Y-%m-%d %H:%M',
    )

    logger.debug('Starting CLI execution...')

    if args.local:
        os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
        logger.info(
            f'🔧 Mode: EMULATOR (Host: {os.environ.get("FIRESTORE_EMULATOR_HOST")})'
        )
    else:
        logger.info('☁️  Mode: CLOUD (Real Firestore)')
    logger.info(
        f'   Project: {os.environ.get("GOOGLE_CLOUD_PROJECT", "unknown")}'
    )

    spec = collection_spec.CollectionSpec(
        _file_path=args.csv_file_path,
        _schema_path=args.schema,
        _merge=args.merge,
        _name=args.collection_name,
    )

    try:
        # Call the service layer with the collected arguments
        service.process_and_upload_csv(spec)
        sys.exit(0)
    except Exception as e:
        logger.error('Upload failed due to an unhandled error.')
        logger.debug(e, exc_info=True)  # Print traceback in debug mode
        sys.exit(1)
