import type { Job, JobDetail } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json"
    },
    ...init
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed (${response.status})`);
  }

  return (await response.json()) as T;
}

export function getHealth(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}

export function listJobs(): Promise<Job[]> {
  return request<Job[]>("/jobs");
}

export function createJob(type: string, payload: Record<string, unknown>): Promise<Job> {
  return request<Job>("/jobs", {
    method: "POST",
    body: JSON.stringify({ type, payload })
  });
}

export function getJob(jobId: number): Promise<JobDetail> {
  return request<JobDetail>(`/jobs/${jobId}`);
}

export function retryJob(jobId: number): Promise<Job> {
  return request<Job>(`/jobs/${jobId}/retry`, {
    method: "POST"
  });
}
