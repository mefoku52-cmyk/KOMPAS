"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Alert, Badge, Bar, Card, Empty, Loading, Stat } from "@/components/ui";
import { apiFetch, formatApiError } from "@/lib/api";
import {
  DRAFT_STATUS_LABELS,
  percent,
  statusLabel,
  statusTone,
} from "@/lib/labels";
import type {
  ClassOverview,
  ClassSummary,
  Draft,
  LibraryItem,
  Paged,
} from "@/lib/types";

export default function TeacherPage() {
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [selectedClass, setSelectedClass] = useState<string | null>(null);
  const [overview, setOverview] = useState<ClassOverview | null>(null);
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newItem, setNewItem] = useState({ title: "", description: "" });
  const [newDraft, setNewDraft] = useState({ title: "", draft_type: "worksheet", topics: "" });
  const [busy, setBusy] = useState<string | null>(null);

  const loadBase = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [classRes, itemRes, draftRes] = await Promise.all([
        apiFetch<Paged<ClassSummary> & { total: number }>("/k09/classes"),
        apiFetch<Paged<LibraryItem>>("/k07/items"),
        apiFetch<Paged<Draft>>("/k08/drafts"),
      ]);
      setClasses(classRes.items);
      setItems(itemRes.items);
      setDrafts(draftRes.items);
      setSelectedClass((prev) => prev ?? classRes.items[0]?.class_group_id ?? null);
    } catch (err) {
      setError(formatApiError(err, "Dáta sa nepodarilo načítať"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBase();
  }, [loadBase]);

  const loadOverview = useCallback(async (classId: string) => {
    try {
      const res = await apiFetch<ClassOverview>(`/k09/classes/${classId}/overview`);
      setOverview(res);
    } catch (err) {
      setOverview(null);
      setError(formatApiError(err, "Prehľad triedy sa nepodarilo načítať"));
    }
  }, []);

  useEffect(() => {
    if (selectedClass) void loadOverview(selectedClass);
  }, [selectedClass, loadOverview]);

  async function createItem() {
    if (!newItem.title.trim()) return;
    setBusy("item");
    setError(null);
    try {
      await apiFetch<LibraryItem>("/k07/items", {
        method: "POST",
        body: JSON.stringify({ title: newItem.title.trim(), description: newItem.description.trim() || null }),
      });
      setNewItem({ title: "", description: "" });
      const res = await apiFetch<Paged<LibraryItem>>("/k07/items");
      setItems(res.items);
    } catch (err) {
      setError(formatApiError(err, "Materiál sa nepodarilo uložiť"));
    } finally {
      setBusy(null);
    }
  }

  async function createDraft() {
    if (!newDraft.title.trim()) return;
    setBusy("draft");
    setError(null);
    try {
      await apiFetch<Draft>("/k08/drafts", {
        method: "POST",
        body: JSON.stringify({
          title: newDraft.title.trim(),
          draft_type: newDraft.draft_type,
          topics: newDraft.topics
            .split(",")
            .map((topic) => topic.trim())
            .filter(Boolean),
        }),
      });
      setNewDraft({ title: "", draft_type: "worksheet", topics: "" });
      const res = await apiFetch<Paged<Draft>>("/k08/drafts");
      setDrafts(res.items);
    } catch (err) {
      setError(formatApiError(err, "Koncept sa nepodarilo vytvoriť"));
    } finally {
      setBusy(null);
    }
  }

  async function submitDraft(draft: Draft) {
    setBusy(draft.id);
    setError(null);
    try {
      await apiFetch<Draft>(`/k08/drafts/${draft.id}/submit`, { method: "POST", body: JSON.stringify({}) });
      const res = await apiFetch<Paged<Draft>>("/k08/drafts");
      setDrafts(res.items);
    } catch (err) {
      setError(formatApiError(err, "Koncept sa nepodarilo odoslať"));
    } finally {
      setBusy(null);
    }
  }

  const statusEntries = Object.entries(overview?.by_status ?? {});
  const totalPairs = overview?.tracked_student_topic_pairs ?? 0;

  return (
    <AppShell
      role="teacher"
      title="Prehľad triedy"
      subtitle="Kde trieda stojí, čo má v knižnici a ktoré koncepty čakajú na schválenie."
      sections={[
        { id: "trieda", label: "Trieda" },
        { id: "kniznica", label: "Knižnica" },
        { id: "koncepty", label: "Koncepty" },
      ]}
    >
      {error ? <Alert>{error}</Alert> : null}
      {loading ? <Loading /> : null}

      {!loading ? (
        <>
          <section id="trieda" className="grid">
            <Card
              title="Trieda"
              actions={
                classes.length > 1 ? (
                  <select
                    aria-label="Vyber triedu"
                    value={selectedClass ?? ""}
                    onChange={(event) => setSelectedClass(event.target.value)}
                  >
                    {classes.map((item) => (
                      <option key={item.class_group_id} value={item.class_group_id}>
                        {item.name} ({item.grade}. ročník)
                      </option>
                    ))}
                  </select>
                ) : undefined
              }
            >
              {classes.length === 0 ? (
                <Empty>Nie si priradený k žiadnej triede.</Empty>
              ) : overview ? (
                <div className="stack">
                  <div className="kv">
                    <span>Trieda</span>
                    <strong>{classes.find((c) => c.class_group_id === selectedClass)?.name ?? "—"}</strong>
                    <span>Žiaci</span>
                    <strong>{overview.total_students}</strong>
                    <span>Sledované dvojice žiak–téma</span>
                    <strong>{totalPairs}</strong>
                  </div>
                  {statusEntries.map(([status, value]) => (
                    <Bar
                      key={status}
                      label={statusLabel(status)}
                      value={value}
                      total={Math.max(totalPairs, 1)}
                      tone={statusTone(status) === "green" ? "green" : statusTone(status) === "amber" ? "amber" : "blue"}
                    />
                  ))}
                </div>
              ) : (
                <Loading label="Načítavam prehľad triedy…" />
              )}
            </Card>

            <Card title="Rozdelenie stavov" subtitle="Percentuálny podiel v rámci triedy">
              {statusEntries.length === 0 ? (
                <Empty>Zatiaľ bez záznamov.</Empty>
              ) : (
                <div className="stack">
                  {statusEntries.map(([status, value]) => (
                    <div key={status} className="bar-row">
                      <span className="bar-label">{statusLabel(status)}</span>
                      <Badge tone={statusTone(status)}>{percent(value, Math.max(totalPairs, 1))} %</Badge>
                    </div>
                  ))}
                  <Stat
                    label="Overenosť triedy"
                    value={`${percent(overview?.by_status?.verified_mastery ?? 0, Math.max(totalPairs, 1))} %`}
                    tone="green"
                  />
                </div>
              )}
            </Card>
          </section>

          <section id="kniznica">
            <Card title="Knižnica príprav" subtitle="Materiály, ktoré môžeš použiť v hodine.">
              {items.length === 0 ? (
                <Empty>Knižnica je prázdna. Pridaj prvý materiál nižšie.</Empty>
              ) : (
                <ul className="list">
                  {items.map((item) => (
                    <li key={item.id} className="list-item">
                      <div>
                        <strong>{item.title}</strong>
                        <p className="muted small">{item.description || "Bez popisu"}</p>
                      </div>
                      <div className="row-actions">
                        {item.archived ? <Badge tone="gray">Archivované</Badge> : <Badge tone="blue">v{item.version}</Badge>}
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              <div className="form-grid">
                <div>
                  <label htmlFor="item-title">Názov materiálu</label>
                  <input
                    id="item-title"
                    value={newItem.title}
                    onChange={(event) => setNewItem((prev) => ({ ...prev, title: event.target.value }))}
                    placeholder="Napr. Zlomky – pracovný list"
                  />
                </div>
                <div>
                  <label htmlFor="item-desc">Popis</label>
                  <input
                    id="item-desc"
                    value={newItem.description}
                    onChange={(event) => setNewItem((prev) => ({ ...prev, description: event.target.value }))}
                    placeholder="Krátky popis pre kolegov"
                  />
                </div>
                <div className="form-actions">
                  <button type="button" disabled={busy === "item" || !newItem.title.trim()} onClick={() => void createItem()}>
                    {busy === "item" ? "Ukladám…" : "Pridať materiál"}
                  </button>
                </div>
              </div>
            </Card>
          </section>

          <section id="koncepty">
            <Card
              title="Asistent – koncepty"
              subtitle="Návrhy nikdy nejdú žiakom priamo; najprv ich schvaľuje učiteľ."
            >
              {drafts.length === 0 ? (
                <Empty>Žiadne koncepty.</Empty>
              ) : (
                <ul className="list">
                  {drafts.map((draft) => (
                    <li key={draft.id} className="list-item">
                      <div>
                        <strong>{draft.title}</strong>
                        <p className="muted small">
                          {draft.draft_type} · {DRAFT_STATUS_LABELS[draft.status] || draft.status}
                          {draft.content ? ` · ${draft.content.slice(0, 80)}` : ""}
                        </p>
                      </div>
                      <div className="row-actions">
                        <Badge tone={statusTone(draft.status)}>{DRAFT_STATUS_LABELS[draft.status] || draft.status}</Badge>
                        {draft.status === "draft" ? (
                          <button type="button" className="secondary" disabled={busy === draft.id} onClick={() => void submitDraft(draft)}>
                            {busy === draft.id ? "Odosielam…" : "Odoslať na schválenie"}
                          </button>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              <div className="form-grid">
                <div>
                  <label htmlFor="draft-title">Názov konceptu</label>
                  <input
                    id="draft-title"
                    value={newDraft.title}
                    onChange={(event) => setNewDraft((prev) => ({ ...prev, title: event.target.value }))}
                    placeholder="Napr. Opakovanie zlomkov"
                  />
                </div>
                <div>
                  <label htmlFor="draft-type">Typ</label>
                  <select
                    id="draft-type"
                    value={newDraft.draft_type}
                    onChange={(event) => setNewDraft((prev) => ({ ...prev, draft_type: event.target.value }))}
                  >
                    <option value="worksheet">Pracovný list</option>
                    <option value="test">Test</option>
                    <option value="lesson_plan">Príprava hodiny</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="draft-topics">Témy (oddelené čiarkou)</label>
                  <input
                    id="draft-topics"
                    value={newDraft.topics}
                    onChange={(event) => setNewDraft((prev) => ({ ...prev, topics: event.target.value }))}
                    placeholder="zlomky, desatinné čísla"
                  />
                </div>
                <div className="form-actions">
                  <button type="button" disabled={busy === "draft" || !newDraft.title.trim()} onClick={() => void createDraft()}>
                    {busy === "draft" ? "Vytváram…" : "Vytvoriť koncept"}
                  </button>
                </div>
              </div>

              <p className="muted small">
                Koncepty sa ukladajú pod tvoj účet. Schválenie prebieha v samostatnom kroku (K08).
              </p>
            </Card>
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
