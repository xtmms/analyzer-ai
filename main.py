import argparse
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

import questionary
from config import AI_PROVIDERS, DEFAULT_PROVIDER
from core.log_parser import parse_log_to_entries, prepare_entries_for_send
from core.ai_providers.registry import build_provider, calculate_cost
from core.formatting import save_report_to_output

console = Console()

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Log Analyzer CLI")
    parser.add_argument("--file", help="Percorso del file di log da analizzare")
    parser.add_argument("--provider", choices=list(AI_PROVIDERS.keys()), help="Provider AI da utilizzare")
    parser.add_argument("--model", help="Modello AI da utilizzare")
    parser.add_argument("--detail", choices=["Sintetico", "Dettagliato"], help="Livello di dettaglio del report")
    
    args = parser.parse_args()
    
    is_interactive = not any([args.file, args.provider, args.model, args.detail])

    if is_interactive:
        console.print(Panel.fit("[bold blue]Log Analyzer AI CLI[/bold blue]", subtitle="Interactive Mode"))
        console.print()
        
        file_path = questionary.path("Seleziona il file di log da analizzare:").ask()
        if not file_path or not os.path.exists(file_path):
            console.print("[bold red]Errore:[/bold red] File non valido o inesistente.")
            sys.exit(1)
            
        provider = questionary.select(
            "Seleziona il provider AI:",
            choices=list(AI_PROVIDERS.keys()),
            default=DEFAULT_PROVIDER
        ).ask()
        
        models = AI_PROVIDERS[provider]["models"]
        default_model = AI_PROVIDERS[provider]["default_model"]
        
        model = questionary.select(
            "Seleziona il modello:",
            choices=models,
            default=default_model
        ).ask()
        
        detail = questionary.select(
            "Seleziona il livello di dettaglio del report:",
            choices=["Sintetico", "Dettagliato"],
            default="Dettagliato"
        ).ask()
    else:
        file_path = args.file
        if not file_path or not os.path.exists(file_path):
            console.print("[bold red]Errore:[/bold red] File non valido o inesistente fornito via --file.")
            sys.exit(1)
            
        provider = args.provider or DEFAULT_PROVIDER
        model = args.model or AI_PROVIDERS[provider]["default_model"]
        detail = args.detail or "Dettagliato"

    api_key_env_var = f"{provider.upper()}_API_KEY"
    api_key = os.getenv(api_key_env_var)
    if not api_key:
        console.print(f"[bold red]Errore:[/bold red] Variabile d'ambiente {api_key_env_var} non impostata.")
        sys.exit(1)

    console.print(f"\n[bold green]Avvio analisi per file:[/bold green] {file_path}")
    console.print(f"Provider: {provider} | Modello: {model} | Dettaglio: {detail}\n")

    with console.status("[bold cyan]Lettura e parsing del file di log...[/bold cyan]"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                log_content = f.read()
        except Exception as e:
            console.print(f"[bold red]Errore lettura file:[/bold red] {e}")
            sys.exit(1)

        entries = parse_log_to_entries(log_content)
        logs_to_send = prepare_entries_for_send(entries, dedupe=True)
        payload = "\n".join(logs_to_send)

    with console.status(f"[bold cyan]Analisi in corso con {model}...[/bold cyan]"):
        ai_client = build_provider(provider, api_key)
        try:
            # Temperature è forzata a "preciso" (es. 0.0) come richiesto
            report, usage = ai_client.analyze(model=model, logs_payload=payload, temperature=0.0, detail_level=detail)
        except Exception as e:
            console.print(f"[bold red]Errore durante la chiamata API:[/bold red] {e}")
            sys.exit(1)

    with console.status("[bold cyan]Salvataggio del report...[/bold cyan]"):
        output_file = save_report_to_output(report, file_path)

    cost_data = calculate_cost(provider, model, usage.get("input_tokens", 0), usage.get("output_tokens", 0))

    console.print(Panel.fit(
        f"[bold green]Analisi completata con successo![/bold green]\n"
        f"Report salvato in: [bold yellow]{output_file}[/bold yellow]\n\n"
        f"📊 [bold]Statistiche Token[/bold]\n"
        f"Input Tokens:  {usage.get('input_tokens', 0)}\n"
        f"Output Tokens: {usage.get('output_tokens', 0)}\n"
        f"Total Tokens:  {usage.get('total_tokens', 0)}\n\n"
        f"💰 [bold]Costo Stimato[/bold]\n"
        f"Costo: ${cost_data['total_cost']:.6f}",
        title="Risultato"
    ))

if __name__ == "__main__":
    main()
