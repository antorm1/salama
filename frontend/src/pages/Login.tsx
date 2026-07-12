import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../useAuth";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await login(username.trim().toLowerCase(), password);
      nav("/");
    } catch (ex) {
      setErr((ex as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5 pt-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white">Welcome back</h1>
        <p className="mt-1 text-slate-400">Sign in to Salama.</p>
      </div>
      <form onSubmit={submit} className="card space-y-3">
        <div>
          <label className="label">Username</label>
          <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} required autoCapitalize="none" />
        </div>
        <div>
          <label className="label">Password</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {err && <p className="text-sm text-red-400">{err}</p>}
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      </form>
      <p className="text-center text-sm text-slate-400">
        No account? <Link to="/register" className="text-brand-light hover:underline">Create one</Link>
      </p>
      <p className="mx-auto max-w-xs text-center text-xs text-slate-600">
        A default admin is seeded: <code>admin</code> / <code>salama-admin-pass</code> — change it via env.
      </p>
    </div>
  );
}
