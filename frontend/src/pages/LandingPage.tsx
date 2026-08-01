import {
  BarChart3,
  Bot,
  CircleDollarSign,
  History,
  type LucideIcon,
  Puzzle,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";

const FEATURES: { icon: LucideIcon; title: string; text: string }[] = [
  {
    icon: Puzzle,
    title: "Parsing multiformato",
    text: "Rileva e raggruppa automaticamente stack trace multi-riga (Java, Python, ...) evitando la frammentazione del log.",
  },
  {
    icon: BarChart3,
    title: "Dashboard interattiva",
    text: "Ripartizione delle severità in tempo reale con grafico a ciambella e metriche riassuntive.",
  },
  {
    icon: Bot,
    title: "Multi-provider AI",
    text: "Scegli tra Google Gemini, OpenAI e Anthropic Claude in base a costo, qualità o preferenza — senza portare la tua chiave.",
  },
  {
    icon: CircleDollarSign,
    title: "Stima costi in tempo reale",
    text: "Conteggio token reale e stima del costo prima di ogni analisi, con suggerimento del modello più economico.",
  },
  {
    icon: SlidersHorizontal,
    title: "Filtri avanzati",
    text: "Filtro per severità, ricerca testuale/regex e selezione delle righe (prime/ultime N) per isolare il problema.",
  },
  {
    icon: History,
    title: "Storico analisi",
    text: "Ogni report generato resta salvato nel tuo account: ritrovalo in qualsiasi momento dalla pagina Storico.",
  },
];

const STEPS = [
  { title: "Carica il log", text: "Trascina un file .txt o .log dalla tua applicazione o infrastruttura." },
  { title: "Filtra le anomalie", text: "Seleziona severità, cerca pattern specifici e scegli quante righe inviare." },
  { title: "Scegli il provider AI", text: "Gemini, OpenAI o Claude: confronta costo stimato e scegli il modello." },
  { title: "Ricevi il report", text: "Sintesi del problema, root cause analysis e raccomandazioni operative, in 3 punti." },
];

export function LandingPage() {
  return (
    <div className="space-y-24 pb-20">
      <section className="mx-auto max-w-3xl pt-10 text-center">
        <p className="mx-auto mb-4 flex w-fit items-center gap-1.5 rounded-full border border-white/10 bg-accent-soft px-4 py-1 text-xs font-medium text-accent">
          <Sparkles className="h-3.5 w-3.5" strokeWidth={2} />
          Analisi log potenziata dall'AI
        </p>
        <h1 className="text-4xl font-semibold text-text sm:text-5xl">
          Trova la causa dei tuoi errori <span className="text-accent">in minuti, non in ore</span>
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-balance text-text-muted">
          Carica i log della tua applicazione o infrastruttura, filtra le anomalie e ottieni un report
          strutturato di Root Cause Analysis generato dall'AI — con Gemini, OpenAI o Claude a tua scelta.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Link
            to="/register"
            className="rounded-lg bg-accent px-6 py-2.5 font-medium text-[#0a0e17] transition hover:bg-accent-strong"
          >
            Inizia gratis
          </Link>
          <Link
            to="/login"
            className="rounded-lg border border-white/10 px-6 py-2.5 font-medium text-text transition hover:border-accent"
          >
            Accedi
          </Link>
        </div>
      </section>

      <section>
        <h2 className="mb-8 text-center text-2xl font-semibold text-text">Tutto quello che serve per il debug</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="glass-card p-6">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-accent-soft">
                <feature.icon className="h-5 w-5 text-accent" strokeWidth={1.75} />
              </div>
              <h3 className="mt-3 text-base font-semibold text-text">{feature.title}</h3>
              <p className="mt-2 text-sm text-text-muted">{feature.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-8 text-center text-2xl font-semibold text-text">Come funziona</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, idx) => (
            <div key={step.title} className="glass-card p-6">
              <span className="text-sm font-semibold text-accent">0{idx + 1}</span>
              <h3 className="mt-2 text-base font-semibold text-text">{step.title}</h3>
              <p className="mt-2 text-sm text-text-muted">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="glass-card mx-auto max-w-2xl p-10 text-center">
        <h2 className="text-2xl font-semibold text-text">Pronto a debuggare più velocemente?</h2>
        <p className="mt-2 text-text-muted">
          Piano gratuito incluso — nessuna carta di credito richiesta per iniziare.
        </p>
        <Link
          to="/register"
          className="mt-6 inline-block rounded-lg bg-accent px-6 py-2.5 font-medium text-[#0a0e17] transition hover:bg-accent-strong"
        >
          Crea il tuo account
        </Link>
      </section>
    </div>
  );
}
