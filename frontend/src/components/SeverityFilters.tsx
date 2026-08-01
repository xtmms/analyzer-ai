import { SEVERITY_COLORS, SEVERITY_LEVELS } from "../lib/types";

interface SeverityFiltersProps {
  severities: string[];
  onSeveritiesChange: (values: string[]) => void;
  searchQuery: string;
  onSearchQueryChange: (value: string) => void;
  maxLines: number;
  onMaxLinesChange: (value: number) => void;
  maxLinesCap: number;
  sliceFromEnd: boolean;
  onSliceFromEndChange: (value: boolean) => void;
  dedupe: boolean;
  onDedupeChange: (value: boolean) => void;
}

export function SeverityFilters({
  severities,
  onSeveritiesChange,
  searchQuery,
  onSearchQueryChange,
  maxLines,
  onMaxLinesChange,
  maxLinesCap,
  sliceFromEnd,
  onSliceFromEndChange,
  dedupe,
  onDedupeChange,
}: SeverityFiltersProps) {
  function toggleSeverity(level: string) {
    if (severities.includes(level)) {
      onSeveritiesChange(severities.filter((s) => s !== level));
    } else {
      onSeveritiesChange([...severities, level]);
    }
  }

  return (
    <div className="glass-card space-y-5 p-6">
      <div>
        <p className="mb-2 text-sm font-medium text-text-muted">Livelli di severità</p>
        <div className="flex flex-wrap gap-2">
          {SEVERITY_LEVELS.map((level) => {
            const color = SEVERITY_COLORS[level];
            const active = severities.includes(level);
            return (
              <button
                key={level}
                type="button"
                onClick={() => toggleSeverity(level)}
                style={
                  active
                    ? { borderColor: color, backgroundColor: `${color}26`, color }
                    : { borderColor: "#ffffff1a" }
                }
                className="flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium text-text-muted transition hover:border-white/20"
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: color, opacity: active ? 1 : 0.5 }}
                />
                {level}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-muted" htmlFor="search-query">
          Ricerca testo / regex
        </label>
        <input
          id="search-query"
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchQueryChange(e.target.value)}
          placeholder="es. timeout|connection refused"
          className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-text outline-none focus:border-accent"
        />
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-muted" htmlFor="max-lines">
          Numero massimo di righe da inviare: <span className="text-text">{maxLines}</span>
        </label>
        <input
          id="max-lines"
          type="range"
          min={1}
          max={Math.max(1, maxLinesCap)}
          value={Math.min(maxLines, Math.max(1, maxLinesCap))}
          onChange={(e) => onMaxLinesChange(Number(e.target.value))}
          className="w-full accent-[#a78bfa]"
        />
      </div>

      <div className="flex flex-wrap items-center gap-6">
        <div className="flex items-center gap-4 text-sm">
          <label className="flex items-center gap-1.5 text-text-muted">
            <input type="radio" checked={sliceFromEnd} onChange={() => onSliceFromEndChange(true)} />
            Ultime righe (consigliato)
          </label>
          <label className="flex items-center gap-1.5 text-text-muted">
            <input type="radio" checked={!sliceFromEnd} onChange={() => onSliceFromEndChange(false)} />
            Prime righe
          </label>
        </div>
        <label className="flex items-center gap-1.5 text-sm text-text-muted">
          <input type="checkbox" checked={dedupe} onChange={(e) => onDedupeChange(e.target.checked)} />
          Comprimi righe duplicate consecutive
        </label>
      </div>
    </div>
  );
}
