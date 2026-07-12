import { Link, useLocation, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "./useAuth";

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();

  const tabs = [
    { to: "/", label: "Home" },
    { to: "/alerts", label: "Alerts" },
    { to: "/checkins", label: "Check-ins" }
  ];

  return (
    <div className="mx-auto flex min-h-full max-w-2xl flex-col">
      <header className="safe-top sticky top-0 z-10 border-b border-white/10 bg-brand-dark/90 backdrop-blur">
        <div className="flex items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-bold text-white">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand">S</span>
            Salama
          </Link>
          {user && (
            <div className="flex items-center gap-3 text-sm">
              <span className="hidden text-slate-400 sm:inline">{user.display_name || user.username}</span>
              <button
                className="text-slate-400 hover:text-white"
                onClick={() => {
                  logout();
                  nav("/login");
                }}
              >
                Sign out
              </button>
            </div>
          )}
        </div>
        <nav className="flex gap-1 px-2 pb-1">
          {tabs.map((t) => (
            <Link
              key={t.to}
              to={t.to}
              className={`px-3 py-2 text-sm font-medium ${
                loc.pathname === t.to ? "text-white border-b-2 border-brand-light" : "text-slate-400 hover:text-white"
              }`}
            >
              {t.label}
            </Link>
          ))}
        </nav>
      </header>

      <main className="flex-1 px-4 py-5">{children}</main>

      <footer className="safe-bottom border-t border-white/10 px-4 py-3 text-center text-xs text-slate-500">
        Salama · offline-first community safety
      </footer>
    </div>
  );
}
