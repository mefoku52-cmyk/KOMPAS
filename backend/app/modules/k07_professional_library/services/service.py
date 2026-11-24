from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.permissions.policy import Scope, authorize
from app.modules.k07_professional_library.repository.repository import K07Repository
from app.shared.storage import FileStorage, LocalFileStorage
from app.shared.types import Principal, Role


class K07Service:
    def __init__(self, db: Session, storage: FileStorage | None = None):
        self.db = db
        self.repo = K07Repository(db)
        self.storage = storage or LocalFileStorage(".data/storage")

    def _owner_ctx(self, principal: Principal, school_id: uuid.UUID, owner_teacher_user_id: uuid.UUID):
        if principal.is_system:
            return {"school_id": school_id, "system_internal": True}
        if principal.role == Role.TEACHER and principal.user_id == owner_teacher_user_id:
            return {"scope": Scope.SELF.value, "owner_user_id": owner_teacher_user_id, "school_id": school_id}
        return {"school_id": school_id}

    def _auth(self, principal: Principal, action: str, resource: str, context: dict):
        decision = authorize(principal, action, resource, context=context, db=self.db)
        if not decision.allowed:
            audit_write(self.db, principal, action, resource, None, "denied", {"reason": decision.reason})
            raise PermissionError(decision.reason)

    def create_item(self, principal: Principal, *, school_id: uuid.UUID, owner_teacher_user_id: uuid.UUID, title: str, description: str | None = None, is_demo: bool = False):
        action = "k07.create_item"
        ctx = self._owner_ctx(principal, school_id, owner_teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_library_item:teacher:{owner_teacher_user_id}", ctx)
        item = self.repo.create_item(school_id=school_id, owner_teacher_user_id=owner_teacher_user_id, title=title, description=description, is_demo=is_demo)
        audit_write(self.db, principal, action, f"teacher_workspace_library_item:{item.id}", None, "success")
        return item

    def add_version(self, principal: Principal, item_id: uuid.UUID, *, version_number: int, content_bytes: bytes | None = None, content_text: str | None = None, note: str | None = None, is_demo: bool = False):
        action = "k07.add_version"
        item = self.repo.get_item(item_id)
        if not item:
            raise ValueError("item_not_found")
        ctx = self._owner_ctx(principal, item.school_id, item.owner_teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_library_item:{item.id}", ctx)
        from app.modules.k07_professional_library.domain.models import LibraryVersion
        existing = self.db.query(LibraryVersion.id).filter(
            LibraryVersion.item_id == item.id, LibraryVersion.version_number == version_number
        ).first()
        if existing is not None:
            raise ValueError("version_number_exists")
        storage_key = None
        if content_bytes is not None:
            storage_key = f"library/{item.id}/v{version_number}.bin"
            self.storage.save(storage_key, content_bytes)
        ver = self.repo.add_version(school_id=item.school_id, item_id=item.id, version_number=version_number, storage_key=storage_key, content_text=content_text, note=note, is_demo=is_demo)
        audit_write(self.db, principal, action, f"teacher_workspace_library_version:{ver.id}", None, "success")
        return ver

    def add_tag(self, principal: Principal, item_id: uuid.UUID, tag: str, is_demo: bool = False):
        action = "k07.add_tag"
        item = self.repo.get_item(item_id)
        if not item:
            raise ValueError("item_not_found")
        ctx = self._owner_ctx(principal, item.school_id, item.owner_teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_library_item:{item.id}", ctx)
        t = self.repo.add_tag(school_id=item.school_id, item_id=item.id, tag=tag, is_demo=is_demo)
        audit_write(self.db, principal, action, f"teacher_workspace_library_tag:{t.id}", None, "success")
        return t

    def archive_item(self, principal: Principal, item_id: uuid.UUID):
        action = "k07.archive_item"
        item = self.repo.get_item(item_id)
        if not item:
            raise ValueError("item_not_found")
        ctx = self._owner_ctx(principal, item.school_id, item.owner_teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_library_item:{item.id}", ctx)
        item = self.repo.archive_item(item)
        audit_write(self.db, principal, action, f"teacher_workspace_library_item:{item.id}", None, "success")
        return item

    def list_items(self, principal: Principal, *, school_id: uuid.UUID, owner_teacher_user_id: uuid.UUID, include_archived: bool = True):
        action = "k07.list_items"
        ctx = self._owner_ctx(principal, school_id, owner_teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_library_item:teacher:{owner_teacher_user_id}", ctx)
        rows = self.repo.list_items(owner_teacher_user_id, school_id, include_archived=include_archived)
        audit_write(self.db, principal, action, f"teacher_workspace_library_item:teacher:{owner_teacher_user_id}", None, "success", {"count": len(rows)})
        return rows

    def list_versions(self, principal: Principal, item_id: uuid.UUID):
        action = "k07.list_versions"
        item = self.repo.get_item(item_id)
        if not item:
            raise ValueError("item_not_found")
        ctx = self._owner_ctx(principal, item.school_id, item.owner_teacher_user_id)
        self._auth(principal, action, f"teacher_workspace_library_item:{item.id}", ctx)
        rows = self.repo.list_versions(item_id)
        audit_write(self.db, principal, action, f"teacher_workspace_library_item:{item.id}", None, "success", {"count": len(rows)})
        return rows
