#!/usr/bin/env python3
"""Administrácia KOMPAS: školy, používatelia, heslá, prechod roka, export auditu.

Heslá sa nikdy neodovzdávajú ako argument príkazového riadku. Použi --password-stdin,
premennú prostredia alebo interaktívny vstup.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import select  # noqa: E402

from app.core.audit.logger import AuditLog, verify_chain, write as audit_write  # noqa: E402
from app.core.config.settings import settings  # noqa: E402
from app.core.database.session import SessionLocal  # noqa: E402
from app.core.rollover import rollover_school_year  # noqa: E402
from app.core.security.auth import hash_password, validate_password_policy  # noqa: E402
from app.shared.identity import RoleAssignment, User  # noqa: E402
from app.shared.school import School, SchoolYear  # noqa: E402
from app.shared.types import SYSTEM_USER_ID, Principal, Role, system_principal  # noqa: E402


def _system_for_school(school_id: uuid.UUID) -> Principal:
    return Principal(user_id=SYSTEM_USER_ID, role=None, school_id=school_id, scopes=("system",), is_system=True)


def _output(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))


def _read_password(args: argparse.Namespace, *, confirm: bool = False) -> str:
    if getattr(args, "password_stdin", False):
        value = sys.stdin.readline().rstrip("\n")
        if not value:
            raise SystemExit("password is empty")
        return value
    env_name = getattr(args, "password_env", None)
    if env_name:
        value = os.environ.get(env_name, "")
        if not value:
            raise SystemExit(f"environment variable {env_name} is empty")
        return value
    first = getpass.getpass("Password: ")
    if confirm:
        second = getpass.getpass("Password again: ")
        if first != second:
            raise SystemExit("passwords do not match")
    return first


def cmd_create_school(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        existing = db.execute(select(School).where(School.name == args.name)).scalars().first()
        if existing is not None:
            raise SystemExit("school_already_exists")
        school = School(name=args.name)
        db.add(school)
        db.flush()
        audit_write(db, _system_for_school(school.id), "manage.create_school", f"school_school:{school.id}", "administration", "success")
        db.commit()
        _output({"id": str(school.id), "name": school.name})
    finally:
        db.close()


def cmd_create_user(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        school = db.get(School, uuid.UUID(args.school_id))
        if school is None:
            raise SystemExit("school_not_found")
        existing = db.execute(
            select(User).where(User.school_id == school.id, User.username == args.username)
        ).scalars().first()
        if existing is not None:
            raise SystemExit("username_already_exists")
        password = _read_password(args, confirm=True)
        validate_password_policy(password, args.username)
        user = User(
            school_id=school.id,
            username=args.username,
            full_name=args.full_name,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.flush()
        db.add(RoleAssignment(user_id=user.id, school_id=school.id, role=args.role))
        audit_write(db, _system_for_school(school.id), "manage.create_user", f"identity_user:{user.id}", "administration", "success", {"school_id": str(school.id), "role": args.role})
        db.commit()
        _output({"id": str(user.id), "school_id": str(school.id), "username": user.username, "role": args.role})
    finally:
        db.close()


def cmd_set_password(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        user = _find_user(db, args)
        password = _read_password(args, confirm=True)
        validate_password_policy(password, user.username)
        user.password_hash = hash_password(password)
        from datetime import datetime, timezone
        user.password_changed_at = datetime.now(timezone.utc)
        user.failed_login_count = 0
        user.locked_until = None
        audit_write(db, _system_for_school(user.school_id), "manage.set_password", f"identity_user:{user.id}", "administration", "success")
        db.commit()
        _output({"id": str(user.id), "username": user.username, "status": "password_changed"})
    finally:
        db.close()


def cmd_list_users(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        stmt = select(User).where(User.school_id == uuid.UUID(args.school_id)).order_by(User.username.asc())
        if args.active_only:
            stmt = stmt.where(User.is_active.is_(True))
        users = db.execute(stmt).scalars().all()
        roles: dict[uuid.UUID, str] = {}
        for ra in db.execute(select(RoleAssignment)).scalars().all():
            roles.setdefault(ra.user_id, ra.role)
        _output({"items": [
            {
                "id": str(u.id),
                "username": u.username,
                "full_name": u.full_name,
                "role": roles.get(u.id),
                "is_active": u.is_active,
                "locked_until": u.locked_until,
            }
            for u in users
        ], "total": len(users)})
    finally:
        db.close()


def cmd_deactivate_user(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        user = db.get(User, uuid.UUID(args.user_id))
        if user is None:
            raise SystemExit("user_not_found")
        user.is_active = False
        audit_write(db, _system_for_school(user.school_id), "manage.deactivate_user", f"identity_user:{user.id}", "administration", "success")
        db.commit()
        _output({"id": str(user.id), "username": user.username, "is_active": False})
    finally:
        db.close()


def cmd_rollover(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        result = rollover_school_year(
            db,
            school_id=uuid.UUID(args.school_id),
            from_school_year_id=uuid.UUID(args.from_year_id),
            to_school_year_id=uuid.UUID(args.to_year_id),
        )
        audit_write(db, _system_for_school(uuid.UUID(args.school_id)), "manage.rollover_school_year", f"school_school:{args.school_id}", "administration", "success", result)
        db.commit()
        _output(result)
    finally:
        db.close()


def cmd_export_audit(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        stmt = select(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())
        if args.school_id:
            stmt = stmt.where(AuditLog.school_id == uuid.UUID(args.school_id))
        rows = db.execute(stmt).scalars().all()
        ok, bad_id = verify_chain(db)
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps({
                    "id": str(row.id),
                    "timestamp": row.timestamp,
                    "action": row.action,
                    "resource": row.resource,
                    "purpose": row.purpose,
                    "outcome": row.outcome,
                    "principal_id": str(row.principal_id) if row.principal_id else None,
                    "principal_role": row.principal_role,
                    "school_id": str(row.school_id) if row.school_id else None,
                    "prev_hash": row.prev_hash,
                    "record_hash": row.record_hash,
                }, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        _output({"output": str(target), "entries": len(rows), "chain_ok": ok, "bad_record_id": str(bad_id) if bad_id else None})
    finally:
        db.close()


def _find_user(db, args: argparse.Namespace) -> User:
    if getattr(args, "user_id", None):
        user = db.get(User, uuid.UUID(args.user_id))
    else:
        stmt = select(User).where(User.username == args.username)
        if getattr(args, "school_id", None):
            stmt = stmt.where(User.school_id == uuid.UUID(args.school_id))
        user = db.execute(stmt).scalars().first()
    if user is None:
        raise SystemExit("user_not_found")
    return user


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KOMPAS administrácia (pripojenie cez DATABASE_URL)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create-school")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_create_school)

    p = sub.add_parser("create-user")
    p.add_argument("--school-id", required=True)
    p.add_argument("--username", required=True)
    p.add_argument("--full-name", required=True)
    p.add_argument("--role", required=True, choices=[role.value for role in Role])
    p.add_argument("--password-stdin", action="store_true")
    p.add_argument("--password-env")
    p.set_defaults(func=cmd_create_user)

    p = sub.add_parser("set-password")
    p.add_argument("--user-id")
    p.add_argument("--username")
    p.add_argument("--school-id")
    p.add_argument("--password-stdin", action="store_true")
    p.add_argument("--password-env")
    p.set_defaults(func=cmd_set_password)

    p = sub.add_parser("list-users")
    p.add_argument("--school-id", required=True)
    p.add_argument("--active-only", action="store_true")
    p.set_defaults(func=cmd_list_users)

    p = sub.add_parser("deactivate-user")
    p.add_argument("--user-id", required=True)
    p.set_defaults(func=cmd_deactivate_user)

    p = sub.add_parser("rollover-school-year")
    p.add_argument("--school-id", required=True)
    p.add_argument("--from-year-id", required=True)
    p.add_argument("--to-year-id", required=True)
    p.set_defaults(func=cmd_rollover)

    p = sub.add_parser("export-audit")
    p.add_argument("--school-id")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_export_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
