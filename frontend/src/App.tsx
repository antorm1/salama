import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./useAuth";
import Layout from "./Layout";
import Home from "./pages/Home";
import Alerts from "./pages/Alerts";
import CheckIns from "./pages/CheckIns";
import Login from "./pages/Login";
import Register from "./pages/Register";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-400">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/alerts" element={<RequireAuth><Alerts /></RequireAuth>} />
          <Route path="/checkins" element={<RequireAuth><CheckIns /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </AuthProvider>
  );
}
