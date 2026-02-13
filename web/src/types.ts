export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export interface Job {
  id: number;
  type: string;
  payload: Record<string, unknown>;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  finished_at: string | null;
  attempt_count: number;
  last_error: string | null;
}

export interface JobDetail extends Job {
  logs: Array<{ level: string; message: string; created_at: string }>;
}
