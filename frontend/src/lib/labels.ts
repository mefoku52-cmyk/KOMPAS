export const STATUS_LABELS: Record<string, string> = {
  in_progress_practice: "Precvičuje",
  partially_mastered: "Čiastočne zvládnuté",
  verified_mastery: "Overené zvládnutie",
};

export const KIND_LABELS: Record<string, string> = {
  practiced: "Precvičené",
  verified: "Overené",
};

export const ACTION_LABELS: Record<string, string> = {
  practice: "Precvičiť",
  verify: "Overiť",
};

export const REQUEST_STATUS_LABELS: Record<string, string> = {
  submitted: "Podaná",
  approved: "Schválená",
  rejected: "Zamietnutá",
  in_progress: "V riešení",
  fulfilled: "Vybavená",
  cancelled: "Zrušená",
};

export const DRAFT_STATUS_LABELS: Record<string, string> = {
  draft: "Koncept",
  submitted: "Odoslané na schválenie",
  approved: "Schválené",
};

export const TASK_TYPE_LABELS: Record<string, string> = {
  numeric: "Číslo",
  text_match: "Text",
  choice: "Voľba",
};

export function statusLabel(value: string): string {
  return STATUS_LABELS[value] || value;
}

export function kindLabel(value: string): string {
  return KIND_LABELS[value] || value;
}

export function statusTone(value: string): "green" | "amber" | "blue" | "gray" {
  if (value === "verified_mastery" || value === "approved" || value === "fulfilled") return "green";
  if (value === "partially_mastered" || value === "submitted" || value === "in_progress") return "amber";
  if (value === "in_progress_practice" || value === "draft") return "blue";
  return "gray";
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("sk-SK", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("sk-SK", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function percent(part: number, total: number): number {
  if (!total) return 0;
  return Math.round((part / total) * 100);
}
