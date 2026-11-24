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
    # only explicit HTTP calls via apiFetch/fetch with API base or known API literals
    api_call = re.compile(r"apiFetch\s*(?:<[^>]*>)?\(\s*[`'\"](/[^`'\"]*)[`'\"]")
    fetch_call = re.compile(r"fetch\s*\(\s*`\$\{API_BASE\}(/[^`'\"]*)`")
    # direct API string literals used as request paths (exclude route segments like href)
    for p in FRONTEND.rglob("*"):
        if p.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in api_call.finditer(text):
            val = re.sub(r"\$\{[^}]+\}", "{param}", m.group(1)).split("?")[0]
            paths.add(val)
        for m in fetch_call.finditer(text):
            val = re.sub(r"\$\{[^}]+\}", "{param}", m.group(1)).split("?")[0]
            paths.add(val)
        # login endpoint literal
        if '"/auth/login"' in text or "'/auth/login'" in text:
            paths.add("/auth/login")
    return paths


def load_openapi_paths() -> set[str]:
    data = json.loads(OPENAPI.read_text(encoding="utf-8"))
    out = set()
    for p, methods in data.get("paths", {}).items():
        canonical_path = re.sub(r"\{[^/{}]+\}", "{param}", p)
        for m in methods:
            if m.lower() in {"get", "post", "put", "patch", "delete"}:
                out.add(canonical_path)
    return out


def main() -> int:
    fe_paths = extract_frontend_paths()
    oa_paths = load_openapi_paths()

    missing_in_openapi = sorted(fe_paths - oa_paths)
    unused_in_frontend = sorted(oa_paths - fe_paths)

    modules_without_ui = []
    fe_text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in FRONTEND.rglob("*")
        if p.is_file() and p.suffix in {".ts", ".tsx", ".js", ".jsx"}
    )
    for mod, area in MODULE_UI.items():
        num = mod.split("-")[1]
        has_call = (f"/k{num}" in fe_text)
        special = {"K-06": "/lab", "K-12": "/analytics", "K-13": "/parent/", "K-14": "/communication", "K-15": "/projects"}
        if mod in special:
            tok = special[mod]
            # require API-like usage, not just route segment coincidence
            has_call = (f'apiFetch("{tok}' in fe_text) or (f"apiFetch('{tok}" in fe_text) or (f"API_BASE}}{tok}" in fe_text) or (f"/k{num}" in fe_text)
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
