"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import sk from "@/locales/sk/common.json";
import { clearRole, clearToken, getRole, getToken } from "@/lib/api";

export default function ParentPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "parent") router.replace("/");
  }, [router]);

  function logout() {
    clearToken();
    clearRole();
    router.replace("/");
  }

  return (
    <main>
      <header>
        <h1>{sk.parent.title}</h1>
        <button className="secondary" onClick={logout}>{sk.app.logout}</button>
      </header>
      <section className="card">
        <h2>{sk.parent.approvedInfo}</h2>
        <p className="muted">Schvalene informacie o vlastnom dietati. Sukromne poznámky ucitela sa nezobrazujú.</p>
      </section>
      <section className="card">
        <h2>{sk.parent.communication}</h2>
        <p className="muted">Komunikacia s povolenymi ucastnikmi.</p>
      </section>
    </main>
  );
}
