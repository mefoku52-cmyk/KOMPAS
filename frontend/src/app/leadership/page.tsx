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

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [overview, planRes, taskRes, requestRes, ilRep] = await Promise.all([
        apiFetch<AnalyticsOverview>("/analytics/overview"),
        apiFetch<Paged<OrgPlan>>("/k10/plans"),
        apiFetch<Paged<OrgTask>>("/k10/tasks"),
        apiFetch<Paged<OperationRequest>>("/k11/requests"),
        process.env.NEXT_PUBLIC_K18_ENABLED === "false"
          ? Promise.resolve(null)
          : apiFetch<ILReport>("/intelligence/report/system").catch(() => null),
      ]);
      setAnalytics(overview);
      setPlans(planRes.items);
      setTasks(taskRes.items);
      setRequests(requestRes.items);
      setIlReport(ilRep);
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

  return (
    <AppShell
      role="leadership"
      title="Vedenie školy"
      subtitle="Agregované prehľady chránia súkromie malých skupín, organizačné úlohy držia školu v chode."
      sections={[
        { id: "prehlady", label: "Prehľady" },
        { id: "intelligence", label: "Intelligence" },
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
