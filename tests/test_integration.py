# Copyright (c) 2025 Felipe Paucar
# Licensed under the MIT License

"""Integration tests for CSV processing with firebase_uploader."""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from firebase_uploader.collection_spec import CollectionSpec
from firebase_uploader.service import get_fields, process_and_upload_csv
from tests.mock_repository import MockRepository


@pytest.fixture
def temp_csv_file():
    """
    Fixture that creates a temporary CSV file and cleans it up after the test.

    Yields:
        Path to the temporary CSV file
    """
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False
        ) as f:
            temp_file = f.name
            yield f
    finally:
        if temp_file and Path(temp_file).exists():
            Path(temp_file).unlink()


@pytest.fixture
def mock_repo():
    """
    Fixture that creates a fresh MockRepository for each test.

    Returns:
        MockRepository instance
    """
    return MockRepository()


class TestCSVProcessing:
    """Integration tests for CSV processing with mock repository."""

    def test_process_simple_csv(self, temp_csv_file, mock_repo):
        """Test processing a simple CSV file."""
        # Create CSV content
        csv_content = """DocumentId,name,age,score
doc1,Alice,25,95.5
doc2,Bob,30,87.3
doc3,Charlie,35,92.1
"""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = temp_csv_file.name

        # Process the CSV with mock repository
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                document_id = row['DocumentId']
                fields = get_fields(row)
                mock_repo.upload_document(
                    'test_collection', document_id, fields
                )

        # Verify uploads
        assert len(mock_repo.uploaded_documents) == 3

        # Check first document
        doc1 = mock_repo.get_document('test_collection', 'doc1')
        assert doc1 is not None
        assert doc1['name'] == 'Alice'
        assert doc1['age'] == 25
        assert doc1['score'] == 95.5

        # Check second document
        doc2 = mock_repo.get_document('test_collection', 'doc2')
        assert doc2 is not None
        assert doc2['name'] == 'Bob'
        assert doc2['age'] == 30

    def test_process_csv_with_type_hints(self, temp_csv_file, mock_repo):
        """Test processing CSV with type hints in headers."""
        csv_content = """DocumentId,name,age:int,employee_id:str,active:bool
emp1,Alice,25,00123,true
emp2,Bob,30,00456,false
"""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = temp_csv_file.name

        # Process the CSV
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                document_id = row['DocumentId']
                fields = get_fields(row)
                mock_repo.upload_document('employees', document_id, fields)

        # Verify types are correct
        emp1 = mock_repo.get_document('employees', 'emp1')
        assert emp1 is not None
        assert emp1['age'] == 25
        assert isinstance(emp1['age'], int)
        assert emp1['employee_id'] == '00123'
        assert isinstance(emp1['employee_id'], str)
        assert emp1['active'] is True
        assert isinstance(emp1['active'], bool)

    def test_mock_repository_clear(self, mock_repo):
        """Test that mock repository clear works."""
        mock_repo.upload_document('col1', 'doc1', {'field': 'value'})
        assert len(mock_repo.uploaded_documents) == 1

        mock_repo.clear()
        assert len(mock_repo.uploaded_documents) == 0
        assert len(mock_repo.collections) == 0

    @pytest.mark.parametrize(
        'csv_content,collection,doc_id,expected_fields',
        [
            (
                'DocumentId,name,count\ndoc1,test,42\n',
                'col1',
                'doc1',
                {'name': 'test', 'count': 42},
            ),
            (
                'DocumentId,active:bool,score:float\ndoc2,true,98.5\n',
                'col2',
                'doc2',
                {'active': True, 'score': 98.5},
            ),
        ],
    )
    def test_various_csv_formats(
        self,
        temp_csv_file,
        mock_repo,
        csv_content,
        collection,
        doc_id,
        expected_fields,
    ):
        """Test processing various CSV formats with different data types."""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = temp_csv_file.name

        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                document_id = row['DocumentId']
                fields = get_fields(row)
                mock_repo.upload_document(collection, document_id, fields)

        doc = mock_repo.get_document(collection, doc_id)
        assert doc is not None
        assert doc == expected_fields


class TestCollectionSpecIntegration:
    """Integration tests using CollectionSpec with the full processing pipeline."""

    def test_process_csv_without_schema(
        self, temp_csv_file, mock_repo, monkeypatch
    ):
        """Test processing CSV without schema file."""
        csv_content = """DocumentId,name,age:int
doc1,Alice,25
doc2,Bob,30
"""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = Path(temp_csv_file.name)

        # Mock FirestoreRepository to use our mock
        monkeypatch.setattr(
            'firebase_uploader.service.FirestoreRepository',
            lambda: mock_repo,
        )

        spec = CollectionSpec(
            _file_path=csv_path,
            _merge=True,
        )

        process_and_upload_csv(spec)

        # Verify documents were uploaded
        assert mock_repo.get_upload_count() == 2
        doc1 = mock_repo.get_document(spec.name, 'doc1')
        assert doc1 is not None
        # Without schema, data goes into 'items' array
        assert 'items' in doc1
        assert len(doc1['items']) == 1
        assert doc1['items'][0]['name'] == 'Alice'
        assert doc1['items'][0]['age'] == 25

    def test_process_csv_with_schema(
        self, temp_csv_file, mock_repo, monkeypatch
    ):
        """Test processing CSV with schema file."""
        csv_content = """DocumentId,id,question,opt_a,opt_b
quiz1,Q1,What is 2+2?,3,4
"""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = Path(temp_csv_file.name)

        # Create schema file
        schema_path = csv_path.with_suffix('.json')
        schema_data = {
            'key_column': 'id',
            'structure': {
                'question': 'question',
                'options': [
                    {'id': 'literal:a', 'text': 'opt_a'},
                    {'id': 'literal:b', 'text': 'opt_b'},
                ],
            },
        }
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        try:
            # Mock FirestoreRepository
            monkeypatch.setattr(
                'firebase_uploader.service.FirestoreRepository',
                lambda: mock_repo,
            )

            spec = CollectionSpec(
                _file_path=csv_path,
                _merge=True,
            )

            process_and_upload_csv(spec)

            # Verify schema was applied
            doc = mock_repo.get_document(spec.name, 'quiz1')
            assert doc is not None
            assert 'Q1' in doc
            assert doc['Q1']['question'] == 'What is 2+2?'
            assert len(doc['Q1']['options']) == 2
            assert doc['Q1']['options'][0]['id'] == 'a'

        finally:
            if schema_path.exists():
                schema_path.unlink()

    def test_process_csv_with_merge_true(
        self, temp_csv_file, mock_repo, monkeypatch
    ):
        """Test processing with merge=True preserves existing fields."""
        csv_content = """DocumentId,name
doc1,Alice
"""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = Path(temp_csv_file.name)

        # Pre-populate document
        mock_repo.upload_document(
            csv_path.stem, 'doc1', {'name': 'Old', 'age': 25}, merge=False
        )

        # Mock FirestoreRepository
        monkeypatch.setattr(
            'firebase_uploader.service.FirestoreRepository',
            lambda: mock_repo,
        )

        spec = CollectionSpec(
            _file_path=csv_path,
            _merge=True,
        )

        process_and_upload_csv(spec)

        doc = mock_repo.get_document(spec.name, 'doc1')
        # Without schema, data is in items array
        assert 'items' in doc
        assert doc['items'][0]['name'] == 'Alice'  # Updated
        assert doc['age'] == 25  # Preserved from original (from pre-population)

    def test_process_csv_with_merge_false(
        self, temp_csv_file, mock_repo, monkeypatch
    ):
        """Test processing with merge=False replaces entire document."""
        csv_content = """DocumentId,name
doc1,Alice
"""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = Path(temp_csv_file.name)

        # Pre-populate document
        mock_repo.upload_document(
            csv_path.stem, 'doc1', {'name': 'Old', 'age': 25}, merge=False
        )

        # Mock FirestoreRepository
        monkeypatch.setattr(
            'firebase_uploader.service.FirestoreRepository',
            lambda: mock_repo,
        )

        spec = CollectionSpec(
            _file_path=csv_path,
            _merge=False,
        )

        process_and_upload_csv(spec)

        doc = mock_repo.get_document(spec.name, 'doc1')
        # Without schema, data is in items array
        assert 'items' in doc
        assert doc['items'][0]['name'] == 'Alice'
        assert 'age' not in doc  # Removed due to overwrite

    def test_process_csv_with_custom_collection_name(
        self, temp_csv_file, mock_repo, monkeypatch
    ):
        """Test processing with custom collection name."""
        csv_content = """DocumentId,name
doc1,Alice
"""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = Path(temp_csv_file.name)

        # Mock FirestoreRepository
        monkeypatch.setattr(
            'firebase_uploader.service.FirestoreRepository',
            lambda: mock_repo,
        )

        spec = CollectionSpec(
            _file_path=csv_path,
            _name='custom_collection',
            _merge=True,
        )

        process_and_upload_csv(spec)

        # Document should be in custom collection
        doc = mock_repo.get_document('custom_collection', 'doc1')
        assert doc is not None
        # Without schema, data is in items array
        assert 'items' in doc
        assert doc['items'][0]['name'] == 'Alice'

    def test_process_csv_with_grouped_rows(
        self, temp_csv_file, mock_repo, monkeypatch
    ):
        """Test processing CSV with multiple rows per DocumentId."""
        csv_content = """DocumentId,item,price:float
order1,Apple,1.50
order1,Banana,0.80
order2,Cherry,2.00
"""
        temp_csv_file.write(csv_content)
        temp_csv_file.flush()
        csv_path = Path(temp_csv_file.name)

        # Mock FirestoreRepository
        monkeypatch.setattr(
            'firebase_uploader.service.FirestoreRepository',
            lambda: mock_repo,
        )

        spec = CollectionSpec(
            _file_path=csv_path,
            _merge=True,
        )

        process_and_upload_csv(spec)

        # Verify grouped documents
        order1 = mock_repo.get_document(spec.name, 'order1')
        assert order1 is not None
        assert 'items' in order1
        assert len(order1['items']) == 2
        assert order1['items'][0]['item'] == 'Apple'
        assert order1['items'][1]['item'] == 'Banana'

        order2 = mock_repo.get_document(spec.name, 'order2')
        assert order2 is not None
        assert len(order2['items']) == 1
