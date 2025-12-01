# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

"""Mock Repository for testing without Firebase connections."""

from firebase_uploader.uploader_interface import UploaderInterface


class MockRepository(UploaderInterface):
    """
    Mock implementation of UploaderInterface for testing.

    Stores uploaded documents in memory instead of uploading to Firestore.
    """

    def __init__(self):
        """Initialize the mock repository with empty storage."""
        self.uploaded_documents = []
        self.collections = {}

    def upload_document(
        self,
        collection_id: str,
        document_id: str,
        fields: dict,
        merge: bool = True,
    ):
        """
        Mock upload that stores the document in memory.

        Args:
            collection_id: The collection name
            document_id: The document ID
            fields: The document fields
            merge: If True, merge with existing document; if False, replace
        """
        # Store in list for ordered access
        self.uploaded_documents.append(
            {
                'collection_id': collection_id,
                'document_id': document_id,
                'fields': fields,
                'merge': merge,
            }
        )

        # Store in dict for collection-based access
        if collection_id not in self.collections:
            self.collections[collection_id] = {}

        if merge and document_id in self.collections[collection_id]:
            # Merge mode: update existing fields
            existing = self.collections[collection_id][document_id]
            existing.update(fields)
        else:
            # Overwrite mode or new document
            self.collections[collection_id][document_id] = fields

    def get_document(self, collection_id: str, document_id: str):
        """
        Retrieve a document from the mock storage.

        Args:
            collection_id: The collection name
            document_id: The document ID

        Returns:
            The document fields or None if not found
        """
        if collection_id in self.collections:
            return self.collections[collection_id].get(document_id)
        return None

    def get_all_documents(self):
        """
        Get all uploaded documents in order.

        Returns:
            List of all uploaded documents
        """
        return self.uploaded_documents

    def clear(self):
        """Clear all stored documents."""
        self.uploaded_documents = []
        self.collections = {}

    def get_upload_count(self):
        """
        Get the number of upload operations performed.

        Returns:
            Number of times upload_document was called
        """
        return len(self.uploaded_documents)
