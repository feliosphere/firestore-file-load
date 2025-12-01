# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

"""Tests for MockRepository functionality."""

import pytest

from tests.mock_repository import MockRepository


@pytest.fixture
def mock_repo():
    """Fixture that creates a fresh MockRepository for each test."""
    return MockRepository()


class TestMockRepositoryBasic:
    """Tests for basic MockRepository functionality."""

    def test_upload_single_document(self, mock_repo):
        """Test uploading a single document."""
        mock_repo.upload_document('col1', 'doc1', {'name': 'Alice', 'age': 25})

        doc = mock_repo.get_document('col1', 'doc1')
        assert doc is not None
        assert doc['name'] == 'Alice'
        assert doc['age'] == 25

    def test_upload_multiple_documents(self, mock_repo):
        """Test uploading multiple documents."""
        mock_repo.upload_document('col1', 'doc1', {'name': 'Alice'})
        mock_repo.upload_document('col1', 'doc2', {'name': 'Bob'})
        mock_repo.upload_document('col2', 'doc3', {'name': 'Charlie'})

        assert len(mock_repo.uploaded_documents) == 3
        assert len(mock_repo.collections['col1']) == 2
        assert len(mock_repo.collections['col2']) == 1

    def test_get_document_not_found(self, mock_repo):
        """Test retrieving a non-existent document returns None."""
        doc = mock_repo.get_document('col1', 'doc1')
        assert doc is None

    def test_get_all_documents(self, mock_repo):
        """Test retrieving all uploaded documents."""
        mock_repo.upload_document('col1', 'doc1', {'field': 'value1'})
        mock_repo.upload_document('col1', 'doc2', {'field': 'value2'})

        all_docs = mock_repo.get_all_documents()
        assert len(all_docs) == 2
        assert all_docs[0]['document_id'] == 'doc1'
        assert all_docs[1]['document_id'] == 'doc2'

    def test_clear(self, mock_repo):
        """Test clearing all documents."""
        mock_repo.upload_document('col1', 'doc1', {'field': 'value'})
        assert len(mock_repo.uploaded_documents) == 1

        mock_repo.clear()
        assert len(mock_repo.uploaded_documents) == 0
        assert len(mock_repo.collections) == 0

    def test_get_upload_count(self, mock_repo):
        """Test getting the upload count."""
        assert mock_repo.get_upload_count() == 0

        mock_repo.upload_document('col1', 'doc1', {'field': 'value'})
        assert mock_repo.get_upload_count() == 1

        mock_repo.upload_document('col1', 'doc2', {'field': 'value'})
        assert mock_repo.get_upload_count() == 2


class TestMockRepositoryMergeBehavior:
    """Tests for merge vs. overwrite behavior."""

    def test_merge_true_updates_existing_fields(self, mock_repo):
        """Test that merge=True updates existing document fields."""
        # Initial upload
        mock_repo.upload_document(
            'col1', 'doc1', {'name': 'Alice', 'age': 25}, merge=True
        )

        # Update with merge
        mock_repo.upload_document(
            'col1', 'doc1', {'age': 26, 'city': 'NYC'}, merge=True
        )

        doc = mock_repo.get_document('col1', 'doc1')
        assert doc['name'] == 'Alice'  # Original field preserved
        assert doc['age'] == 26  # Field updated
        assert doc['city'] == 'NYC'  # New field added

    def test_merge_false_replaces_document(self, mock_repo):
        """Test that merge=False replaces entire document."""
        # Initial upload
        mock_repo.upload_document(
            'col1', 'doc1', {'name': 'Alice', 'age': 25}, merge=False
        )

        # Overwrite with merge=False
        mock_repo.upload_document(
            'col1', 'doc1', {'age': 26, 'city': 'NYC'}, merge=False
        )

        doc = mock_repo.get_document('col1', 'doc1')
        assert 'name' not in doc  # Original field removed
        assert doc['age'] == 26
        assert doc['city'] == 'NYC'

    def test_merge_default_is_true(self, mock_repo):
        """Test that merge defaults to True when not specified."""
        # Initial upload without specifying merge
        mock_repo.upload_document('col1', 'doc1', {'name': 'Alice', 'age': 25})

        # Update without specifying merge
        mock_repo.upload_document('col1', 'doc1', {'age': 26})

        doc = mock_repo.get_document('col1', 'doc1')
        assert (
            doc['name'] == 'Alice'
        )  # Original field preserved (merge=True default)
        assert doc['age'] == 26

    def test_merge_on_new_document(self, mock_repo):
        """Test that merge=True on new document creates it normally."""
        mock_repo.upload_document('col1', 'doc1', {'name': 'Alice'}, merge=True)

        doc = mock_repo.get_document('col1', 'doc1')
        assert doc is not None
        assert doc['name'] == 'Alice'

    def test_overwrite_on_new_document(self, mock_repo):
        """Test that merge=False on new document creates it normally."""
        mock_repo.upload_document(
            'col1', 'doc1', {'name': 'Alice'}, merge=False
        )

        doc = mock_repo.get_document('col1', 'doc1')
        assert doc is not None
        assert doc['name'] == 'Alice'

    def test_multiple_merges(self, mock_repo):
        """Test multiple merge operations on same document."""
        mock_repo.upload_document(
            'col1', 'doc1', {'field1': 'value1'}, merge=True
        )
        mock_repo.upload_document(
            'col1', 'doc1', {'field2': 'value2'}, merge=True
        )
        mock_repo.upload_document(
            'col1', 'doc1', {'field3': 'value3'}, merge=True
        )

        doc = mock_repo.get_document('col1', 'doc1')
        assert doc['field1'] == 'value1'
        assert doc['field2'] == 'value2'
        assert doc['field3'] == 'value3'

    def test_merge_then_overwrite(self, mock_repo):
        """Test merge followed by overwrite."""
        # Merge operations
        mock_repo.upload_document(
            'col1', 'doc1', {'field1': 'value1'}, merge=True
        )
        mock_repo.upload_document(
            'col1', 'doc1', {'field2': 'value2'}, merge=True
        )

        # Verify merge worked
        doc = mock_repo.get_document('col1', 'doc1')
        assert 'field1' in doc
        assert 'field2' in doc

        # Now overwrite
        mock_repo.upload_document(
            'col1', 'doc1', {'field3': 'value3'}, merge=False
        )

        # Verify overwrite
        doc = mock_repo.get_document('col1', 'doc1')
        assert 'field1' not in doc
        assert 'field2' not in doc
        assert doc['field3'] == 'value3'

    def test_upload_history_records_merge_flag(self, mock_repo):
        """Test that upload history records the merge flag."""
        mock_repo.upload_document(
            'col1', 'doc1', {'field': 'value'}, merge=True
        )
        mock_repo.upload_document(
            'col1', 'doc2', {'field': 'value'}, merge=False
        )

        history = mock_repo.get_all_documents()
        assert history[0]['merge'] is True
        assert history[1]['merge'] is False

    def test_merge_with_nested_structures(self, mock_repo):
        """Test merge behavior with nested dictionaries."""
        # Initial document with nested structure
        mock_repo.upload_document(
            'col1',
            'doc1',
            {'user': {'name': 'Alice', 'age': 25}, 'active': True},
            merge=True,
        )

        # Update with merge
        mock_repo.upload_document(
            'col1', 'doc1', {'user': {'age': 26, 'city': 'NYC'}}, merge=True
        )

        doc = mock_repo.get_document('col1', 'doc1')
        # Note: Python's dict.update() does shallow merge, so nested dict gets replaced
        assert doc['user']['age'] == 26
        assert doc['user']['city'] == 'NYC'
        assert 'name' not in doc['user']  # Nested dict was replaced, not merged
        assert doc['active'] is True  # Top-level field preserved
