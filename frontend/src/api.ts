export type DbTestRequest = {
  db_type: string; // 'postgres'
  table: string;
  use_env?: boolean;
  // manual/DSN
  dsn?: string;
  host?: string;
  port?: number;
  name?: string;
  user?: string;
  password?: string;
  sslmode?: string;
};

export type RunRequest = {
  question: string;
  user_id?: string;
  // data source
  db_type?: string; // 'postgres'
  use_env?: boolean;
  dsn?: string;
  host?: string;
  port?: number;
  name?: string;
  user?: string;
  password?: string;
  table?: string;
  sslmode?: string;
  // email overrides
  email_from?: string;
  email_to?: string;
  email_key?: string;
};

export type ScheduleJobRequest = {
  question: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  time: string; // HH:MM
  user_id?: string;
  // optional overrides (same as run)
  use_env?: boolean;
  dsn?: string;
  host?: string;
  port?: number;
  name?: string;
  user?: string;
  password?: string;
  table?: string;
  sslmode?: string;
};

export type RunResponse = {
  status: string;
  artifacts: Record<string, string>;
  preview: any[];
  run_id?: string;
};

export type LogsResponse = { status: string; logs: any[] };
export type DbTestResponse = { status: string; rows?: any[]; error?: string };
export type SchedAddResponse = { status: string; job_id: string };
export type SchedListResponse = { status: string; jobs: any[] };
export type SchedDeleteResponse = { status: string; deleted: boolean };

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function http<T>(path: string, opts: RequestInit & { json?: any } = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    method: opts.method || 'GET',
    body: opts.json ? JSON.stringify(opts.json) : opts.body,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export const api = {
  baseUrl: API_BASE,
  health: () => http<{ status: string }>(`/health`),
  run: (payload: RunRequest) => http<RunResponse>(`/run`, { method: 'POST', json: payload }),
  dbTest: (payload: DbTestRequest) => http<DbTestResponse>(`/db/test`, { method: 'POST', json: payload }),
  logs: (limit = 200) => http<LogsResponse>(`/logs?limit=${limit}`),
  schedAdd: (payload: ScheduleJobRequest) => http<SchedAddResponse>(`/scheduler/add`, { method: 'POST', json: payload }),
  schedList: () => http<SchedListResponse>(`/scheduler/list`),
  schedDelete: (jobId: string) => http<SchedDeleteResponse>(`/scheduler/${encodeURIComponent(jobId)}`, { method: 'DELETE' }),
};
