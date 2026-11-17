from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database.session import Base
from app.core.security.auth import verify_password
from app.shared.identity import User

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "manage.py"


@pytest.fixture()
def cli_env(tmp_path):
    db_path = tmp_path / "manage.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    engine.dispose()
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["PYTHONPATH"] = str(ROOT / "backend")
    env["JWT_SECRET_KEY"] = "test-secret-key-0123456789abcdef"

    def run(*args: str, stdin: str | None = None) -> dict:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), *args], cwd=ROOT, env=env,
            input=stdin, capture_output=True, text=True, timeout=120,
        )
        assert completed.returncode == 0, completed.stderr + completed.stdout
        return json.loads(completed.stdout)

    yield run, db_path


def test_manage_cli_full_flow(cli_env, tmp_path):
    run, db_path = cli_env
    school = run("create-school", "--name", "CLI škola")
    user = run(
        "create-user", "--school-id", school["id"], "--username", "riaditel",
        "--full-name", "Riaditeľ Test", "--role", "leadership", "--password-stdin",
        stdin="AdminPass1234\n",
    )
    assert user["role"] == "leadership"
    users = run("list-users", "--school-id", school["id"])
    assert users["total"] == 1
    assert users["items"][0]["username"] == "riaditel"
    assert users["items"][0]["is_active"] is True

    run("set-password", "--user-id", user["id"], "--password-stdin", stdin="NoveHeslo1234\n")
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Session = sessionmaker(bind=engine, future=True)
    with Session() as db:
        stored = db.execute(select(User).where(User.username == "riaditel")).scalars().one()
        assert verify_password("NoveHeslo1234", stored.password_hash)
    engine.dispose()

    deactivated = run("deactivate-user", "--user-id", user["id"])
    assert deactivated["is_active"] is False
    active = run("list-users", "--school-id", school["id"], "--active-only")
    assert active["total"] == 0

    output = tmp_path / "audit.jsonl"
    exported = run("export-audit", "--school-id", school["id"], "--output", str(output))
    assert exported["chain_ok"] is True
    assert exported["entries"] >= 4
    lines = [json.loads(line) for line in output.read_text().splitlines() if line.strip()]
    assert len(lines) == exported["entries"]
    assert any(row["action"] == "manage.create_user" for row in lines)


def test_manage_cli_rejects_weak_password(cli_env):
    run, db_path = cli_env
    school = run("create-school", "--name", "Slabé heslo")
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["PYTHONPATH"] = str(ROOT / "backend")
    env["JWT_SECRET_KEY"] = "test-secret-key-0123456789abcdef"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "create-user", "--school-id", school["id"], "--username", "slaby",
         "--full-name", "Slabý", "--role", "student", "--password-stdin"],
        cwd=ROOT, env=env, input="short\n", capture_output=True, text=True, timeout=120,
    )
    assert completed.returncode != 0
    assert "password_too_short" in completed.stderr
