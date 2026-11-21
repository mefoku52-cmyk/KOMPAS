"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Alert, Badge, Card, Empty, Loading, Stat } from "@/components/ui";
import { apiFetch, formatApiError, getUserId } from "@/lib/api";
import { formatDateTime, kindLabel, statusLabel, statusTone } from "@/lib/labels";
import type { ChildOverview, Message, Paged, Thread } from "@/lib/types";

export default function ParentPage() {
  const myId = getUserId();
  const [children, setChildren] = useState<string[]>([]);
  const [overviews, setOverviews] = useState<ChildOverview[]>([]);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThread, setActiveThread] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [childRes, threadRes] = await Promise.all([
        apiFetch<Paged<string>>("/parent/children"),
        apiFetch<Paged<Thread>>("/communication/threads"),
      ]);
      setChildren(childRes.items);
      setThreads(threadRes.items);
      setActiveThread((prev) => prev ?? threadRes.items[0]?.id ?? null);
      const loaded = await Promise.all(
        childRes.items.map((childId) =>
          apiFetch<ChildOverview>(`/parent/children/${childId}`).catch(() => null),
        ),
      );
      setOverviews(loaded.filter((value): value is ChildOverview => value !== null));
    } catch (err) {
      setError(formatApiError(err, "Dáta sa nepodarilo načítať"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const loadMessages = useCallback(async (threadId: string) => {
    try {
      const res = await apiFetch<Paged<Message>>(`/communication/threads/${threadId}/messages`);
      setMessages(res.items);
    } catch (err) {
      setError(formatApiError(err, "Správy sa nepodarilo načítať"));
    }
  }, []);

  useEffect(() => {
    if (activeThread) void loadMessages(activeThread);
  }, [activeThread, loadMessages]);

  async function sendMessage() {
    if (!activeThread || !draft.trim()) return;
    setSending(true);
    setError(null);
    try {
      await apiFetch<Message>(`/communication/threads/${activeThread}/messages`, {
        method: "POST",
        body: JSON.stringify({ body: draft.trim() }),
      });
      setDraft("");
      await loadMessages(activeThread);
    } catch (err) {
      setError(formatApiError(err, "Správu sa nepodarilo odoslať"));
    } finally {
      setSending(false);
    }
  }

  return (
    <AppShell
      role="parent"
      title="Rodičovský prehľad"
      subtitle="Schválené informácie o tvojom dieťati a komunikácia so školou."
      sections={[
        { id: "deti", label: "Dieťa" },
        { id: "komunikacia", label: "Komunikácia" },
      ]}
    >
      {error ? <Alert>{error}</Alert> : null}
      {loading ? <Loading /> : null}

      {!loading ? (
        <>
          <section id="deti">
            {overviews.length === 0 ? (
              <Card title="Dieťa">
                <Empty>Nemáš prepojené žiadne dieťa.</Empty>
              </Card>
            ) : (
              overviews.map((child) => (
                <Card
                  key={child.child_user_id}
                  title={child.child_full_name || "Dieťa"}
                  subtitle="Súkromné poznámky učiteľa sa tu nikdy nezobrazujú."
                >
                  <div className="grid">
                    <Stat label="Sledované témy" value={child.progress.tracked_pairs} />
                    <Stat
                      label="Overené zvládnutie"
                      value={child.progress.by_status?.verified_mastery ?? 0}
                      tone="green"
                    />
                    <Stat
                      label="Na precvičenie"
                      value={child.progress.by_status?.partially_mastered ?? 0}
                      tone="amber"
                    />
                    <Stat
                      label="V precvičovaní"
                      value={child.progress.by_status?.in_progress_practice ?? 0}
                      tone="blue"
                    />
                  </div>

                  <div className="stack">
                    {Object.entries(child.progress.by_status ?? {}).map(([status, value]) => (
                      <div key={status} className="bar-row">
                        <span className="bar-label">{statusLabel(status)}</span>
                        <Badge tone={statusTone(status)}>{value}</Badge>
                      </div>
                    ))}
                    {Object.entries(child.progress.by_kind ?? {}).map(([kind, value]) => (
                      <div key={`kind-${kind}`} className="bar-row">
                        <span className="bar-label muted">{kindLabel(kind)}</span>
                        <span className="bar-value">{value}</span>
                      </div>
                    ))}
                  </div>

                  {child.teacher_notes.length > 0 ? (
                    <div className="stack">
                      <h3>Poznámky učiteľa</h3>
                      <ul className="list">
                        {child.teacher_notes.map((note, index) => (
                          <li key={index} className="list-item">
                            <p className="muted small">{note.body || note.note || ""}</p>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </Card>
              ))
            )}
          </section>

          <section id="komunikacia">
            <Card
              title="Komunikácia so školou"
              subtitle="Vidíš len vlákna, ktorých si účastníkom."
              actions={
                threads.length > 1 ? (
                  <select
                    aria-label="Vyber vlákno"
                    value={activeThread ?? ""}
                    onChange={(event) => setActiveThread(event.target.value)}
                  >
                    {threads.map((thread) => (
                      <option key={thread.id} value={thread.id}>{thread.subject}</option>
                    ))}
                  </select>
                ) : undefined
              }
            >
              {threads.length === 0 ? (
                <Empty>Žiadne vlákna.</Empty>
              ) : (
                <>
                  {threads.length === 1 ? (
                    <p className="muted small">Vlákno: {threads[0].subject}</p>
                  ) : null}
                  <ul className="messages">
                    {messages.map((message) => {
                      const mine = message.sender_user_id === myId;
                      return (
                        <li key={message.id} className={mine ? "message mine" : "message"}>
                          <div className="message-head">
                            <strong>{mine ? "Ja" : message.sender_full_name || "Účastník"}</strong>
                            <span className="muted small">{formatDateTime(message.valid_from)}</span>
                          </div>
                          <p>{message.body}</p>
                        </li>
                      );
                    })}
                  </ul>

                  <div className="message-form">
                    <label htmlFor="message-body">Nová správa</label>
                    <textarea
                      id="message-body"
                      rows={3}
                      value={draft}
                      onChange={(event) => setDraft(event.target.value)}
                      placeholder="Napíš správu škole…"
                    />
                    <div className="form-actions">
                      <button type="button" disabled={sending || !draft.trim()} onClick={() => void sendMessage()}>
                        {sending ? "Odosielam…" : "Odoslať"}
                      </button>
                    </div>
                  </div>
                </>
              )}
            </Card>
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
