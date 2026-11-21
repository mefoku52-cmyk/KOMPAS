"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import sk from "@/locales/sk/common.json";
import { clearRole, clearToken, getRole, getToken, type Role } from "@/lib/api";
import { Loading } from "@/components/ui";

const roleLabels: Record<Role, string> = {
  student: sk.roles.student,
  teacher: sk.roles.teacher,
  leadership: sk.roles.leadership,
  parent: sk.roles.parent,
};

export function AppShell({
  role,
  title,
  subtitle,
  sections,
  children,
}: {
  role: Role;
  title: string;
  subtitle?: string;
  sections?: { id: string; label: string }[];
  children: ReactNode;
}) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getToken();
    const currentRole = getRole();
    if (!token || currentRole !== role) {
      router.replace("/");
      return;
    }
    setReady(true);
  }, [router, role]);

  function logout() {
    clearToken();
    clearRole();
    router.replace("/");
  }

  if (!ready) {
    return (
      <main>
        <Loading label="Overujem prihlásenie…" />
      </main>
    );
  }

  return (
    <>
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden>K</span>
          <span>
            <strong>{sk.app.title}</strong>
            <small>{roleLabels[role]}</small>
          </span>
        </div>
        <nav className="app-nav" aria-label="Sekcie">
          {sections?.map((section) => (
            <a key={section.id} href={`#${section.id}`}>{section.label}</a>
          ))}
        </nav>
        <div className="header-right">
          <span className="role-pill">{roleLabels[role]}</span>
          <button className="secondary" onClick={logout}>{sk.app.logout}</button>
        </div>
      </header>
      <main>
        <div className="page-title">
          <h1>{title}</h1>
          {subtitle ? <p className="muted">{subtitle}</p> : null}
        </div>
        {children}
      </main>
    </>
  );
}
