import { getToken } from "./auth";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(path, { ...options, headers });
  if (res.status === 401) {
    window.dispatchEvent(new CustomEvent("astarote:unauthorized"));
  }
  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

/** WebSocket URL builder that forwards the auth token as a query parameter. */
export function wsUrl(path: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  let host = window.location.host;
  if (window.location.port === "3000") {
    host = window.location.hostname + ":8000";
  }
  const token = getToken();
  const sep = path.includes("?") ? "&" : "?";
  return `${protocol}//${host}${path}${sep}token=${encodeURIComponent(token ?? "")}`;
}

/* ------------------------------------------------------------------ */
/* Shared domain types                                                */
/* ------------------------------------------------------------------ */

export interface CatalogGame {
  slug: string;
  name: string;
  tagline: string;
  description: string;
  domain: string;
  level: string;
  difficulty: number;
  duration_minutes: number;
  skills: string[];
  version: string;
  total_levels: number;
  total_points: number;
  enrolled: boolean;
  enrollment: GameSummary | null;
}

export interface GameSummary {
  id: number;
  user_id: number;
  catalog_slug: string | null;
  name: string;
  description: string | null;
  domain: string;
  level: string;
  status: string;
  current_level_index: number;
  total_levels: number;
  progress: number;
  created_at: string;
  updated_at: string;
}
