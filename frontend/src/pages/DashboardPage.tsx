import { useEffect, useMemo, useState } from "react";

import { CostCard } from "../components/CostCard";
import { ProviderModelSelect } from "../components/ProviderModelSelect";
import { ReportCards } from "../components/ReportCards";
import { SeverityDonutChart } from "../components/SeverityDonutChart";
import { SeverityFilters } from "../components/SeverityFilters";
import { TerminalPreview } from "../components/TerminalPreview";
import { UploadCard } from "../components/UploadCard";
import { UsageBadge } from "../components/UsageBadge";
import { api, ApiError } from "../lib/api";
import { buildMarkdownReport } from "../lib/markdown";
import { DEFAULT_SEVERITY_FILTER } from "../lib/types";
import type { AnalyzeLogsOut, EstimateOut, ParseLogsOut, ProviderOut, UsageOut } from "../lib/types";

export function DashboardPage() {
  const [fileName, setFileName] = useState<string | null>(null);
  const [logContent, setLogContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [severities, setSeverities] = useState<string[]>(DEFAULT_SEVERITY_FILTER);
  const [searchQuery, setSearchQuery] = useState("");
  const [maxLines, setMaxLines] = useState(200);
  const [sliceFromEnd, setSliceFromEnd] = useState(true);
  const [dedupe, setDedupe] = useState(true);

  const [parseResult, setParseResult] = useState<ParseLogsOut | null>(null);
  const [parsing, setParsing] = useState(false);

  const [providers, setProviders] = useState<ProviderOut[]>([]);
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");

  const [estimate, setEstimate] = useState<EstimateOut | null>(null);
  const [estimating, setEstimating] = useState(false);

  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeLogsOut | null>(null);

  const [usage, setUsage] = useState<UsageOut | null>(null);

  useEffect(() => {
    api
      .providers()
      .then((list) => {
        setProviders(list);
        if (list.length > 0) {
          setProvider(list[0].id);
          setModel(list[0].default_model);
        }
      })
      .catch(() => setError("Impossibile caricare i provider AI disponibili."));
    api.usage().then(setUsage).catch(() => {});
  }, []);

  useEffect(() => {
    if (!logContent) {
      setParseResult(null);
      return;
    }
    setParsing(true);
    const timeout = setTimeout(() => {
      api
        .parseLogs({
          log_content: logContent,
          severities,
          search_query: searchQuery,
          max_lines: maxLines,
          slice_from_end: sliceFromEnd,
          dedupe,
        })
        .then((result) => {
          setParseResult(result);
          setError(null);
        })
        .catch((err) =>
          setError(err instanceof ApiError ? err.message : "Errore nel parsing dei log."),
        )
        .finally(() => setParsing(false));
    }, 300);
    return () => clearTimeout(timeout);
  }, [logContent, severities, searchQuery, maxLines, sliceFromEnd, dedupe]);

  const logsPayload = useMemo(() => parseResult?.logs_to_send.join("\n") ?? "", [parseResult]);

  useEffect(() => {
    if (!logsPayload || !provider || !model) {
      setEstimate(null);
      return;
    }
    setEstimating(true);
    const timeout = setTimeout(() => {
      api
        .estimate({ provider, model, logs_payload: logsPayload })
        .then(setEstimate)
        .catch(() => setEstimate(null))
        .finally(() => setEstimating(false));
    }, 400);
    return () => clearTimeout(timeout);
  }, [logsPayload, provider, model]);

  function handleFileLoaded(content: string, name: string) {
    setLogContent(content);
    setFileName(name);
    setAnalyzeResult(null);
    setError(null);
  }

  function handleProviderChange(id: string) {
    setProvider(id);
    setModel(providers.find((p) => p.id === id)?.default_model ?? "");
  }

  async function handleAnalyze() {
    if (!logsPayload || !provider || !model) return;
    setAnalyzing(true);
    setError(null);
    try {
      const result = await api.analyze({
        provider,
        model,
        logs_payload: logsPayload,
        filename: fileName ?? "log.txt",
      });
      setAnalyzeResult(result);
      setUsage(await api.usage());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Errore durante l'analisi AI.");
    } finally {
      setAnalyzing(false);
    }
  }

  function handleDownload() {
    if (!analyzeResult) return;
    const blob = new Blob([buildMarkdownReport(analyzeResult.report)], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "ai_log_analysis_report.md";
    link.click();
    URL.revokeObjectURL(url);
  }

  const percentage =
    parseResult && parseResult.total_lines > 0
      ? (parseResult.filtered_count / parseResult.total_lines) * 100
      : 0;

  const quotaExhausted = usage !== null && usage.remaining === 0;

  return (
    <div className="space-y-8 pb-16">
      <div>
        <h1 className="text-2xl font-semibold text-text">Dashboard</h1>
        <p className="mt-1 text-sm text-text-muted">
          Carica un file di log, filtra le anomalie e genera un report AI strutturato.
        </p>
      </div>

      <UsageBadge usage={usage} />

      {error && (
        <p className="rounded-lg border border-red-400/30 bg-red-400/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <UploadCard fileName={fileName} onFileLoaded={handleFileLoaded} onError={setError} />

      {logContent && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <MetricCard label="Voci totali" value={parseResult?.total_lines ?? 0} />
            <MetricCard label="Voci filtrate" value={parseResult?.filtered_count ?? 0} accent="#ef4444" />
            <MetricCard label="Quota filtrata" value={`${percentage.toFixed(2)}%`} accent="#3b82f6" />
          </div>

          <div className="glass-card p-6">
            <h3 className="mb-4 text-base font-semibold text-text">Distribuzione severità</h3>
            <SeverityDonutChart severityCounts={parseResult?.severity_counts ?? {}} />
          </div>

          <SeverityFilters
            severities={severities}
            onSeveritiesChange={setSeverities}
            searchQuery={searchQuery}
            onSearchQueryChange={setSearchQuery}
            maxLines={maxLines}
            onMaxLinesChange={setMaxLines}
            maxLinesCap={Math.max(1, parseResult?.filtered_count ?? 1)}
            sliceFromEnd={sliceFromEnd}
            onSliceFromEndChange={setSliceFromEnd}
            dedupe={dedupe}
            onDedupeChange={setDedupe}
          />

          <div>
            {parsing && <p className="mb-2 text-xs text-text-muted">Aggiornamento anteprima…</p>}
            <TerminalPreview
              colorizedHtml={parseResult?.colorized_preview ?? ""}
              numLines={parseResult?.logs_to_send.length ?? 0}
            />
          </div>

          <div className="glass-card space-y-4 p-6">
            <h3 className="text-base font-semibold text-text">Analisi AI</h3>
            <ProviderModelSelect
              providers={providers}
              provider={provider}
              model={model}
              onProviderChange={handleProviderChange}
              onModelChange={setModel}
            />

            {estimating && <p className="text-xs text-text-muted">Calcolo stima costi…</p>}
            {estimate && <CostCard estimate={estimate} />}

            {quotaExhausted && (
              <p className="rounded-lg border border-orange-400/30 bg-orange-400/10 p-3 text-sm text-orange-300">
                Quota mensile esaurita. L'upgrade al piano Pro sarà disponibile a breve.
              </p>
            )}

            <button
              type="button"
              onClick={handleAnalyze}
              disabled={analyzing || !logsPayload || !provider || quotaExhausted}
              className="w-full rounded-lg bg-accent py-2.5 font-medium text-[#0a0e17] transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
            >
              {analyzing ? "Analisi in corso…" : "Genera report di analisi"}
            </button>
          </div>

          {analyzeResult && (
            <div className="space-y-4">
              <ReportCards report={analyzeResult.report} />
              <button
                type="button"
                onClick={handleDownload}
                className="rounded-lg border border-white/10 px-4 py-2 text-sm text-text transition hover:border-accent"
              >
                Scarica report in Markdown
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: string;
}) {
  return (
    <div className="glass-card p-5">
      <p className="text-xs text-text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold" style={{ color: accent ?? "#e2e8f0" }}>
        {value}
      </p>
    </div>
  );
}
