import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api, type User } from "./api";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      if (!localStorage.getItem("salama_token")) return setUser(null);
      setUser(await api.me());
    } catch {
      localStorage.removeItem("salama_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function login(username: string, password: string) {
    const u = await api.login(username, password);
    setUser(u);
  }

  function logout() {
    api.logout();
    setUser(null);
  }

  return <Ctx.Provider value={{ user, loading, login, logout, refresh }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
