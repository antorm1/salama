import { useEffect, useState } from "react";
import { useAuth } from "../useAuth";
import { api, CATEGORIES, SEVERITIES, severityStyle, timeAgo, type Alert, type AlertStatus, type Category, type Severity } from "../api";

export default function Alerts() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<AlertStatus | "all">("active");
  const [filter, setFilter] = useState<"" | Category>("");

  // New-alert form
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<Category>("hazard");
  const [severity, setSeverity] = useState<Severity>("medium");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  async function load() {
    try {
      setAlerts(await api.alerts(status, filter || undefined));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, filter]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setSaving(true);
    try {
      await api.createAlert({ category, severity, title: title.trim(), description: description.trim() });
      setTitle("");
      setDescription("");
      setShowForm(false);
      await load();
    } catch (ex) {
      setErr((ex as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function resolve(a: Alert) {
    await api.setAlertStatus(a.id, a.status === "active" ? "resolved" : "active");
    load();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Alerts</h1>
        <button className="btn-primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Close" : "+ New"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={submit} className="card space-y-3">
          <div>
            <label className="label">Title</label>
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={160} placeholder="e.g. Flooded road on Moi Ave" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Category</label>
              <select className="input" value={category} onChange={(e) => setCategory(e.target.value as Category)}>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Severity</label>
              <select className="input" value={severity} onChange={(e) => setSeverity(e.target.value as Severity)}>
                {SEVERITIES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Details</label>
            <textarea className="input" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} maxLength={2000} placeholder="What's happening? Any landmarks?" />
          </div>
          {err && <p className="text-sm text-red-400">{err}</p>}
          <button className="btn-primary w-full" disabled={saving}>
            {saving ? "Posting…" : "Post alert"}
          </button>
        </form>
      )}

      <div className="flex flex-wrap gap-2 text-xs">
        {(["active", "resolved", "all"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`rounded-full border px-3 py-1 ${status === s ? "border-brand-light text-white" : "border-white/10 text-slate-400"}`}
          >
            {s}
          </button>
        ))}
        <select className="rounded-full border border-white/10 bg-transparent px-3 py-1 text-slate-300" value={filter} onChange={(e) => setFilter(e.target.value as "" | Category)}>
          <option value="">all categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <p className="text-slate-400">Loading…</p>
      ) : alerts.length === 0 ? (
        <p className="card text-slate-400">Nothing here.</p>
      ) : (
        <ul className="space-y-3">
          {alerts.map((a) => (
            <li key={a.id} className="card">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-white">{a.title}</h3>
                  <p className="mt-1 text-sm text-slate-400">{a.description || "No details."}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    {a.author_name} · {timeAgo(a.created_at)}
                    {a.lat != null && a.lng != null && " · 📍 located"}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className={`rounded-full border px-2 py-0.5 text-xs uppercase ${severityStyle(a.severity)}`}>{a.severity}</span>
                  <span className="rounded-full border border-white/10 px-2 py-0.5 text-xs uppercase text-slate-300">{a.category}</span>
                </div>
              </div>
              {(user?.is_admin || user?.id === a.author_id) && (
                <button onClick={() => resolve(a)} className="btn-ghost mt-3 w-full">
                  Mark {a.status === "active" ? "resolved" : "active"}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
