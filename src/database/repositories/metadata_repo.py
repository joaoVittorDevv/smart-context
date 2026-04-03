"""
Project Metadata repository for managing project-level settings.
"""

from typing import Optional, List
import json
from src.database.models import ProjectMetadata
from src.database.repositories.base import BaseRepository


class MetadataRepository(BaseRepository[ProjectMetadata]):
    """
    Repository for project metadata and settings.
    """

    def __init__(self, session):
        super().__init__(session, ProjectMetadata)

    def get_setting(self, key: str, default=None) -> Optional[str]:
        """Get a specific metadata setting by key."""
        meta = self.session.query(ProjectMetadata).filter_by(key=key).first()
        return meta.value if meta else default

    def set_setting(self, key: str, value: str):
        """Set a specific metadata setting by key."""
        meta = self.session.query(ProjectMetadata).filter_by(key=key).first()
        if meta:
            meta.value = value
        else:
            meta = ProjectMetadata(key=key, value=value)
            self.session.add(meta)
        return meta

    def get_included_folders(self) -> List[str]:
        """Get the list of folders to be indexed."""
        folders_json = self.get_setting('included_folders', '[]')
        try:
            return json.loads(folders_json)
        except json.JSONDecodeError:
            return []

    def set_included_folders(self, folders: List[str]):
        """Set the list of folders to be indexed."""
        self.set_setting('included_folders', json.dumps(folders))

    def get_project_root(self) -> Optional[str]:
        """Get the stored project root path."""
        return self.get_setting('project_root')

    def set_project_root(self, root_path: str):
        """Set the project root path."""
        self.set_setting('project_root', root_path)
