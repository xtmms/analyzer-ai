import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../lib/api";
import { useAuth } from "../lib/auth-context";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Errore durante l'accesso.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm pt-10">
      <h1 className="text-center text-2xl font-semibold text-text">Bentornato</h1>
      <p className="mt-1 text-center text-sm text-text-muted">Accedi al tuo account per continuare.</p>

      <form onSubmit={handleSubmit} className="glass-card mt-8 space-y-4 p-6">
        {error && (
          <p className="rounded-lg border border-red-400/30 bg-red-400/10 p-3 text-sm text-red-300">
            {error}
          </p>
        )}
        <div>
          <label className="mb-1.5 block text-sm text-text-muted" htmlFor="login-email">
            Email
          </label>
          <input
            id="login-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-text outline-none focus:border-accent"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm text-text-muted" htmlFor="login-password">
            Password
          </label>
          <input
            id="login-password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-text outline-none focus:border-accent"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-accent py-2.5 font-medium text-[#0a0e17] transition hover:bg-accent-strong disabled:opacity-60"
        >
          {submitting ? "Accesso in corso…" : "Accedi"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-text-muted">
        Non hai un account?{" "}
        <Link to="/register" className="text-accent hover:underline">
          Registrati
        </Link>
      </p>
    </div>
  );
}
