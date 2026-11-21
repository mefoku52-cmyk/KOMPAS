export type Paged<T> = { items: T[]; total: number; limit: number; offset: number };

export type StudentProfile = {
  id: string;
  student_user_id: string;
  school_year_id: string;
  grade: number;
  label: string | null;
  version: number;
  is_demo: boolean;
};

export type TopicState = {
  id: string;
  topic_id: string;
  topic_name?: string | null;
  kind: "practiced" | "verified" | string;
  status: "in_progress_practice" | "partially_mastered" | "verified_mastery" | string;
  evidence_attempt_ref: string | null;
  is_verification_evidence: boolean;
  valid_from: string;
  version: number;
};

export type Recommendation = {
  topic_id: string;
  reason: string;
  suggested_action: "practice" | "verify" | string;
};

export type Mission = {
  id: string;
  topic_id: string;
  topic_name: string;
  title: string;
  is_verification: boolean;
  task_count: number;
  is_demo: boolean;
};

export type MissionTask = {
  id: string;
  mission_id: string;
  task_type: "numeric" | "text_match" | "choice" | string;
  prompt: string;
  order_index: number;
};

export type Attempt = {
  id: string;
  task_id: string;
  task_prompt?: string | null;
  student_user_id: string;
  answer: string;
  is_correct: boolean;
  evaluated: boolean;
  valid_from: string;
};

export type ClassSummary = {
  class_group_id: string;
  name: string;
  grade: number;
  school_year_id: string;
  student_count: number;
};

export type ClassOverview = {
  class_group_id: string;
  total_students: number;
  tracked_student_topic_pairs?: number;
  by_status: Record<string, number>;
  by_kind?: Record<string, number>;
  by_topic?: Record<string, Record<string, number>>;
};

export type SuppressedCount = { value: number; suppressed: boolean };

export type AnalyticsOverview = {
  suppressed: boolean;
  threshold: number;
  total_students: number;
  tracked_pairs: number;
  by_status: Record<string, SuppressedCount>;
  by_kind: Record<string, SuppressedCount>;
  by_topic: Record<string, SuppressedCount>;
};

export type LibraryItem = {
  id: string;
  title: string;
  description: string | null;
  archived: boolean;
  version: number;
};

export type Draft = {
  id: string;
  title: string;
  draft_type: string;
  content: string | null;
  status: string;
  version: number;
};

export type OrgPlan = { id: string; name: string; description: string | null; valid_from: string };
export type OrgTask = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  due_at: string | null;
};
export type OperationRequest = {
  id: string;
  request_type: string;
  title: string;
  description: string | null;
  status: string;
  requester_user_id: string;
};

export type ChildOverview = {
  child_user_id: string;
  child_full_name: string | null;
  progress: {
    tracked_pairs: number;
    by_status: Record<string, number>;
    by_kind: Record<string, number>;
  };
  teacher_notes: { body?: string; note?: string; created_at?: string }[];
};

export type Thread = {
  id: string;
  subject: string;
  is_private: boolean;
  created_by_user_id: string;
  valid_from: string;
};

export type Message = {
  id: string;
  thread_id: string;
  sender_user_id: string;
  sender_full_name?: string | null;
  body: string;
  valid_from: string;
};
