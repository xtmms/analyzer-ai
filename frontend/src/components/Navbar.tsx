import { LogOut, ScanSearch } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../lib/auth-context";

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-[#0a0e17]/70 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-text">
          <ScanSearch className="h-5 w-5 text-accent" strokeWidth={2} />
          AI Log Analyzer
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {user ? (
            <>
              <Link to="/dashboard" className="text-text-muted transition hover:text-text">
                Dashboard
              </Link>
              <Link to="/history" className="text-text-muted transition hover:text-text">
                Storico
              </Link>
              <span className="rounded-full border border-white/10 px-3 py-1 text-xs font-medium uppercase tracking-wide text-accent">
                {user.plan}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-text-muted transition hover:border-accent hover:text-text"
              >
                <LogOut className="h-3.5 w-3.5" strokeWidth={2} />
                Esci
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-text-muted transition hover:text-text">
                Accedi
              </Link>
              <Link
                to="/register"
                className="rounded-lg bg-accent px-4 py-1.5 font-medium text-[#0a0e17] transition hover:bg-accent-strong"
              >
                Inizia gratis
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
