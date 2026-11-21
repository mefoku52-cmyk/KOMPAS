import type { TopicState } from "@/lib/types";

export const STATUS_RANK: Record<string, number> = {
  in_progress_practice: 1,
  partially_mastered: 2,
  verified_mastery: 3,
};

/**
 * Mirrors backend `app/shared/progress.py`: `progress_topic_state` is append-only,
 * so the newest row alone is not the topic's state. Practice can lift a topic but
 * never lower it; a verification attempt always applies (even when it fails).
 */
export function effectiveStates(states: TopicState[]): Map<string, TopicState> {
  const ordered = [...states].sort((a, b) => {
    const delta = new Date(a.valid_from).getTime() - new Date(b.valid_from).getTime();
    return delta !== 0 ? delta : (a.version ?? 0) - (b.version ?? 0);
  });
  const folded = new Map<string, TopicState>();
  for (const state of ordered) {
    const prev = folded.get(state.topic_id);
    if (!prev) {
      folded.set(state.topic_id, state);
      continue;
    }
    if (state.kind === "verified") {
      folded.set(state.topic_id, state);
      continue;
    }
    if ((STATUS_RANK[state.status] ?? 0) > (STATUS_RANK[prev.status] ?? 0)) {
      folded.set(state.topic_id, state);
    }
  }
  return folded;
}
