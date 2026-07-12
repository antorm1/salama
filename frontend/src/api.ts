// Thin typed API client. All tokens are stored in localStorage; no secrets in code.
const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) || "http://localhost:8000";

export const CATEGORIES = ["sos", "hazard", "medical", "weather", "crime", "other"] as const;
export const SEVERITIES = ["low", "medium", "high", "critical"] as const;

export type Category = (typeof CATEGORIES)[number];
export type Severity = (typeof SEVERITIES)[number];
export type AlertStatus = "active" | "resolved";

export interface User {
  id: number;
  username: string;
  phone: string;
  display_name: string;
  is_admin: boolean;
  created_at: string;
}

export interface Alert {
  id: number;
  author_id: number;
  author_name: string;
  category: Category;
  severity: Severity;
  title: string;
  description: string;
  lat: number | null;
  lng: number | null;
  status: AlertStatus;
  created_at: string;
  updated_at: string;
}

export interface CheckIn {
  id: number;
  user_id: number;
  user_name: string;
  note: string;
  lat: number | null;
  lng: number | null;
  created_at: string;
}

function token(): string | null {
  return localStorage.getItem("salama_token");
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const t = token();
  if (t) headers["Authorization"] = `Bearer ${t}`;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) msg = Array.isArray(body.detail) ? body.detail[0]?.msg || msg : String(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  async health() {
    return request<{ status: string }>("/health");
  },
  async register(data: { username: string; phone: string; display_name?: string; password: string }) {
    return request<User>("/auth/register", { method: "POST", body: JSON.stringify(data) });
  },
  async login(username: string, password: string) {
    const r = await request<{ access_token: string }>("/auth/token", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
    localStorage.setItem("salama_token", r.access_token);
    return api.me();
  },
  logout() {
    localStorage.removeItem("salama_token");
  },
  async me() {
    return request<User>("/auth/me");
  },
  async alerts(status: AlertStatus | "all" = "active", category?: string) {
    const qs = new URLSearchParams({ status: status });
    if (category) qs.set("category", category);
    return request<Alert[]>(`/alerts?${qs.toString()}`);
  },
  async createAlert(data: { category: Category; severity: Severity; title: string; description?: string; lat?: number; lng?: number }) {
    return request<Alert>("/alerts", { method: "POST", body: JSON.stringify(data) });
  },
  async setAlertStatus(id: number, status: AlertStatus) {
    return request<Alert>(`/alerts/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });
  },
  async checkins(onlyMine = false) {
    return request<CheckIn[]>(`/checkins?only_mine=${onlyMine}`);
  },
  async checkin(data: { note?: string; lat?: number; lng?: number }) {
    return request<CheckIn>("/checkins", { method: "POST", body: JSON.stringify(data) });
  }
};

export function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const s = Math.floor((Date.now() - then) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function severityStyle(sev: Severity): string {
  switch (sev) {
    case "critical":
      return "bg-red-600/20 text-red-300 border-red-500/40";
    case "high":
      return "bg-orange-500/20 text-orange-300 border-orange-400/40";
    case "medium":
      return "bg-yellow-500/20 text-yellow-300 border-yellow-400/40";
    default:
      return "bg-slate-500/20 text-slate-300 border-slate-400/40";
  }
}
