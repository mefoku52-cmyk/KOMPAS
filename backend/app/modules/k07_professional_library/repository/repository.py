from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.k07_professional_library.domain.models import LibraryItem, LibraryTag, LibraryVersion


class K07Repository:
    def __init__(self, db: Session):
        self.db = db

    def create_item(self, *, school_id: uuid.UUID, owner_teacher_user_id: uuid.UUID, title: str, description: str | None = None, is_demo: bool = False) -> LibraryItem:
        obj = LibraryItem(school_id=school_id, owner_teacher_user_id=owner_teacher_user_id, title=title, description=description, archived=False, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_item(self, item_id: uuid.UUID) -> LibraryItem | None:
        return self.db.get(LibraryItem, item_id)

    def list_items(self, owner_teacher_user_id: uuid.UUID, school_id: uuid.UUID, include_archived: bool = True):
        stmt = select(LibraryItem).where(LibraryItem.owner_teacher_user_id == owner_teacher_user_id, LibraryItem.school_id == school_id)
        if not include_archived:
            stmt = stmt.where(LibraryItem.archived.is_(False))
        return list(self.db.execute(stmt).scalars().all())

    def archive_item(self, item: LibraryItem) -> LibraryItem:
        item.archived = True
        self.db.flush()
        return item

    def add_version(self, *, school_id: uuid.UUID, item_id: uuid.UUID, version_number: int, storage_key: str | None = None, content_text: str | None = None, note: str | None = None, is_demo: bool = False) -> LibraryVersion:
        obj = LibraryVersion(school_id=school_id, item_id=item_id, version_number=version_number, storage_key=storage_key, content_text=content_text, note=note, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_versions(self, item_id: uuid.UUID):
        stmt = select(LibraryVersion).where(LibraryVersion.item_id == item_id).order_by(LibraryVersion.version_number.asc())
        return list(self.db.execute(stmt).scalars().all())

    def add_tag(self, *, school_id: uuid.UUID, item_id: uuid.UUID, tag: str, is_demo: bool = False) -> LibraryTag:
        obj = LibraryTag(school_id=school_id, item_id=item_id, tag=tag, is_demo=is_demo)
        self.db.add(obj)
        self.db.flush()
        return obj

    def list_tags(self, item_id: uuid.UUID):
        stmt = select(LibraryTag.tag).where(LibraryTag.item_id == item_id)
        return [r[0] for r in self.db.execute(stmt).all()]
