import logging

from firebase_admin import credentials, firestore, initialize_app

from .uploader_interface import UploaderInterface

logger = logging.getLogger(__name__)


class FirestoreRepository(UploaderInterface):
    def __init__(self):
        """
        The connection is established and stored when the class is INSTANTIATED.
        """
        self._db_client = self._connect_to_firestore()

    def _connect_to_firestore(self):
        """
        Initializes the Firebase Admin SDK and returns a Firestore client.
        """
        try:
            cred = credentials.ApplicationDefault()

            initialize_app(cred)
        except ValueError as e:
            logger.error(f'Firebase already initialized: {e}')
        except Exception as e:
            logger.error(f'Failed to initialize Firebase: {e}')
            raise

        return firestore.client()

    def upload_document(
        self, collection_id: str, document_id: str, fields: dict
    ):
        """
        Uploads a single document to a specified Firestore collection.
        Uses the internal _db_client without it being passed as an argument.
        """
        try:
            doc_ref = self._db_client.collection(collection_id).document(
                document_id
            )
            doc_ref.set(fields)
            logger.debug(f'Document {document_id} uploaded to {collection_id}.')
        except Exception as e:
            logger.error(
                f'Failed to upload document {document_id} to {collection_id}: %s',
                e,
            )
            raise
