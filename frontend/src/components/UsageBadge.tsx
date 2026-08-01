import { TriangleAlert } from "lucide-react";

import type { UsageOut } from "../lib/types";

export function UsageBadge({ usage }: { usage: UsageOut | null }) {
  if (!usage) return null;
  const pct = usage.limit > 0 ? Math.min(100, (usage.used / usage.limit) * 100) : 0;

  return (
    <div className="glass-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
        <span className="text-text-muted">
          Piano <strong className="text-accent">{usage.plan}</strong> — {usage.period}
        </span>
        <span className="text-text">
          {usage.used}/{usage.limit} analisi usate
        </span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${pct}%` }} />
      </div>
      {usage.remaining === 0 && (
        <p className="mt-2 flex items-center gap-1.5 text-xs text-orange-300">
          <TriangleAlert className="h-3.5 w-3.5 shrink-0" strokeWidth={2} />
          Quota mensile esaurita. L'upgrade al piano Pro sarà disponibile a breve.
        </p>
      )}
    </div>
  );
}
