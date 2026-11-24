export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type ApiError = { status: number; detail?: string };

export type Role = "student" | "teacher" | "leadership" | "parent";

export type TokenClaims = {
  sub?: string;
  role?: string | null;
  school_id?: string | null;
  exp?: number;
};

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
}

export async function apiFetch<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  if (!headers.has("Content-Type") && init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if ((res.status === 401 || res.status === 403) && path !== "/auth/login") {
    handleAuthError(res.status);
  }
  if (!res.ok) {
    let detail: string | undefined;
    try {
      const data = await res.json();
      detail =
        (data && (data.detail || data.message || data?.error?.message_key)) || undefined;
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

export async function login(username: string, password: string, school_id?: string, role?: Role): Promise<{ access_token: string }> {
  const body: Record<string, string> = { username, password };
  if (school_id) body.school_id = school_id;
  if (role) body.role = role;
  return apiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function parseClaims(token: string): TokenClaims | null {
  try {
    const part = token.split(".")[1];
    if (!part) return null;
    const json = atob(part.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json) as TokenClaims;
  } catch {
    return null;
  }
}

export function parseRoleFromToken(token: string): string | null {
  return parseClaims(token)?.role || null;
}

export function getUserId(): string | null {
  const token = getToken();
  if (!token) return null;
  return parseClaims(token)?.sub || null;
}

export function formatApiError(err: unknown, fallback: string): string {
  if (typeof err === "object" && err !== null && "status" in err) {
    const apiErr = err as ApiError;
    if (apiErr.detail) return `${apiErr.detail} (${apiErr.status})`;
    return `${fallback} (${apiErr.status})`;
  }
  return fallback;
}
