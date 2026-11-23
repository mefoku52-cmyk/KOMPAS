from __future__ import annotations

from typing import Any

import httpx

from app.core.config.settings import settings
from app.integrations.sis.base import (
    ExternalClass,
    ExternalClassTeacher,
    ExternalEnrollment,
    ExternalGuardianLink,
    ExternalPerson,
    ExternalSchoolYear,
    RosterSnapshot,
)


class EduPageClientError(RuntimeError):
    pass


class EduPageProvider:
    provider_type = "edupage"

    def __init__(self, *, subdomain: str, api_key: str, base_url: str | None = None, timeout_seconds: int | None = None):
        self.subdomain = subdomain.strip().strip(".")
        self.api_key = api_key
        self.base_url = (base_url or f"https://{self.subdomain}.edupage.org").rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.sis_request_timeout_seconds

    def _request(self, cmd: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/eduapi"
        data = {"cmd": cmd, **(params or {})}
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                resp = client.post(url, data=data, headers=headers)
        except httpx.HTTPError as exc:
            raise EduPageClientError(f"edupage_request_failed:{exc.__class__.__name__}") from exc
        if resp.status_code >= 400:
            raise EduPageClientError(f"edupage_http_{resp.status_code}")
        try:
            payload = resp.json()
        except ValueError:
            # some EduPage deployments can return form-encoded/text wrappers; keep a safe error
            raise EduPageClientError("edupage_invalid_json")
        if isinstance(payload, dict) and payload.get("status") in {"error", "fail"}:
            raise EduPageClientError(f"edupage_error:{payload.get('error') or payload.get('message') or 'unknown'}")
        if not isinstance(payload, dict):
            raise EduPageClientError("edupage_invalid_payload")
        return payload

    def healthcheck(self) -> dict[str, Any]:
        # getbasedata is the least-privilege read command typically available
        payload = self._request("getbasedata", {"format": "json"})
        return {
            "ok": True,
            "provider": self.provider_type,
            "subdomain": self.subdomain,
            "keys": sorted(list(payload.keys()))[:20],
        }

    def fetch_roster(self) -> RosterSnapshot:
        payload = self._request("getbasedata", {"format": "json"})
        return self.normalize_getbasedata(payload)

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            # EduPage may return {"rows":[...]} or {"1": {...}}
            if "rows" in value and isinstance(value["rows"], list):
                return value["rows"]
            return list(value.values())
        return []

    @staticmethod
    def _id(raw: dict[str, Any], *keys: str) -> str | None:
        for k in keys:
            v = raw.get(k)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                return s
        return None

    @staticmethod
    def _name(raw: dict[str, Any], *keys: str) -> str | None:
        for k in keys:
            v = raw.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        first = str(raw.get("firstname") or raw.get("first_name") or "").strip()
        last = str(raw.get("lastname") or raw.get("last_name") or "").strip()
        name = f"{first} {last}".strip()
        return name or None

    def normalize_getbasedata(self, payload: dict[str, Any]) -> RosterSnapshot:
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        teachers_raw = self._as_list(data.get("teachers") or data.get("teacher") or payload.get("teachers"))
        students_raw = self._as_list(data.get("students") or data.get("student") or payload.get("students"))
        classes_raw = self._as_list(data.get("classes") or data.get("class") or payload.get("classes"))
        years_raw = self._as_list(data.get("schoolyears") or data.get("school_years") or data.get("years"))
        parents_raw = self._as_list(data.get("parents") or data.get("guardians"))

        school_years: list[ExternalSchoolYear] = []
        for row in years_raw:
            if not isinstance(row, dict):
                continue
            eid = self._id(row, "id", "schoolyearid", "yearid")
            name = self._name(row, "name", "text", "short")
            if eid and name:
                school_years.append(ExternalSchoolYear(external_id=eid, name=name, raw=row))

        classes: list[ExternalClass] = []
        for row in classes_raw:
            if not isinstance(row, dict):
                continue
            eid = self._id(row, "id", "classid")
            name = self._name(row, "name", "short", "class")
            if not eid or not name:
                continue
            grade = row.get("grade")
            try:
                grade_int = int(grade) if grade is not None and str(grade).strip() != "" else None
            except Exception:
                grade_int = None
            classes.append(ExternalClass(
                external_id=eid,
                name=name,
                grade=grade_int,
                school_year_external_id=self._id(row, "schoolyearid", "yearid"),
                is_active=str(row.get("isactive", row.get("active", True))).lower() not in {"0", "false", "no"},
                raw=row,
            ))

        def person(row: dict[str, Any], *id_keys: str) -> ExternalPerson | None:
            eid = self._id(row, *id_keys)
            name = self._name(row, "name", "fullname", "label")
            if not eid or not name:
                return None
            return ExternalPerson(
                external_id=eid,
                full_name=name,
                first_name=(str(row.get("firstname") or row.get("first_name") or "").strip() or None),
                last_name=(str(row.get("lastname") or row.get("last_name") or "").strip() or None),
                email=(str(row.get("email") or "").strip() or None),
                username_hint=(str(row.get("username") or row.get("login") or "").strip() or None),
                is_active=str(row.get("isactive", row.get("active", True))).lower() not in {"0", "false", "no"},
                raw=row,
            )

        teachers = [p for row in teachers_raw if isinstance(row, dict) for p in [person(row, "id", "teacherid", "uid")] if p]
        students = [p for row in students_raw if isinstance(row, dict) for p in [person(row, "id", "studentid", "uid")] if p]
        guardians = [p for row in parents_raw if isinstance(row, dict) for p in [person(row, "id", "parentid", "guardianid", "uid")] if p]

        enrollments: list[ExternalEnrollment] = []
        for row in students_raw:
            if not isinstance(row, dict):
                continue
            sid = self._id(row, "id", "studentid", "uid")
            cid = self._id(row, "classid", "class_id", "class")
            if sid and cid:
                enrollments.append(ExternalEnrollment(
                    student_external_id=sid,
                    class_external_id=cid,
                    school_year_external_id=self._id(row, "schoolyearid", "yearid"),
                    is_active=str(row.get("isactive", row.get("active", True))).lower() not in {"0", "false", "no"},
                    raw={"student": sid, "class": cid},
                ))

        class_teachers: list[ExternalClassTeacher] = []
        for row in classes_raw:
            if not isinstance(row, dict):
                continue
            cid = self._id(row, "id", "classid")
            if not cid:
                continue
            teacher_ids = row.get("teacherids") or row.get("teachers") or row.get("class_teacher_ids")
            for tid in self._as_list(teacher_ids):
                if isinstance(tid, dict):
                    tid = self._id(tid, "id", "teacherid", "uid")
                if tid is None:
                    continue
                class_teachers.append(ExternalClassTeacher(
                    teacher_external_id=str(tid),
                    class_external_id=cid,
                    school_year_external_id=self._id(row, "schoolyearid", "yearid"),
                    raw={"class": cid, "teacher": str(tid)},
                ))
            # common single fields
            for key in ("teacherid", "teacher_id", "classroomteacherid"):
                tid = self._id(row, key)
                if tid:
                    class_teachers.append(ExternalClassTeacher(teacher_external_id=tid, class_external_id=cid, raw={"class": cid, "teacher": tid, "field": key}))

        guardian_links: list[ExternalGuardianLink] = []
        for row in parents_raw:
            if not isinstance(row, dict):
                continue
            gid = self._id(row, "id", "parentid", "guardianid", "uid")
            if not gid:
                continue
            children = row.get("studentids") or row.get("students") or row.get("childids")
            for child in self._as_list(children):
                if isinstance(child, dict):
                    child = self._id(child, "id", "studentid", "uid")
                if child is None:
                    continue
                guardian_links.append(ExternalGuardianLink(
                    guardian_external_id=gid,
                    child_student_external_id=str(child),
                    relationship=(str(row.get("relationship") or row.get("type") or "").strip() or None),
                    raw={"guardian": gid, "child": str(child)},
                ))

        return RosterSnapshot(
            school_years=school_years,
            classes=classes,
            teachers=teachers,
            students=students,
            guardians=guardians,
            enrollments=enrollments,
            class_teachers=class_teachers,
            guardian_links=guardian_links,
            metadata={"provider": "edupage", "raw_keys": sorted(list(payload.keys()))[:30]},
        )
