import { useEffect, useState } from "react";
import { useAuth } from "../useAuth";
import { api, timeAgo, type CheckIn } from "../api";

export default function CheckIns() {
  const { user } = useAuth();
  const [items, setItems] = useState<CheckIn[]>([]);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [onlyMine, setOnlyMine] = useState(false);

  async function load() {
    try {
      setItems(await api.checkins(onlyMine));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onlyMine]);

  async function checkIn(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      let lat: number | undefined, lng: number | undefined;
      try {
        const pos = await new Promise<GeolocationPosition>((res, rej) =>
          navigator.geolocation.getCurrentPosition(res, rej, { timeout: 5000 })
        );
        lat = pos.coords.latitude;
        lng = pos.coords.longitude;
      } catch {
        /* optional */
      }
      await api.checkin({ note: note.trim(), lat, lng });
      setNote("");
      await load();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Check-ins</h1>
        <label className="flex items-center gap-2 text-xs text-slate-400">
          <input type="checkbox" checked={onlyMine} onChange={(e) => setOnlyMine(e.target.checked)} />
          only me
        </label>
      </div>

      <form onSubmit={checkIn} className="card space-y-3">
        <div>
          <label className="label">Status / note</label>
          <input className="input" value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} placeholder="I'm safe at home" />
        </div>
        <button className="btn-primary w-full" disabled={saving}>
          {saving ? "Checking in…" : "✓ Check in safely"}
        </button>
        <p className="text-center text-xs text-slate-500">Optional location is attached when permitted.</p>
      </form>

      {loading ? (
        <p className="text-slate-400">Loading…</p>
      ) : items.length === 0 ? (
        <p className="card text-slate-400">No check-ins yet. Let neighbors know you're OK.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((c) => (
            <li key={c.id} className="card">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white">{c.user_name}</span>
                <span className="text-xs text-slate-500">{timeAgo(c.created_at)}</span>
              </div>
              {c.note && <p className="mt-1 text-sm text-slate-300">{c.note}</p>}
              {c.lat != null && c.lng != null && <p className="mt-1 text-xs text-slate-500">📍 located</p>}
            </li>
          ))}
        </ul>
      )}

      {user && <p className="text-center text-xs text-slate-600">Signed in as {user.username}</p>}
    </div>
  );
}
