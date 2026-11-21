"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Alert, Badge, Bar, Card, Empty, Loading, Stat } from "@/components/ui";
import { apiFetch, formatApiError, getUserId } from "@/lib/api";
import { ACTION_LABELS, TASK_TYPE_LABELS, formatDateTime, statusLabel, statusTone } from "@/lib/labels";
import { effectiveStates } from "@/lib/progress";
import type {
  Attempt,
  Mission,
  MissionTask,
  Paged,
  Recommendation,
  StudentProfile,
  TopicState,
} from "@/lib/types";

type Data = {
  profile: StudentProfile | null;
  states: TopicState[];
  recommendations: Recommendation[];
  missions: Mission[];
  attempts: Attempt[];
  attemptsTotal: number;
};

export default function StudentPage() {
  const userId = getUserId();
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openMission, setOpenMission] = useState<Mission | null>(null);
  const [tasks, setTasks] = useState<MissionTask[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, { correct: boolean; answer: string }>>({});
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  const load = useCallback(async (): Promise<Data | null> => {
    if (!userId) return null;
    setError(null);
    try {
      const [profile, states, recommendations, missions, attempts] = await Promise.all([
        apiFetch<StudentProfile>(`/k01/profiles/${userId}/latest`).catch(() => null),
        apiFetch<Paged<TopicState>>(`/k05/states/${userId}`),
        apiFetch<Paged<Recommendation>>(`/k03/recommendations/${userId}`),
        apiFetch<Paged<Mission>>("/k04/missions"),
        apiFetch<Paged<Attempt>>("/k04/attempts/mine"),
      ]);
      const next: Data = {
        profile,
        states: states.items,
        recommendations: recommendations.items,
        missions: missions.items,
        attempts: attempts.items,
        attemptsTotal: attempts.total,
      };
      setData(next);
      return next;
    } catch (err) {
      setError(formatApiError(err, "Dáta sa nepodarilo načítať"));
      return null;
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const topicNames = useMemo(() => {
    const map = new Map<string, string>();
    data?.missions.forEach((mission) => map.set(mission.topic_id, mission.topic_name));
    data?.states.forEach((state) => {
      if (state.topic_name) map.set(state.topic_id, state.topic_name);
    });
    return map;
  }, [data?.missions, data?.states]);

  const progress = useMemo(() => {
    const states = data?.states ?? [];
    const values = Array.from(effectiveStates(states).values());
    const attempts = data?.attempts ?? [];
    const correct = attempts.filter((attempt) => attempt.is_correct).length;
    const practicedTopics = new Set(
      states.filter((state) => state.kind === "practiced").map((state) => state.topic_id)
    );
    return {
      covered: values.length,
      practiced: practicedTopics.size,
      verified: values.filter((state) => state.status === "verified_mastery").length,
      partially: values.filter((state) => state.status === "partially_mastered").length,
      states: values,
      attemptsTotal: data?.attemptsTotal ?? attempts.length,
      accuracy: attempts.length ? Math.round((correct / attempts.length) * 100) : 0,
      lastAt: attempts[0]?.valid_from,
    };
  }, [data?.states, data?.attempts, data?.attemptsTotal]);

  async function openMissionDetail(mission: Mission) {
    setFlash(null);
    setOpenMission(mission);
    setTasks([]);
    setTasksLoading(true);
    try {
      const res = await apiFetch<Paged<MissionTask>>(`/k04/missions/${mission.id}/tasks`);
      setTasks(res.items);
    } catch (err) {
      setError(formatApiError(err, "Úlohy sa nepodarilo načítať"));
    } finally {
      setTasksLoading(false);
    }
  }

  async function submitAnswer(task: MissionTask) {
    const answer = (answers[task.id] || "").trim();
    if (!answer) return;
    setSubmitting(task.id);
    setError(null);
    try {
      const attempt = await apiFetch<Attempt>("/k04/attempts", {
        method: "POST",
        body: JSON.stringify({ task_id: task.id, answer }),
      });
      setResults((prev) => ({ ...prev, [task.id]: { correct: attempt.is_correct, answer } }));
      setAnswers((prev) => ({ ...prev, [task.id]: "" }));
      const topicId = openMission?.topic_id;
      const before = topicId
        ? effectiveStates(data?.states ?? []).get(topicId)?.status
        : undefined;
      const next = await load();
      const after = topicId
        ? effectiveStates(next?.states ?? []).get(topicId)?.status
        : undefined;
      const loadedAttempts = next?.attempts ?? [];
      const loadedCorrect = loadedAttempts.filter((item) => item.is_correct).length;
      const accuracy = loadedAttempts.length
        ? Math.round((loadedCorrect / loadedAttempts.length) * 100)
        : 0;
      const stats = `pokusov ${next?.attemptsTotal ?? loadedAttempts.length} · úspešnosť ${accuracy} %`;
      if (after) {
        const label = statusLabel(after);
        const changed = before && before !== after;
        setFlash(
          changed
            ? `${attempt.is_correct ? "Správne" : "Nesprávne"} — stav témy sa zmenil: ${statusLabel(before)} -> ${label} · ${stats}.`
            : `${attempt.is_correct ? "Správne" : "Nesprávne"} — stav témy zostáva: ${label} · ${stats}.`
        );
      } else {
        setFlash(`Odpoveď uložená — ${stats}.`);
      }
      if (openMission) {
        const res = await apiFetch<Paged<MissionTask>>(`/k04/missions/${openMission.id}/tasks`);
        setTasks(res.items);
      }
    } catch (err) {
      setError(formatApiError(err, "Odpoveď sa nepodarilo odovzdať"));
    } finally {
      setSubmitting(null);
    }
  }

  function practiceMissionFor(topicId: string, action: string) {
    const match = data?.missions.find(
      (mission) => mission.topic_id === topicId && mission.is_verification === (action === "verify"),
    );
    if (match) void openMissionDetail(match);
  }

  return (
    <AppShell
      role="student"
      title="Osobný pokrok"
      subtitle="Čo už vieš, čo si precvičil a čo ti odporúčame ďalej."
      sections={[
        { id: "prehlad", label: "Prehľad" },
        { id: "odporucania", label: "Odporúčania" },
        { id: "misie", label: "Misie" },
        { id: "historia", label: "História" },
      ]}
    >
      {error ? <Alert>{error}</Alert> : null}
      {!data ? <Loading /> : null}

      {data ? (
        <>
          <section id="prehlad" className="grid">
            <Stat label="Prebraté témy" value={progress.covered} hint="témy so záznamom" />
            <Stat label="Precvičované" value={progress.practiced} tone="blue" hint="aspoň jeden pokus" />
            <Stat label="Čiastočne zvládnuté" value={progress.partially} tone="amber" />
            <Stat label="Overené zvládnutie" value={progress.verified} tone="green" hint="overené misiou" />
            <Stat label="Odovzdané odpovede" value={progress.attemptsTotal} hint="všetky pokusy" />
            <Stat
              label="Úspešnosť"
              value={`${progress.accuracy} %`}
              tone={progress.accuracy >= 60 ? "green" : "amber"}
              hint={progress.lastAt ? `naposledy ${formatDateTime(progress.lastAt)}` : "zatiaľ bez pokusu"}
            />
          </section>

          {flash ? <Alert tone="blue">{flash}</Alert> : null}

          {data.profile ? (
            <Card title="Môj profil" subtitle="Údaje pre aktuálny školský rok">
              <div className="kv">
                <span>Ročník</span>
                <strong>{data.profile.grade}</strong>
                <span>Označenie</span>
                <strong>{data.profile.label || "—"}</strong>
                <span>Verzia profilu</span>
                <strong>v{data.profile.version}</strong>
              </div>
            </Card>
          ) : null}

          <section id="odporucania">
            <Card
              title="Odporúčania"
              subtitle="Vychádzajú z tvojich posledných záznamov o učení."
            >
              {data.recommendations.length === 0 ? (
                <Empty>Zatiaľ žiadne odporúčania. Precviči si nejakú misiu.</Empty>
              ) : (
                <ul className="list">
                  {data.recommendations.map((rec) => (
                    <li key={`${rec.topic_id}-${rec.suggested_action}`} className="list-item">
                      <div>
                        <strong>{topicNames.get(rec.topic_id) || "Téma"}</strong>
                        <p className="muted small">{rec.reason}</p>
                      </div>
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => practiceMissionFor(rec.topic_id, rec.suggested_action)}
                      >
                        {ACTION_LABELS[rec.suggested_action] || "Otvoriť"}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </section>

          <section id="misie">
            <Card title="Misie" subtitle="Vyber misiu a odpovedz na jej úlohy.">
              {data.missions.length === 0 ? (
                <Empty>Žiadne misie.</Empty>
              ) : (
                <ul className="list">
                  {data.missions.map((mission) => (
                    <li key={mission.id} className="list-item">
                      <div>
                        <strong>{mission.title}</strong>
                        <p className="muted small">
                          {mission.topic_name} · {mission.task_count} úloh
                        </p>
                      </div>
                      <div className="row-actions">
                        {mission.is_verification ? <Badge tone="green">Overenie</Badge> : <Badge tone="blue">Precvičovanie</Badge>}
                        <button type="button" onClick={() => void openMissionDetail(mission)}>
                          Otvoriť
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              {openMission ? (
                <div className="mission-detail">
                  <div className="card-head">
                    <div>
                      <h3>{openMission.title}</h3>
                      <p className="muted small">{openMission.topic_name}</p>
                    </div>
                    <button className="secondary" type="button" onClick={() => setOpenMission(null)}>Zavrieť</button>
                  </div>
                  {tasksLoading ? <Loading label="Načítavam úlohy…" /> : null}
                  {!tasksLoading && tasks.length === 0 ? <Empty>Táto misia zatiaľ nemá úlohy.</Empty> : null}
                  <ol className="task-list">
                    {tasks.map((task) => {
                      const result = results[task.id];
                      return (
                        <li key={task.id} className="task">
                          <p className="task-prompt">{task.prompt}</p>
                          <span className="muted small">{TASK_TYPE_LABELS[task.task_type] || task.task_type}</span>
                          <div className="task-input">
                            <input
                              aria-label={`Odpoveď na úlohu ${task.order_index}`}
                              value={answers[task.id] ?? ""}
                              onChange={(event) =>
                                setAnswers((prev) => ({ ...prev, [task.id]: event.target.value }))
                              }
                              placeholder="Tvoja odpoveď"
                            />
                            <button
                              type="button"
                              disabled={submitting === task.id || !(answers[task.id] || "").trim()}
                              onClick={() => void submitAnswer(task)}
                            >
                              {submitting === task.id ? "Odosielam…" : "Odovzdať"}
                            </button>
                          </div>
                          {result ? (
                            <p className={result.correct ? "result ok" : "result bad"}>
                              {result.correct ? "Správne" : "Nesprávne"} — tvoja odpoveď: {result.answer}
                            </p>
                          ) : null}
                        </li>
                      );
                    })}
                  </ol>
                </div>
              ) : null}
            </Card>
          </section>

          <section id="historia" className="grid">
            <Card title="Stav učiva" subtitle="Efektívny stav témy — precvičenie ho nezníži, overenie ho vždy nastaví.">
              {progress.states.length === 0 ? (
                <Empty>Zatiaľ žiadny záznam.</Empty>
              ) : (
                <div className="stack">
                  {progress.states.map((state) => (
                    <div key={state.topic_id} className="bar-row">
                      <span className="bar-label">{topicNames.get(state.topic_id) || "Téma"}</span>
                      <Badge tone={statusTone(state.status)}>{statusLabel(state.status)}</Badge>
                    </div>
                  ))}
                  <Bar
                    label="Overené z celku"
                    value={progress.verified}
                    total={Math.max(progress.covered, 1)}
                    tone="green"
                  />
                </div>
              )}
            </Card>

            <Card title="Moje pokusy" subtitle="Najnovších 5 odovzdaní">
              {data.attempts.length === 0 ? (
                <Empty>Zatiaľ žiadne pokusy.</Empty>
              ) : (
                <ul className="list compact">
                  {data.attempts.slice(0, 5).map((attempt) => (
                    <li key={attempt.id} className="list-item">
                      <div>
                        <strong>{attempt.task_prompt || "Úloha"}</strong>
                        <p className="muted small">
                          {formatDateTime(attempt.valid_from)} · odpoveď: {attempt.answer}
                        </p>
                      </div>
                      <Badge tone={attempt.is_correct ? "green" : "red"}>
                        {attempt.is_correct ? "Správne" : "Nesprávne"}
                      </Badge>
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
