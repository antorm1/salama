import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../useAuth";
import { api } from "../api";

export default function Register() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [phone, setPhone] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await api.register({ username: username.trim().toLowerCase(), phone, display_name: displayName.trim(), password });
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
        <h1 className="text-2xl font-bold text-white">Join Salama</h1>
        <p className="mt-1 text-slate-400">Create your safety account.</p>
      </div>
      <form onSubmit={submit} className="card space-y-3">
        <div>
          <label className="label">Username</label>
          <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} autoCapitalize="none" />
        </div>
        <div>
          <label className="label">Phone</label>
          <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} required placeholder="+2547..." />
        </div>
        <div>
          <label className="label">Display name (optional)</label>
          <input className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} maxLength={80} />
        </div>
        <div>
          <label className="label">Password</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
        </div>
        {err && <p className="text-sm text-red-400">{err}</p>}
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
      </form>
      <p className="text-center text-sm text-slate-400">
        Already have one? <Link to="/login" className="text-brand-light hover:underline">Sign in</Link>
      </p>
    </div>
  );
}
