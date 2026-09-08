"""
Schema condiviso del report di analisi log e prompt generation.
"""
from pydantic import BaseModel, Field

class ReportPoint(BaseModel):
    title: str = Field(description="Titolo sintetico del punto del report in italiano")
    content: str = Field(
        description=(
            "Contenuto descrittivo in formato Markdown. "
            "Non includere il titolo all'interno del contenuto."
        )
    )

class TestAutomationReport(BaseModel):
    failing_tests_summary: ReportPoint = Field(description="Elenco dei test falliti e descrizione dell'assertion che non è passata.")
    root_cause_analysis: ReportPoint = Field(description="Perché il test è fallito? (Es. Bug nel codice, selettore UI cambiato, timeout di rete).")
    flakiness_assessment: ReportPoint = Field(description="Valuta se questo fallimento sembra un test instabile/flaky legato a timing/concorrenza, o un problema deterministico.")
    fix_recommendations: ReportPoint = Field(description="Suggerimenti pratici su come fixare il test o il codice sottostante.")

def get_system_instruction(detail_level: str = "Dettagliato") -> str:
    base = (
        "Sei un esperto SDET e QA Automation Engineer senior. "
        "Analizza i fallimenti della test suite (log, XML o JSON) e produci un report strutturato compilando lo schema JSON richiesto in italiano.\n"
    )
    if detail_level.lower() == "sintetico":
        base += (
            "Sii estremamente conciso. Vai dritto al punto indicando il test, perché è fallito e come fixarlo. "
            "Usa bullet point e comandi/esempi di codice diretti."
        )
    else:
        base += (
            "Fornisci un'analisi dettagliata. Spiega la dinamica del fallimento del test, l'eventuale "
            "instabilità (flakiness) e proponi una soluzione robusta a livello di codice."
        )
    return base

def build_user_prompt(logs_payload: str, hint: str = None) -> str:
    prompt = (
        "Ecco i dettagli dei test falliti da analizzare:\n\n"
        f"```log\n{logs_payload}\n```\n\n"
    )
    if hint:
        prompt += f"L'operatore QA fornisce questo contesto aggiuntivo per aiutarti nell'analisi:\n{hint}\n\n"
        
    prompt += "Genera il report strutturato in base a queste informazioni."
    return prompt

