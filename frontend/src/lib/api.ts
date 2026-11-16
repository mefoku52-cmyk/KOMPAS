export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type ApiError = { status: number; detail?: string };

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string) {
  if (typeof window !== "undefined") localStorage.setItem("access_token", token);
}

export function clearToken() {
  if (typeof window !== "undefined") localStorage.removeItem("access_token");
}

export function getRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("user_role");
}

export function setRole(role: string) {
  if (typeof window !== "undefined") localStorage.setItem("user_role", role);
}

export function clearRole() {
  if (typeof window !== "undefined") localStorage.removeItem("user_role");
}

function handleAuthError(status: number) {
  if (typeof window === "undefined") return;
  if (status === 401) {
    clearToken();
    clearRole();
    window.location.href = "/";
  }
  if (status === 403) {
    // caller can show forbidden state; keep user on page
  }
}

export async function apiFetch<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  if (!headers.has("Content-Type") && init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (res.status === 401 || res.status === 403) {
    handleAuthError(res.status);
  }
  if (!res.ok) {
    let detail: string | undefined;
    try {
      const data = await res.json();
      detail = (data && (data.detail || data.message)) as string | undefined;
    } catch {
      detail = res.statusText;
    }
    const err: ApiError = { status: res.status, detail };
    throw err;
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

export async function login(username: string, password: string, school_id?: string): Promise<{ access_token: string }> {
  const body: Record<string, string> = { username, password };
  if (school_id) body.school_id = school_id;
  return apiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function parseRoleFromToken(token: string): string | null {
  try {
    const part = token.split(".")[1];
    if (!part) return null;
    const json = atob(part.replace(/-/g, "+").replace(/_/g, "/"));
    const payload = JSON.parse(json) as { role?: string | null };
    return payload.role || null;
  } catch {
    return null;
  }
}
