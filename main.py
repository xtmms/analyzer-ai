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
from core.formatting import save_report_to_output, save_masked_log_to_output, build_markdown_report

console = Console()

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Log Analyzer CLI")
    parser.add_argument("--file", help="Percorso del file di log da analizzare")
    parser.add_argument("--provider", choices=list(AI_PROVIDERS.keys()), help="Provider AI da utilizzare")
    parser.add_argument("--model", help="Modello AI da utilizzare")
    parser.add_argument("--detail", choices=["Sintetico", "Dettagliato"], help="Livello di dettaglio del report")
    parser.add_argument("--hint", help="Contesto aggiuntivo per l'analisi")
    parser.add_argument("--print", action="store_true", help="Stampa il report Markdown in console")
    
    args = parser.parse_args()
    
    has_stdin = not sys.stdin.isatty()
    
    is_interactive = not has_stdin and not any([args.file, args.provider, args.model, args.detail, args.hint, args.print])

    hint = args.hint
    print_to_console = args.print

    if is_interactive:
        print_to_console = True  # Default in interactive mode
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
        
        hint = questionary.text("Fornisci un contesto aggiuntivo (opzionale, premi invio per saltare):").ask()
    elif has_stdin:
        file_path = None
        provider = args.provider or DEFAULT_PROVIDER
        model = args.model or AI_PROVIDERS[provider]["default_model"]
        detail = args.detail or "Dettagliato"
    else:
        file_path = args.file
        if not file_path or not os.path.exists(file_path):
            console.print("[bold red]Errore:[/bold red] File non valido o inesistente fornito via --file o stdin.")
            sys.exit(1)
            
        provider = args.provider or DEFAULT_PROVIDER
        model = args.model or AI_PROVIDERS[provider]["default_model"]
        detail = args.detail or "Dettagliato"

    api_key_env_var = f"{provider.upper()}_API_KEY"
    api_key = os.getenv(api_key_env_var)
    if not api_key:
        console.print(f"[bold red]Errore:[/bold red] Variabile d'ambiente {api_key_env_var} non impostata.")
        sys.exit(1)

    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    source_label = file_path if file_path else "Standard Input (stdin)"
    base_name = os.path.basename(file_path) if file_path else "stdin_log"
    name_without_ext = os.path.splitext(base_name)[0]
    run_folder = f"output/run_{timestamp}_{name_without_ext}"

    console.print(f"\n[bold green]Avvio analisi per:[/bold green] {source_label}")
    console.print(f"Provider: {provider} | Modello: {model} | Dettaglio: {detail}")
    if hint:
        console.print(f"Contesto: [italic]{hint}[/italic]")
    console.print()

    with console.status("[bold cyan]Lettura e parsing del file di log...[/bold cyan]"):
        try:
            if has_stdin:
                log_content = sys.stdin.read()
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    log_content = f.read()
        except Exception as e:
            console.print(f"[bold red]Errore lettura:[/bold red] {e}")
            sys.exit(1)

        entries = parse_log_to_entries(log_content)
        logs_to_send = prepare_entries_for_send(entries, dedupe=True)
        payload = "\n".join(logs_to_send)
        
        # Salvataggio del log mascherato per audit
        masked_log_path = save_masked_log_to_output(payload, run_folder)

    with console.status(f"[bold cyan]Analisi in corso con {model}...[/bold cyan]"):
        ai_client = build_provider(provider, api_key)
        try:
            report, usage = ai_client.analyze(model=model, logs_payload=payload, temperature=0.0, detail_level=detail, hint=hint)
        except Exception as e:
            console.print(f"[bold red]Errore durante la chiamata API:[/bold red] {e}")
            sys.exit(1)

    with console.status("[bold cyan]Salvataggio del report...[/bold cyan]"):
        output_file = save_report_to_output(report, run_folder)

    if print_to_console:
        console.print("\n[bold magenta]--- Inizio Report ---[/bold magenta]\n")
        console.print(Markdown(build_markdown_report(report)))
        console.print("\n[bold magenta]--- Fine Report ---[/bold magenta]\n")

    cost_data = calculate_cost(provider, model, usage.get("input_tokens", 0), usage.get("output_tokens", 0))

    console.print(Panel.fit(
        f"[bold green]Analisi completata con successo![/bold green]\n"
        f"Report salvato in: [bold yellow]{output_file}[/bold yellow]\n"
        f"Log mascherato per audit salvato in: [bold yellow]{masked_log_path}[/bold yellow]\n\n"
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
