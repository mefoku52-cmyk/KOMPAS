import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_alembic_upgrade_downgrade_upgrade(tmp_path):
    db_path = tmp_path / "migr.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["JWT_SECRET_KEY"] = env.get("JWT_SECRET_KEY", "test-secret-key-0123456789abcdef")
    env["JWT_ALGORITHM"] = "HS256"
    env["PYTHONPATH"] = str(ROOT / "backend")
    cmd = [sys.executable, "-m", "alembic"]
    cwd = ROOT / "backend"
    subprocess.check_call(cmd + ["upgrade", "head"], cwd=cwd, env=env)
    subprocess.check_call(cmd + ["downgrade", "base"], cwd=cwd, env=env)
    subprocess.check_call(cmd + ["upgrade", "head"], cwd=cwd, env=env)
