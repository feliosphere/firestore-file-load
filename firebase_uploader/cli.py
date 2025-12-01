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
        prog='ffload',
        description=(
            'Upload CSV data to Google Cloud Firestore with automatic type conversion '
            'and optional schema-driven transformation.'
        ),
        epilog=(
            'Examples:\n'
            '  %(prog)s data.csv                      # Basic upload\n'
            '  %(prog)s data.csv -s schema.json       # With custom schema\n'
            '  %(prog)s data.csv -c products --local  # To local emulator\n'
            '  %(prog)s data.csv --no-merge -v        # Overwrite mode with verbose output'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # File Inputs
    files_group = parser.add_argument_group('File Inputs')

    files_group.add_argument(
        'csv_file_path',
        type=Path,
        metavar='CSV_FILE',
        help='Path to the CSV file to upload (must contain DocumentId column).',
    )

    files_group.add_argument(
        '-s',
        '--schema',
        type=Path,
        metavar='SCHEMA_FILE',
        default=None,
        help=(
            'Path to JSON schema file for transforming CSV structure. '
            'If not specified, auto-detects [csv_filename].json. '
            'Without schema, rows are grouped into "items" arrays.'
        ),
    )

    # Collection Configuration
    collection_group = parser.add_argument_group('Collection Options')

    collection_group.add_argument(
        '-c',
        '--collection',
        type=str,
        dest='collection_name',
        metavar='NAME',
        default=None,
        help='Firestore collection name (defaults to CSV filename without extension).',
    )

    collection_group.add_argument(
        '--merge',
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            'Merge with existing documents (preserves unmentioned fields). '
            'Use --no-merge to replace entire documents.'
        ),
    )

    # Connection / Environment
    conn_group = parser.add_argument_group('Connection Options')

    conn_group.add_argument(
        '--local',
        action='store_true',
        help='Use local Firestore emulator at localhost:8080 instead of Cloud Firestore.',
    )

    # Logging and Debugging
    logging_group = parser.add_argument_group('Logging and Debugging Options')
    logging_exclusive = logging_group.add_mutually_exclusive_group()

    logging_exclusive.add_argument(
        '-d',
        '--debug',
        help='Enable debug logging (shows detailed execution and tracebacks).',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
    )
    logging_exclusive.add_argument(
        '-v',
        '--verbose',
        help='Enable verbose logging (shows INFO level messages).',
        action='store_const',
        dest='loglevel',
        const=logging.INFO,
    )
    parser.set_defaults(loglevel=logging.WARNING)

    args = parser.parse_args()

    # Validate CSV file exists
    if not args.csv_file_path.exists():
        parser.error(f'CSV file not found: {args.csv_file_path}')

    if not args.csv_file_path.is_file():
        parser.error(f'Path is not a file: {args.csv_file_path}')

    # Validate schema file if provided
    if args.schema is not None and not args.schema.exists():
        parser.error(f'Schema file not found: {args.schema}')

    return args


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

    # Display configuration
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

    # Log configuration details
    logger.info(f'📁 CSV File: {args.csv_file_path}')
    logger.info(
        f'📦 Collection: {args.collection_name or args.csv_file_path.stem}'
    )
    if args.schema:
        logger.info(f'📋 Schema: {args.schema}')
    logger.info(f'🔀 Merge Mode: {"ON" if args.merge else "OFF"}')

    spec = collection_spec.CollectionSpec(
        _file_path=args.csv_file_path,
        _schema_path=args.schema,
        _merge=args.merge,
        _name=args.collection_name,
    )

    try:
        # Call the service layer with the collected arguments
        service.process_and_upload_csv(spec)
        logger.info('✅ Upload completed successfully!')
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f'❌ File not found: {e}')
        logger.debug('Full traceback:', exc_info=True)
        sys.exit(1)
    except ValueError as e:
        logger.error(f'❌ Invalid data: {e}')
        logger.debug('Full traceback:', exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning('⚠️  Upload cancelled by user')
        sys.exit(130)
    except Exception as e:
        logger.error(f'❌ Upload failed: {e}')
        logger.debug('Full traceback:', exc_info=True)
        sys.exit(1)
