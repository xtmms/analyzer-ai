import json
import os
from datetime import datetime
from core.report_schema import LogAnalysisReport

def build_markdown_report(report: LogAnalysisReport) -> str:
    """Trasforma il LogAnalysisReport in una stringa Markdown pronta per il salvataggio."""
    
    md_content = f"# Log Analysis Report\n\n"
    md_content += f"*Data Generazione: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    sections = [
        ("1. Sintesi delle Problematiche", report.problem_summary),
        ("2. Analisi delle Cause", report.root_cause_analysis),
        ("3. Raccomandazioni", report.recommendations)
    ]
    
    for title, point in sections:
        md_content += f"## {title}\n"
        md_content += f"### {point.title}\n"
        md_content += f"{point.content}\n\n"
        
    return md_content

def save_report_to_output(report: LogAnalysisReport, original_filename: str) -> str:
    """Salva il report nella cartella output/ e ritorna il percorso del file creato."""
    if not os.path.exists("output"):
        os.makedirs("output")
        
    base_name = os.path.basename(original_filename)
    name_without_ext = os.path.splitext(base_name)[0]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    out_filename = f"output/analysis_{name_without_ext}_{timestamp}.md"
    
    md_content = build_markdown_report(report)
    
    with open(out_filename, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    return out_filename
