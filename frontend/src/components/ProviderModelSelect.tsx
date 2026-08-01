import type { ProviderOut } from "../lib/types";

interface ProviderModelSelectProps {
  providers: ProviderOut[];
  provider: string;
  model: string;
  onProviderChange: (id: string) => void;
  onModelChange: (model: string) => void;
}

export function ProviderModelSelect({
  providers,
  provider,
  model,
  onProviderChange,
  onModelChange,
}: ProviderModelSelectProps) {
  const current = providers.find((p) => p.id === provider);

  if (providers.length === 0) {
    return (
      <div className="glass-card border-orange-400/30 p-4 text-sm text-orange-300">
        Nessun provider AI configurato lato server. Imposta almeno una chiave (GEMINI_API_KEY,
        OPENAI_API_KEY o ANTHROPIC_API_KEY) nel backend.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <label className="mb-2 block text-sm font-medium text-text-muted" htmlFor="provider-select">
          Provider AI
        </label>
        <select
          id="provider-select"
          value={provider}
          onChange={(e) => onProviderChange(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          {providers.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="mb-2 block text-sm font-medium text-text-muted" htmlFor="model-select">
          Modello
        </label>
        <select
          id="model-select"
          value={model}
          onChange={(e) => onModelChange(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          {current?.models.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
