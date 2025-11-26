from abc import ABC, abstractmethod


class UploaderInterface(ABC):
    """Abstract Base Class defining the contract for any data uploader."""

    @abstractmethod
    def upload_document(
        self, collection_id: str, document_id: str, fields: dict
    ):
        """Uploads a single data document to the data store."""
        pass
