import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../useAuth";
import { api, type Alert } from "../api";

export default function Home() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [online, setOnline] = useState(navigator.onLine);
  const [sosBusy, setSosBusy] = useState(false);

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  useEffect(() => {
    if (!user) return;
    api
      .alerts("active")
      .then(setAlerts)
      .catch(() => setAlerts([]));
  }, [user]);

  async function sos() {
    if (!user) return;
    setSosBusy(true);
    try {
      // Best-effort geolocation; falls back to null and the backend still records the SOS.
      let lat: number | undefined, lng: number | undefined;
      try {
        const pos = await new Promise<GeolocationPosition>((res, rej) =>
          navigator.geolocation.getCurrentPosition(res, rej, { timeout: 5000 })
        );
        lat = pos.coords.latitude;
        lng = pos.coords.longitude;
      } catch {
        /* location denied */
      }
      await api.createAlert({ category: "sos", severity: "critical", title: "SOS — need help", lat, lng });
      const fresh = await api.alerts("active");
      setAlerts(fresh);
    } catch (e) {
      alert("SOS failed: " + (e as Error).message);
    } finally {
      setSosBusy(false);
    }
  }

  if (!user) {
    return (
      <div className="space-y-6 text-center">
        <div className="card">
          <h1 className="text-2xl font-bold text-white">Stay safe, together.</h1>
          <p className="mt-2 text-slate-400">
            Salama is an offline-first community safety app: raise an SOS, share local hazards, and check in
            with neighbors — even on flaky connections.
          </p>
        </div>
        <div className="flex justify-center gap-3">
          <Link to="/login" className="btn-primary">Sign in</Link>
          <Link to="/register" className="btn-ghost">Create account</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <button onClick={sos} disabled={sosBusy} className="btn-danger w-full text-base">
        {sosBusy ? "Sending SOS…" : "🆘 SOS — I NEED HELP"}
      </button>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Active near you</h2>
        <span className={`text-xs ${online ? "text-emerald-400" : "text-amber-400"}`}>
          {online ? "● online" : "● offline"}
        </span>
      </div>

      {alerts.length === 0 ? (
        <p className="card text-slate-400">No active alerts. Stay alert and look out for each other.</p>
      ) : (
        <ul className="space-y-2">
          {alerts.slice(0, 5).map((a) => (
            <li key={a.id} className="card">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white">{a.title}</span>
                <span className="rounded-full border px-2 py-0.5 text-xs uppercase">{a.category}</span>
              </div>
              <p className="mt-1 text-sm text-slate-400">by {a.author_name}</p>
            </li>
          ))}
        </ul>
      )}

      <div className="grid grid-cols-2 gap-3 pt-2">
        <Link to="/alerts" className="btn-ghost">View all alerts</Link>
        <Link to="/checkins" className="btn-ghost">Check in</Link>
      </div>
    </div>
  );
}
