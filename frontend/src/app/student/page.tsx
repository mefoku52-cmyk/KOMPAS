"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import sk from "@/locales/sk/common.json";
import { clearRole, clearToken, getRole, getToken } from "@/lib/api";

export default function StudentPage() {
  const router = useRouter();
  const [answer, setAnswer] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "student") router.replace("/");
  }, [router]);

  function logout() {
    clearToken();
    clearRole();
    router.replace("/");
  }

  return (
    <main>
      <header>
        <h1>{sk.student.title}</h1>
        <button className="secondary" onClick={logout}>{sk.app.logout}</button>
      </header>
      <section className="card">
        <h2>{sk.student.progress}</h2>
        <div className="grid">
          <div className="card"><h3>{sk.student.covered}</h3><p className="muted">0</p></div>
          <div className="card"><h3>{sk.student.practiced}</h3><p className="muted">0</p></div>
          <div className="card"><h3>{sk.student.verified}</h3><p className="muted">0</p></div>
        </div>
      </section>
      <section className="card">
        <h2>{sk.student.assignments}</h2>
        <ul><li className="muted">-</li></ul>
        <label htmlFor="ans">{sk.student.submitAnswer}</label>
        <textarea id="ans" value={answer} onChange={(e) => setAnswer(e.target.value)} rows={3} />
        <div style={{ marginTop: 8 }}>
          <button type="button" onClick={() => setSubmitted(answer || "-")}>{sk.student.submitAnswer}</button>
        </div>
        {submitted !== null ? <p className="muted">Odoslane: {submitted}</p> : null}
      </section>
    </main>
  );
}
