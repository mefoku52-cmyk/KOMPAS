"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import sk from "@/locales/sk/common.json";
import { clearRole, clearToken, getRole, getToken } from "@/lib/api";

export default function TeacherPage() {
  const router = useRouter();
  const [draft, setDraft] = useState("");

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "teacher") router.replace("/");
  }, [router]);

  function logout() {
    clearToken();
    clearRole();
    router.replace("/");
  }

  return (
    <main>
      <header>
        <h1>{sk.teacher.title}</h1>
        <button className="secondary" onClick={logout}>{sk.app.logout}</button>
      </header>
      <section className="card">
        <h2>{sk.teacher.classOverview}</h2>
        <p className="muted">Prehlad stavov uciva v triede.</p>
      </section>
      <section className="card">
        <h2>{sk.teacher.library}</h2>
        <p className="muted">Kniznica priprav, verzie a stitky.</p>
      </section>
      <section className="card">
        <h2>{sk.teacher.assistant}</h2>
        <p className="error">{sk.teacher.assistantNote}</p>
        <label htmlFor="draft">Navrh</label>
        <textarea id="draft" value={draft} onChange={(e) => setDraft(e.target.value)} rows={4} />
        <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button">Ulozit koncept</button>
          <button type="button" className="secondary" disabled>Schvalit (vyzaduje ucitela)</button>
        </div>
      </section>
    </main>
  );
}
