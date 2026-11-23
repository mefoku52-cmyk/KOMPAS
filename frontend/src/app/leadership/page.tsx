"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Alert, Badge, Card, Empty, Loading, Stat } from "@/components/ui";
import { apiFetch, formatApiError } from "@/lib/api";
import {
  REQUEST_STATUS_LABELS,
  formatDate,
  statusLabel,
  statusTone,
} from "@/lib/labels";
import type {
  AnalyticsOverview,
  OperationRequest,
  OrgPlan,
  OrgTask,
  Paged,
} from "@/lib/types";

type ILReport = { counts: Record<string, number>; invariants: Record<string, boolean>; status: string };

const TRANSITIONS: Record<string, string[]> = {
  submitted: ["approved", "rejected", "cancelled"],
  approved: ["in_progress", "cancelled"],
  in_progress: ["fulfilled", "cancelled"],
};

export default function LeadershipPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [plans, setPlans] = useState<OrgPlan[]>([]);
  const [tasks, setTasks] = useState<OrgTask[]>([]);
  const [requests, setRequests] = useState<OperationRequest[]>([]);
  const [ilReport, setIlReport] = useState<ILReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [sisSources, setSisSources] = useState<any[]>([]);
  const [sisJobs, setSisJobs] = useState<any[]>([]);
  const [sisConflicts, setSisConflicts] = useState<any[]>([]);
  const [sisForm, setSisForm] = useState({ name: "EduPage", subdomain: "", api_key: "", is_enabled: false });
  const [sisBusy, setSisBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [overview, planRes, taskRes, requestRes, ilRep, sisSrc, sisJ, sisC] = await Promise.all([
        apiFetch<AnalyticsOverview>("/analytics/overview"),
        apiFetch<Paged<OrgPlan>>("/k10/plans"),
        apiFetch<Paged<OrgTask>>("/k10/tasks"),
        apiFetch<Paged<OperationRequest>>("/k11/requests"),
        process.env.NEXT_PUBLIC_K18_ENABLED === "false"
          ? Promise.resolve(null)
          : apiFetch<ILReport>("/intelligence/report/system").catch(() => null),
        apiFetch<{ items: any[] }>("/integrations/sis/sources").catch(() => ({ items: [] })),
        apiFetch<{ items: any[] }>("/integrations/sis/jobs").catch(() => ({ items: [] })),
        apiFetch<{ items: any[] }>("/integrations/sis/conflicts").catch(() => ({ items: [] })),
      ]);
      setAnalytics(overview);
      setPlans(planRes.items);
      setTasks(taskRes.items);
      setRequests(requestRes.items);
      setIlReport(ilRep);
      setSisSources(sisSrc.items || []);
      setSisJobs(sisJ.items || []);
      setSisConflicts(sisC.items || []);
    } catch (err) {
      setError(formatApiError(err, "Dáta sa nepodarilo načítať"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function transition(request: OperationRequest, newStatus: string) {
    setBusy(request.id);
    setError(null);
    try {
      await apiFetch<OperationRequest>(`/k11/requests/${request.id}/transition`, {
        method: "POST",
        body: JSON.stringify({ new_status: newStatus }),
      });
      const res = await apiFetch<Paged<OperationRequest>>("/k11/requests");
      setRequests(res.items);
    } catch (err) {
      setError(formatApiError(err, "Zmena stavu sa nepodarila"));
    } finally {
      setBusy(null);
    }
  }

  const statusEntries = analytics ? Object.entries(analytics.by_status) : [];

  async function createSisSource(e: React.FormEvent) {
    e.preventDefault();
    setSisBusy("create");
    setError(null);
    try {
      await apiFetch("/integrations/sis/sources", { method: "POST", body: JSON.stringify({ ...sisForm, provider_type: "edupage" }) });
      setSisForm({ name: "EduPage", subdomain: "", api_key: "", is_enabled: false });
      await load();
    } catch (err) {
      setError(formatApiError(err, "Integráciu sa nepodarilo uložiť"));
    } finally {
      setSisBusy(null);
    }
  }

  async function sisAction(sourceId: string, action: "test" | "sync" | "dry_run") {
    setSisBusy(`${action}:${sourceId}`);
    setError(null);
    try {
      if (action === "test") await apiFetch(`/integrations/sis/sources/${sourceId}/test`, { method: "POST" });
      if (action === "sync") await apiFetch(`/integrations/sis/sources/${sourceId}/sync`, { method: "POST", body: JSON.stringify({ mode: "full" }) });
      if (action === "dry_run") await apiFetch(`/integrations/sis/sources/${sourceId}/sync`, { method: "POST", body: JSON.stringify({ mode: "dry_run" }) });
      await load();
    } catch (err) {
      setError(formatApiError(err, "Akcia integrácie zlyhala"));
    } finally {
      setSisBusy(null);
    }
  }

  return (
    <AppShell
      role="leadership"
      title="Vedenie školy"
      subtitle="Agregované prehľady chránia súkromie malých skupín, organizačné úlohy držia školu v chode."
      sections={[
        { id: "prehlady", label: "Prehľady" },
        { id: "intelligence", label: "Intelligence" },
        { id: "integracie", label: "Integrácie" },
        { id: "ulohy", label: "Úlohy" },
        { id: "poziadavky", label: "Požiadavky" },
      ]}
    >
      {error ? <Alert>{error}</Alert> : null}
      {loading ? <Loading /> : null}

      {!loading && analytics ? (
        <>
          <section id="prehlady" className="grid">
            <Card title="Prehľad učenia" subtitle={`Prah pre potlačenie: ${analytics.threshold} žiakov`}>
              <div className="grid">
                <Stat label="Žiaci v škole" value={analytics.suppressed ? "—" : analytics.total_students} />
                <Stat
                  label="Sledované dvojice"
                  value={analytics.suppressed ? "—" : analytics.tracked_pairs}
                  hint="žiak × téma"
                />
              </div>
              {analytics.suppressed ? (
                <Alert tone="amber">
                  Skupina je príliš malá na zverejnenie agregátu. Údaje sa nezobrazujú, aby sa nedali
                  identifikovať jednotliví žiaci.
                </Alert>
              ) : (
                <div className="stack">
                  {statusEntries.map(([status, count]) => (
                    <div key={status} className="bar-row">
                      <span className="bar-label">{statusLabel(status)}</span>
                      <Badge tone={statusTone(status)}>
                        {count.suppressed ? "potlačené" : count.value}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card title="Plány" subtitle="Organizačné plány školy">
              {plans.length === 0 ? (
                <Empty>Žiadne plány.</Empty>
              ) : (
                <ul className="list">
                  {plans.map((plan) => (
                    <li key={plan.id} className="list-item">
                      <div>
                        <strong>{plan.name}</strong>
                        <p className="muted small">{plan.description || "Bez popisu"}</p>
                      </div>
                      <Badge tone="blue">od {formatDate(plan.valid_from)}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </section>

          <section id="intelligence">
            <Card title="Intelligence Layer (K18)" subtitle="Systémový prehľad IL — len agregované/invarianty.">
              {!ilReport ? <Empty>Report nie je dostupný alebo chýbajú oprávnenia.</Empty> : (
                <div className="stack">
                  <div className="grid">
                    {Object.entries(ilReport.counts || {}).map(([k, v]) => <Stat key={k} label={k} value={v} />)}
                  </div>
                  <div className="stack">
                    {Object.entries(ilReport.invariants || {}).map(([k, v]) => (
                      <div key={k} className="bar-row"><span className="bar-label">{k}</span><Badge tone={v ? "green" : "red"}>{v ? "OK" : "FAIL"}</Badge></div>
                    ))}
                    <Badge tone={ilReport.status === "INTEGRATED" ? "green" : "amber"}>{ilReport.status}</Badge>
                  </div>
                </div>
              )}
            </Card>
          </section>

          <section id="integracie">
            <Card title="Integrácie SIS (EduPage)" subtitle="Pripojenie školy, test spojenia, dry-run a synchronizácia. API kľúč sa neukladá v čistom texte.">
              <form className="stack" onSubmit={createSisSource}>
                <div className="grid">
                  <label className="stack"><span className="muted small">Názov</span><input value={sisForm.name} onChange={(e)=>setSisForm({...sisForm,name:e.target.value})} required /></label>
                  <label className="stack"><span className="muted small">EduPage subdoména</span><input value={sisForm.subdomain} onChange={(e)=>setSisForm({...sisForm,subdomain:e.target.value})} placeholder="napr. skola" required /></label>
                </div>
                <label className="stack"><span className="muted small">API kľúč (uloží sa šifrovane)</span><input value={sisForm.api_key} onChange={(e)=>setSisForm({...sisForm,api_key:e.target.value})} placeholder="EduPage API key" /></label>
                <label className="row-actions"><input type="checkbox" checked={sisForm.is_enabled} onChange={(e)=>setSisForm({...sisForm,is_enabled:e.target.checked})} /> <span className="muted small">Povoliť zdroj</span></label>
                <div className="row-actions"><button type="submit" disabled={sisBusy==="create"}>{sisBusy==="create"?"Ukladám…":"Pridať zdroj"}</button></div>
              </form>
              <div className="stack" style={{marginTop:16}}>
                {sisSources.length===0 ? <Empty>Žiadny SIS zdroj.</Empty> : sisSources.map((src:any)=>(
                  <div key={src.id} className="list-item">
                    <div>
                      <strong>{src.name}</strong> <Badge tone={src.is_enabled?"green":"gray"}>{src.is_enabled?"enabled":"disabled"}</Badge>
                      <p className="muted small">{src.provider_type} · {src.config?.subdomain || "bez subdomény"} · secret: {src.has_secret ? (src.secret_masked || "nastavený") : "chýba"}</p>
                      <p className="muted small">Posledná sync: {src.last_sync_at || "—"} · Úspešná: {src.last_success_at || "—"}</p>
                    </div>
                    <div className="row-actions">
                      <button type="button" className="secondary" disabled={!!sisBusy} onClick={()=>void sisAction(src.id,"test")}>Test</button>
                      <button type="button" className="secondary" disabled={!!sisBusy} onClick={()=>void sisAction(src.id,"dry_run")}>Dry-run</button>
                      <button type="button" disabled={!!sisBusy} onClick={()=>void sisAction(src.id,"sync")}>Sync</button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="História synchronizácií" subtitle="Posledné behy, chyby a sumáre.">
              {sisJobs.length===0 ? <Empty>Žiadne synchronizácie.</Empty> : (
                <ul className="list">
                  {sisJobs.slice(0,10).map((job:any)=>(
                    <li key={job.id} className="list-item">
                      <div>
                        <strong>{job.mode}</strong> <Badge tone={job.status==="success"?"green":job.status==="failed"?"red":"amber"}>{job.status}</Badge>
                        <p className="muted small">{job.started_at || "—"} → {job.finished_at || "—"}</p>
                        {job.error ? <p className="muted small">Chyba: {job.error}</p> : null}
                        {job.summary?.conflicts?.length ? <p className="muted small">Konflikty: {job.summary.conflicts.length}</p> : null}
                        {job.summary?.deactivated_candidates?.length ? <p className="muted small">Kandidáti deaktivácie: {job.summary.deactivated_candidates.length}</p> : null}
                      </div>
                      <div className="muted small">C:{JSON.stringify(job.summary?.created||{})} U:{JSON.stringify(job.summary?.updated||{})}</div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card title="Konflikty identity" subtitle="Záznamy vyžadujúce kontrolu.">
              {sisConflicts.length===0 ? <Empty>Žiadne konflikty.</Empty> : (
                <ul className="list">
                  {sisConflicts.slice(0,20).map((c:any)=>(
                    <li key={c.id} className="list-item">
                      <div><strong>{c.entity_type}</strong> <span className="muted small">{c.external_id}</span></div>
                      <Badge tone="amber">{c.conflict_state}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </section>

          <section id="ulohy">
            <Card title="Organizačné úlohy" subtitle="Čo má škola naplánované">
              {tasks.length === 0 ? (
                <Empty>Žiadne úlohy.</Empty>
              ) : (
                <ul className="list">
                  {tasks.map((task) => (
                    <li key={task.id} className="list-item">
                      <div>
                        <strong>{task.title}</strong>
                        <p className="muted small">{task.description || "Bez popisu"}</p>
                      </div>
                      <div className="row-actions">
                        <Badge tone={statusTone(task.status)}>{task.status}</Badge>
                        <span className="muted small">do {formatDate(task.due_at)}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </section>

          <section id="poziadavky">
            <Card title="Prevádzkové požiadavky" subtitle="Schvaľovanie žiadostí o priestory a vybavenie">
              {requests.length === 0 ? (
                <Empty>Žiadne požiadavky.</Empty>
              ) : (
                <ul className="list">
                  {requests.map((request) => (
                    <li key={request.id} className="list-item">
                      <div>
                        <strong>{request.title}</strong>
                        <p className="muted small">
                          {request.request_type} · {request.description || "Bez popisu"}
                        </p>
                      </div>
                      <div className="row-actions">
                        <Badge tone={statusTone(request.status)}>
                          {REQUEST_STATUS_LABELS[request.status] || request.status}
                        </Badge>
                        {(TRANSITIONS[request.status] || []).map((next) => (
                          <button
                            key={next}
                            type="button"
                            className="secondary"
                            disabled={busy === request.id}
                            onClick={() => void transition(request, next)}
                          >
                            {REQUEST_STATUS_LABELS[next] || next}
                          </button>
                        ))}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
