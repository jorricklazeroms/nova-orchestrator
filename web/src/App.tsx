import { FormEvent, useEffect, useMemo, useState } from "react";

import { createJob, getHealth, getJob, listJobs, retryJob } from "./api";
import { formatStatusLabel } from "./lib/status";
import type { Job, JobDetail } from "./types";

export function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobDetail | null>(null);
  const [jobType, setJobType] = useState("email");
  const [jobPayload, setJobPayload] = useState('{"message":"hello"}');
  const [health, setHealth] = useState("checking...");
  const [error, setError] = useState<string | null>(null);

  async function refreshJobs() {
    try {
      const next = await listJobs();
      setJobs(next);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function refreshHealth() {
    try {
      const status = await getHealth();
      setHealth(status.status);
    } catch {
      setHealth("offline");
    }
  }

  useEffect(() => {
    refreshHealth();
    refreshJobs();
    const timer = window.setInterval(refreshJobs, 2000);
    return () => window.clearInterval(timer);
  }, []);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(jobPayload) as Record<string, unknown>;
    } catch {
      setError("Payload must be valid JSON.");
      return;
    }

    try {
      await createJob(jobType, payload);
      await refreshJobs();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function openJob(jobId: number) {
    setError(null);
    try {
      const detail = await getJob(jobId);
      setSelectedJob(detail);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function onRetry(jobId: number) {
    setError(null);
    try {
      await retryJob(jobId);
      await refreshJobs();
      await openJob(jobId);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const selectedTitle = useMemo(() => {
    if (!selectedJob) {
      return "No job selected";
    }
    return `Job #${selectedJob.id} (${selectedJob.type})`;
  }, [selectedJob]);

  return (
    <main className="layout">
      <header>
        <h1>Nova Orchestrator v0.1</h1>
        <p>API health: {health}</p>
      </header>

      <section className="panel">
        <h2>Create Job</h2>
        <form onSubmit={handleCreate} className="form">
          <label>
            Type
            <input value={jobType} onChange={(event) => setJobType(event.target.value)} required />
          </label>
          <label>
            Payload JSON
            <textarea
              rows={5}
              value={jobPayload}
              onChange={(event) => setJobPayload(event.target.value)}
            />
          </label>
          <button type="submit">Queue Job</button>
        </form>
      </section>

      <section className="panel two-col">
        <div>
          <h2>Jobs</h2>
          <ul className="job-list">
            {jobs.map((job) => (
              <li key={job.id}>
                <button onClick={() => openJob(job.id)} className="job-item" type="button">
                  <span>#{job.id}</span>
                  <span>{job.type}</span>
                  <span className={`status status-${job.status}`}>{formatStatusLabel(job.status)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2>{selectedTitle}</h2>
          {selectedJob && (
            <>
              <p>Status: {formatStatusLabel(selectedJob.status)}</p>
              <p>Attempts: {selectedJob.attempt_count}</p>
              {selectedJob.status === "failed" && (
                <button type="button" onClick={() => onRetry(selectedJob.id)}>
                  Retry failed job
                </button>
              )}
              <h3>Logs</h3>
              <ul className="logs">
                {selectedJob.logs.map((log, index) => (
                  <li key={`${log.created_at}-${index}`}>
                    [{log.level}] {log.message}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </section>

      {error && <p className="error">{error}</p>}
    </main>
  );
}
