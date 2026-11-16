#!/usr/bin/env python3
"""Porovnanie ciest volaných z frontend/src s docs/api-contracts/openapi.json.
Funguje offline. Exit 1 pri nezhode alebo pri chýbajúcich vstupoch.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"
OPENAPI = ROOT / "docs" / "api-contracts" / "openapi.json"

# moduly bez akéhokoľvek UI (mapovanie na frontend stránky/volania)
MODULE_UI = {
    "K-01": "student",
    "K-02": "teacher",
    "K-03": "student",
    "K-04": "student",
    "K-05": "student/teacher",
    "K-06": "student",
    "K-07": "teacher",
    "K-08": "teacher",
    "K-09": "teacher",
    "K-10": "leadership",
    "K-11": "leadership",
    "K-12": "leadership",
    "K-13": "parent",
    "K-14": "student/teacher/leadership/parent",
    "K-15": "student/teacher",
    "K-16": "jadro (bez priamej UI dlaždice)",
}


def extract_frontend_paths() -> set[str]:
    paths: set[str] = set()
    # apiFetch("/path") / fetch(`${API_BASE}/path`) / login uses /auth/login internally
    patterns = [
        re.compile(r"apiFetch\s*(?:<[^>]*>)?\(\s*[`'\"](/[^`'\"]*)[`'\"]"),
        re.compile(r"fetch\s*\(\s*(?:`\$\{API_BASE\}(/[^`\"']*)`|[`'\"][^`'\"]*(/[^`'\"]*)[`'\"])"),
        re.compile(r"['\"](/auth/login)['\"]"),
        re.compile(r"['\"](/health)['\"]"),
        re.compile(r"['\"](/k\d{2}/[^'\"]+)['\"]"),
        re.compile(r"['\"](/(?:lab|analytics|parent|communication|projects)(?:/[^'\"]*)?)['\"]"),
    ]
    for p in FRONTEND.rglob("*"):
        if p.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in patterns:
            for m in pat.finditer(text):
                # pick first non-empty group
                val = next((g for g in m.groups() if g), None)
                if val and val.startswith("/"):
                    # normalize template remnants
                    val = re.sub(r"\$\{[^}]+\}", "{param}", val)
                    paths.add(val.split("?")[0])
    return paths


def load_openapi_paths() -> set[str]:
    data = json.loads(OPENAPI.read_text(encoding="utf-8"))
    out = set()
    for p, methods in data.get("paths", {}).items():
        for m in methods:
            if m.lower() in {"get", "post", "put", "patch", "delete"}:
                out.add(p)
    return out


def main() -> int:
    fe_paths = extract_frontend_paths()
    oa_paths = load_openapi_paths()

    # compare: frontend-called paths must exist in openapi
    missing_in_openapi = sorted(fe_paths - oa_paths)
    unused_in_frontend = sorted(oa_paths - fe_paths)

    modules_without_ui = []
    # modules without any direct API call from frontend beyond auth/health/status? treat as without real UI integration
    fe_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in FRONTEND.rglob("*.tsx") if p.is_file())
    for mod, area in MODULE_UI.items():
        token = mod.lower().replace("-", "")  # k-01 -> k01
        num = mod.split("-")[1]
        has_call = (f"/k{num}" in fe_text) or (f"{mod}" in fe_text)
        # special prefixes
        special = {"K-06": "/lab", "K-12": "/analytics", "K-13": "/parent", "K-14": "/communication", "K-15": "/projects"}
        if mod in special:
            has_call = special[mod] in fe_text
        if not has_call:
            modules_without_ui.append(f"{mod} ({area})")

    print("=== check_contract.py ===")
    print(f"Frontend cesty (extrahované): {sorted(fe_paths) or 'žiadne'}")
    print(f"OpenAPI cesty: {len(oa_paths)}")
    print(f"Chýbajú v OpenAPI (volané z frontendu): {missing_in_openapi or 'žiadne'}")
    print(f"V OpenAPI, nevolané priamo z frontendu (info): {unused_in_frontend or 'žiadne'}")
    print("Moduly bez akéhokoľvek UI volania (frontend nevolá ich endpointy):")
    for m in modules_without_ui:
        print(f" - {m}")

    ok = len(missing_in_openapi) == 0
    print(f"VYSLEDOK: {'OK' if ok else 'NEZHODA'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
