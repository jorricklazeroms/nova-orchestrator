import type { JobStatus } from "../types";

export function formatStatusLabel(status: JobStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
