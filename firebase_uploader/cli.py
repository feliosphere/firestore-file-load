# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

import argparse
import logging
import os
import sys

from . import service

logger = logging.getLogger(__name__)


def parse_args():
    """Defines and parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description='A simple CLI tool for csv to Firestore'
    )
    # Logging arguments
    #
    logging_group = parser.add_argument_group('Logging and Debugging Options')
    logging_group.add_argument(
        '-d',
        '--debug',
        help='print debug messages',
        action='store_const',
        dest='debug',
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    logging_group.add_argument(
        '-v',
        '--verbose',
        help='verbose output (INFO level)',
        action='store_const',
        dest='loglevel',
        const=logging.INFO,
        default=logging.WARNING,
    )

    # CSV file path argument
    parser.add_argument('csv_file_path', type=str, help='Path to the CSV file.')

    # NEW Feature: Collection name argument
    parser.add_argument(
        '-c',
        '--collection',
        type=str,
        default='',
        help='Target Firestore collection name. Defaults to CSV filename.',
    )

    parser.add_argument(
        '--local',
        action='store_true',
        help='Use the Firestore emulator instead of Cloud Firestore',
    )

    return parser.parse_args()


def cli_entrypoint():
    """The main entry point function for the CLI."""
    args = parse_args()

    # Configure logging based on CLI arguments
    logging.basicConfig(
        level=min(args.debug, args.loglevel),
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

    try:
        # Call the service layer with the collected arguments
        service.process_and_upload_csv(args.csv_file_path, args.collection)
        sys.exit(0)
    except Exception as e:
        logger.error('Upload failed due to an unhandled error.')
        logger.debug(e, exc_info=True)  # Print traceback in debug mode
        sys.exit(1)
