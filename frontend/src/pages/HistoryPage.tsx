import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ReportCards } from "../components/ReportCards";
import { api, ApiError } from "../lib/api";
import type { AnalysisDetail, AnalysisSummary } from "../lib/types";

export function HistoryPage() {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AnalysisDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    api
      .history()
      .then(setAnalyses)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Errore nel caricamento dello storico."),
      )
      .finally(() => setLoading(false));
  }, []);

  async function handleSelect(id: number) {
    setLoadingDetail(true);
    setError(null);
    try {
      setSelected(await api.historyDetail(id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Errore nel caricamento dell'analisi.");
    } finally {
      setLoadingDetail(false);
    }
  }

  return (
    <div className="space-y-6 pb-16">
      <div>
        <h1 className="text-2xl font-semibold text-text">Storico analisi</h1>
        <p className="mt-1 text-sm text-text-muted">Ritrova i report generati in precedenza.</p>
      </div>

      {error && (
        <p className="rounded-lg border border-red-400/30 bg-red-400/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-text-muted">Caricamento…</p>
      ) : analyses.length === 0 ? (
        <p className="glass-card p-6 text-sm text-text-muted">
          Nessuna analisi ancora generata. Vai alla{" "}
          <Link to="/dashboard" className="text-accent hover:underline">
            Dashboard
          </Link>{" "}
          per iniziare.
        </p>
      ) : (
        <div className="glass-card divide-y divide-white/10">
          {analyses.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => handleSelect(item.id)}
              className={`flex w-full items-center justify-between px-5 py-4 text-left transition hover:bg-white/5 ${
                selected?.id === item.id ? "bg-white/5" : ""
              }`}
            >
              <div>
                <p className="font-medium text-text">{item.filename}</p>
                <p className="text-xs text-text-muted">
                  {new Date(item.created_at).toLocaleString("it-IT")} · {item.provider}/{item.model_used}
                </p>
              </div>
              <div className="text-right text-xs text-text-muted">
                <p>{item.token_count.toLocaleString()} token</p>
                <p>${item.cost_estimate.toFixed(5)}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {loadingDetail && <p className="text-sm text-text-muted">Caricamento report…</p>}

      {selected && (
        <div>
          <h2 className="mb-4 text-lg font-semibold text-text">{selected.filename}</h2>
          <ReportCards report={selected.report_json} />
        </div>
      )}
    </div>
  );
}
