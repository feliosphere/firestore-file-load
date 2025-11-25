import argparse
import csv
import logging
import os
import sys

import firebase_admin
from firebase_admin import credentials, firestore


def main(csv_file_path):
    logger.debug("csv file: {}".format(csv_file_path))

    db = connect_to_firestore()

    base_filename = os.path.basename(csv_file_path)
    collectionId = os.path.splitext(base_filename)[0]
    logger.debug("collectionId: {}".format(collectionId))

    with open(csv_file_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            documentId = row["DocumentId"]
            fields = get_fields(row)
            doc_ref = db.collection(collectionId).document(documentId)
            doc_ref.set(fields)

    logging.info("Data added to Firestore emulator successfully!")


def connect_to_firestore():
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    logger.debug(
        "FIRESTORE_EMULATOR_HOST: {}".format(os.environ.get("FIRESTORE_EMULATOR_HOST"))
    )
    cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred)

    return firestore.client()


def get_fields(row):
    fields = {}
    for key, value in row.items():
        if key != "DocumentId":
            if value.isdigit():
                fields[key] = int(value)
            elif value.replace(".", "", 1).isdigit():
                fields[key] = float(value)
            else:
                fields[key] = value
    return fields


def parse_args():
    parser = argparse.ArgumentParser(
        description="A simple CLI tool for csv to Firestore"
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="print debug messages",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="verbose output",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    parser.add_argument("csv_file_path", type=str, help="csv file path")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        level=args.loglevel,
        format="{asctime} - {levelname} :\t{message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )

    logger = logging.getLogger()

    sys.exit(main(args.csv_file_path))
