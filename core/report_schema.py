"""
Schema condiviso del report di analisi log.

Ogni provider in core/ai_providers/ deve produrre un LogAnalysisReport,
indipendentemente dall'SDK/API sottostante. Isolato in un modulo a parte
(prima viveva in gemini_client.py) perché ora è condiviso da più provider
e da core/formatting.build_markdown_report.
"""
from pydantic import BaseModel, Field


class ReportPoint(BaseModel):
    title: str = Field(description="Titolo sintetico del punto del report in italiano")
    content: str = Field(
        description=(
            "Contenuto descrittivo in formato Markdown (può contenere elenchi, tabelle "
            "o frammenti di codice). Non includere il titolo all'interno del contenuto."
        )
    )


class LogAnalysisReport(BaseModel):
    problem_summary: ReportPoint = Field(description="Punto 1: Sintesi delle Problematiche")
    root_cause_analysis: ReportPoint = Field(description="Punto 2: Analisi delle Cause Principali")
    recommendations: ReportPoint = Field(description="Punto 3: Raccomandazioni e Soluzioni")


SYSTEM_INSTRUCTION = (
    "Sei un esperto software engineer, DevOps ed SRE senior. Ti verranno forniti i log estratti da un sistema o un'applicazione.\n"
    "Analizza i log e produci un report strutturato compilando lo schema JSON richiesto.\n"
    "Usa l'italiano per la risposta. Mantieni uno stile formale, chiaro e orientato alla risoluzione del problema.\n"
    "Nei campi richiesti:\n"
    "- problem_summary: Riassumi i problemi riscontrati (eventi anomali rilevati, frequenza ed impatto complessivo).\n"
    "- root_cause_analysis: Spiega la causa tecnica dettagliata (Root Cause Analysis) basandoti sulle stack trace, codici di errore e messaggi dei log.\n"
    "- recommendations: Suggerisci raccomandazioni pratiche ed operative di risoluzione (bug fix per i dev, modifiche infrastrutturali o configurazioni)."
)


def build_user_prompt(logs_payload: str) -> str:
    return (
        "Ecco le righe di log di errore da analizzare:\n\n"
        f"```log\n{logs_payload}\n```\n\n"
        "Genera il report strutturato in base a queste informazioni."
    )


# JSON Schema equivalente a LogAnalysisReport, usato dai provider (OpenAI,
# Anthropic) la cui API di structured output/tool-use richiede uno schema
# JSON esplicito invece di un modello Pydantic nativo come fa google-genai.
LOG_ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "problem_summary": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
            "required": ["title", "content"],
            "additionalProperties": False,
        },
        "root_cause_analysis": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
            "required": ["title", "content"],
            "additionalProperties": False,
        },
        "recommendations": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
            "required": ["title", "content"],
            "additionalProperties": False,
        },
    },
    "required": ["problem_summary", "root_cause_analysis", "recommendations"],
    "additionalProperties": False,
}
