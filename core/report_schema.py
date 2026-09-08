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

class LogAnalysisReport(BaseModel):
    problem_summary: ReportPoint = Field(description="Punto 1: Sintesi delle Problematiche")
    root_cause_analysis: ReportPoint = Field(description="Punto 2: Analisi delle Cause Principali")
    recommendations: ReportPoint = Field(description="Punto 3: Raccomandazioni e Soluzioni")

def get_system_instruction(detail_level: str = "Dettagliato") -> str:
    base = (
        "Sei un esperto software engineer, DevOps ed SRE senior. "
        "Analizza i log e produci un report strutturato compilando lo schema JSON richiesto in italiano.\n"
    )
    if detail_level.lower() == "sintetico":
        base += (
            "Sii estremamente conciso. Vai dritto al punto con bullet point brevi e diretti. "
            "Evita spiegazioni discorsive inutili, fornisci solo i fatti e i comandi/fix esatti."
        )
    else:
        base += (
            "Fornisci un'analisi estremamente dettagliata e discorsiva. Spiega a fondo "
            "le possibili cause, esplora scenari alternativi e proponi soluzioni architetturali complete."
        )
    return base

def build_user_prompt(logs_payload: str) -> str:
    return (
        "Ecco le righe di log di errore da analizzare:\n\n"
        f"```log\n{logs_payload}\n```\n\n"
        "Genera il report strutturato in base a queste informazioni."
    )
