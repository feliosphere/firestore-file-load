import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CollectionSpec:
    _file_path: Path  # The Data
    _merge: bool  # The Behavior
    _name: Optional[str] = None
    _schema_path: Optional[Path] = None  # The Structure
    _cached_schema: Optional[dict] = None  # Cache for loaded schema

    @property
    def file_path(self) -> Path:
        return self._file_path

    @property
    def merge(self) -> bool:
        return self._merge

    @property
    def name(self) -> str:
        # Your logic here (using .stem)
        return self._name or self.file_path.stem

    @property
    def schema_path(self) -> Path:
        return self._schema_path or self.file_path.with_suffix('.json')

    def get_schema(self) -> dict | None:
        """
        Loads the schema from the file if it exists.
        Returns None if no file is found (implying default structure).
        """
        # Return cached version if we already loaded it
        if self._cached_schema is not None:
            return self._cached_schema

        path = self.schema_path

        if not path.exists():
            logger.info('ℹ️ No schema.json found. Using default flat structure.')
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info('✅ Loaded custom schema.json')
                self._cached_schema = data  # Cache it
                return data
        except json.JSONDecodeError as e:
            # It's better to crash early or raise a clear error here
            raise ValueError(f'Invalid JSON in schema file {path}: {e}')
