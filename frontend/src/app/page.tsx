"use client";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import sk from "@/locales/sk/common.json";
import { clearRole, clearToken, getRole, getToken, login, parseRoleFromToken, setRole, setToken } from "@/lib/api";
const roleToPath: Record<string, string> = {
  student: "/student",
  teacher: "/teacher",
  leadership: "/leadership",
  parent: "/parent",
};
type RoleKey = "student" | "teacher" | "leadership" | "parent";
function loginErrorMessage(error: unknown): string {
  const detail = typeof error === "object" && error !== null && "detail" in error
    ? (error as { detail?: unknown }).detail
    : undefined;
  if (typeof detail === "string") {
    if (detail === "no_active_role_assignment") return sk.auth.noActiveRole;
    if (detail === "role_selection_required") return sk.auth.roleSelection;
    if (detail === "account_locked") return sk.auth.accountLocked;
    if (detail === "rate_limited") return sk.auth.rateLimited;
  }
  return sk.auth.invalid;
}
export default function HomePage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [schoolId, setSchoolId] = useState("");
  const [selectedRole, setSelectedRole] = useState<RoleKey | "">("");
  const [showRoleSelection, setShowRoleSelection] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (token && role && roleToPath[role]) {
      router.replace(roleToPath[role]);
    }
  }, [router]);
  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await login(username, password, schoolId || undefined, selectedRole || undefined);
      setToken(res.access_token);
      const role = parseRoleFromToken(res.access_token);
      if (!role || !roleToPath[role]) {
        clearToken();
        clearRole();
        setError(sk.auth.invalid);
        return;
      }
      setRole(role);
      router.replace(roleToPath[role]);
    } catch (err) {
      const message = loginErrorMessage(err);
      if (message === sk.auth.roleSelection) {
        setShowRoleSelection(true);
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <main>
      <div className="card" style={{ maxWidth: 480, margin: "40px auto" }}>
        <h1>{sk.app.title}</h1>
        <p className="muted">{sk.app.login}</p>
        <form onSubmit={onSubmit}>
          <label htmlFor="username">{sk.auth.username}</label>
          <input id="username" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
          <label htmlFor="password">{sk.auth.password}</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
          <label htmlFor="school">School ID (volitelne)</label>
          <input id="school" value={schoolId} onChange={(e) => setSchoolId(e.target.value)} />
          {showRoleSelection ? (
            <>
              <label htmlFor="role">{sk.auth.chooseRole}</label>
              <select id="role" value={selectedRole} onChange={(e) => setSelectedRole(e.target.value as RoleKey | "")} required>
                <option value="">{sk.auth.chooseRole}</option>
                {(Object.keys(roleToPath) as RoleKey[]).map((role) => (
                  <option key={role} value={role}>{sk.roles[role]}</option>
                ))}
              </select>
            </>
          ) : null}
          {error ? <p className="error" role="alert">{error}</p> : null}
          <div style={{ marginTop: 12 }}>
            <button type="submit" disabled={loading}>{sk.auth.submit}</button>
          </div>
        </form>
      </div>
    </main>
  );
}
