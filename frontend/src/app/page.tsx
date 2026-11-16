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

export default function HomePage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [schoolId, setSchoolId] = useState("");
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
      const res = await login(username, password, schoolId || undefined);
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
    } catch {
      setError(sk.auth.invalid);
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
          {error ? <p className="error" role="alert">{error}</p> : null}
          <div style={{ marginTop: 12 }}>
            <button type="submit" disabled={loading}>{sk.auth.submit}</button>
          </div>
        </form>
      </div>
    </main>
  );
}
