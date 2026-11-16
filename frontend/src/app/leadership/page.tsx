"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import sk from "@/locales/sk/common.json";
import { clearRole, clearToken, getRole, getToken } from "@/lib/api";

export default function LeadershipPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "leadership") router.replace("/");
  }, [router]);

  function logout() {
    clearToken();
    clearRole();
    router.replace("/");
  }

  return (
    <main>
      <header>
        <h1>{sk.leadership.title}</h1>
        <button className="secondary" onClick={logout}>{sk.app.logout}</button>
      </header>
      <section className="card">
        <h2>{sk.leadership.aggregates}</h2>
        <p className="muted">Agregovane prehlady skoly (male skupiny sa potlacia).</p>
      </section>
      <section className="card">
        <h2>{sk.leadership.tasks}</h2>
        <p className="muted">Organizacne ulohy a plany.</p>
      </section>
      <section className="card">
        <h2>{sk.leadership.requests}</h2>
        <p className="muted">Prevadzkove poziadavky (priestory, vybavenie).</p>
      </section>
    </main>
  );
}
