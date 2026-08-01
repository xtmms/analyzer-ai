import { CircleDollarSign, TriangleAlert } from "lucide-react";

import type { EstimateOut } from "../lib/types";

export function CostCard({ estimate }: { estimate: EstimateOut }) {
  const { token_count, is_real_token_count, cost_breakdown, suggestion } = estimate;

  return (
    <div className="glass-card space-y-4 p-6">
      <div className="flex items-center gap-2 text-sm font-semibold text-[#10b981]">
        <CircleDollarSign className="h-4 w-4" strokeWidth={2} /> Stima dei costi (API)
      </div>
      <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        <Stat
          label={is_real_token_count ? "Token input (reale)" : "Token input (stima)"}
          value={token_count.toLocaleString()}
        />
        <Stat label="Costo input" value={`$${cost_breakdown.input_cost.toFixed(6)}`} accent />
        <Stat label="Token output stimati" value={`~${cost_breakdown.output_tokens_est}`} />
        <Stat label="Costo output" value={`$${cost_breakdown.output_cost.toFixed(6)}`} accent />
      </div>
      <div className="flex items-center justify-between border-t border-white/10 pt-3">
        <span className="text-sm text-text-muted">Costo totale stimato</span>
        <span className="text-lg font-semibold text-text">${cost_breakdown.total_cost.toFixed(6)}</span>
      </div>
      {suggestion && (
        <div className="flex items-start gap-2 rounded-lg border border-orange-400/30 bg-orange-400/10 p-3 text-sm text-orange-300">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2} />
          <span>
            Con questo volume di log, <strong>{suggestion.model}</strong> costerebbe circa il{" "}
            {suggestion.savings_pct.toFixed(0)}% in meno (${suggestion.total_cost.toFixed(5)} totali) pur
            mantenendo ottime performance.
          </span>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <p className="text-xs text-text-muted">{label}</p>
      <p className={`font-medium ${accent ? "text-[#10b981]" : "text-text"}`}>{value}</p>
    </div>
  );
}
