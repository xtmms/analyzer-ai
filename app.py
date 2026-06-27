import streamlit as st
import re
import os
import json
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Carica le variabili d'ambiente da un file .env se presente
load_dotenv()

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="AI Log Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile CSS custom per un'estetica premium ed elegante (Dark Mode oriented)
st.markdown("""
<style>
    /* Importazione Font Moderni */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Configurazione Layout & Sfondi Globali */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        color: #e2e8f0;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #08090d !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(127, 90, 240, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(167, 139, 250, 0.05) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(14, 165, 233, 0.03) 0px, transparent 50%) !important;
        background-attachment: fixed !important;
    }
    
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0d0f16 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    
    /* Scrollbar Personalizzata */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.01);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(127, 90, 240, 0.4);
    }
    
    /* Titolo Principale della Dashboard */
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #a78bfa 0%, #c084fc 50%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        font-weight: 400;
        line-height: 1.5;
    }
    
    /* Stile dei Pulsanti Streamlit */
    div.stButton > button {
        background: linear-gradient(135deg, #6d28d9 0%, #4c1d95 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 0.6rem 2.5rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(109, 40, 217, 0.25) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(109, 40, 217, 0.45) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    div.stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Stile per i Download Button ed altri bottoni secondari */
    div[data-testid="stDownloadButton"] > button {
        background: rgba(255, 255, 255, 0.03) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: none !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background: rgba(255, 255, 255, 0.07) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* Custom Cards Metriche con Glassmorphism */
    .metric-card {
        background: rgba(18, 20, 29, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 14px;
        padding: 1.25rem 1rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(16px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(167, 139, 250, 0.3);
        box-shadow: 0 12px 40px rgba(167, 139, 250, 0.08);
        background: rgba(18, 20, 29, 0.7);
    }
    .metric-val {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 8px;
        font-weight: 600;
    }
    
    /* File Uploader Streamlit */
    div[data-testid="stFileUploader"] {
        background-color: rgba(18, 20, 29, 0.4) !important;
        border: 1px dashed rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: rgba(167, 139, 250, 0.4) !important;
        background-color: rgba(18, 20, 29, 0.5) !important;
    }
    
    /* Selettori ed Input Streamlit */
    div[data-baseweb="select"] > div, input[type="text"] {
        background-color: #12141d !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        transition: all 0.2s ease !important;
    }
    div[data-baseweb="select"] > div:hover, input[type="text"]:focus {
        border-color: rgba(167, 139, 250, 0.4) !important;
    }
    
    /* Expanders Streamlit */
    div[data-testid="stExpander"] {
        background-color: rgba(18, 20, 29, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
        overflow: hidden !important;
        margin-bottom: 1.5rem !important;
    }
    summary[class*="streamlit-expanderHeader"] {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        color: #f1f5f9 !important;
        background-color: rgba(18, 20, 29, 0.5) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03) !important;
        padding: 1rem !important;
        transition: all 0.2s ease !important;
    }
    summary[class*="streamlit-expanderHeader"]:hover {
        background-color: rgba(18, 20, 29, 0.75) !important;
        color: #ffffff !important;
    }
    
    /* Stile della visualizzazione Log Anteprima */
    .log-preview {
        background-color: #0b0d13;
        color: #f8fafc;
        padding: 1.25rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        height: 300px;
        overflow-y: auto;
        overflow-x: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        white-space: pre;
        line-height: 1.5;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.5);
    }
    
    /* Cards per il Report di Gemini (Punti 1, 2, 3) */
    .report-card {
        background: rgba(18, 20, 29, 0.5);
        border-left: 4px solid #7f5af0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-left-width: 5px;
    }
    .report-card-1 { border-left-color: #c084fc; }
    .report-card-2 { border-left-color: #fb923c; }
    .report-card-3 { border-left-color: #4ade80; }
    
    .report-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #ffffff;
        letter-spacing: -0.2px;
    }
    
    .report-content {
        font-size: 0.95rem;
        color: #cbd5e1;
        line-height: 1.6;
        margin-top: 0.75rem;
    }
    
    .report-p {
        margin-bottom: 1rem;
    }
    
    .report-list {
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        padding-left: 1.25rem;
        list-style-type: disc;
    }
    
    .report-list li {
        margin-bottom: 0.4rem;
    }
    
    .inline-code {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #f1f5f9 !important;
        padding: 0.15rem 0.4rem !important;
        border-radius: 4px !important;
        font-size: 0.85em !important;
    }
    
    .code-block-preview {
        background-color: #0b0d13 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        overflow-x: auto !important;
        margin: 1rem 0 !important;
    }
    
    .code-block-preview code {
        font-family: 'JetBrains Mono', monospace !important;
        color: #f8fafc !important;
        font-size: 0.85rem !important;
    }
    
    /* Card della Stima Costi */
    .cost-card {
        background: rgba(18, 20, 29, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(16px);
    }
    .cost-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        color: #ffffff;
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .cost-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        font-size: 0.85rem;
        margin-top: 12px;
    }
    .cost-item {
        background: rgba(255, 255, 255, 0.02);
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.03);
    }
    .cost-label {
        color: #94a3b8;
        display: block;
        margin-bottom: 4px;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .cost-val {
        color: #ffffff;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .cost-total-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    .cost-total-label {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        color: #ffffff;
        font-size: 1rem;
    }
    .cost-total-val {
        color: #4ade80;
        font-weight: 700;
        font-size: 1.3rem;
        font-family: 'Space Grotesk', sans-serif;
    }
    .cost-suggestion {
        font-size: 0.8rem;
        color: #fb923c;
        margin-top: 12px;
        background: rgba(251, 146, 60, 0.08);
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid rgba(251, 146, 60, 0.15);
    }
    
    /* Livelli di conteggio righe (Badge) */
    .badge-row-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 15px;
    }
    .badge-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: rgba(18, 20, 29, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 10px;
        padding: 8px 16px;
        transition: all 0.2s ease;
    }
    .badge-row:hover {
        background-color: rgba(18, 20, 29, 0.8);
        border-color: rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)


# Pydantic schema per Structured Outputs di Gemini
class ReportPoint(BaseModel):
    title: str = Field(description="Titolo sintetico del punto del report in italiano")
    content: str = Field(description="Contenuto descrittivo in formato Markdown (può contenere elenchi, tabelle o frammenti di codice). Non includere il titolo all'interno del contenuto.")

class LogAnalysisReport(BaseModel):
    problem_summary: ReportPoint = Field(description="Punto 1: Sintesi delle Problematiche")
    root_cause_analysis: ReportPoint = Field(description="Punto 2: Analisi delle Cause Principali")
    recommendations: ReportPoint = Field(description="Punto 3: Raccomandazioni e Soluzioni")


# Funzione di parsing dei log con categorizzazione delle severità
def parse_log_to_entries(log_content: str) -> list:
    """
    Parsa l'intero log riga per riga, raggruppando le stack trace Traceback in elementi logici multi-riga.
    Rileva il livello di severità di ciascun elemento.
    """
    lines = log_content.splitlines()
    entries = []
    
    severity_patterns = {
        "CRITICAL": re.compile(r'\b(CRITICAL|FATAL|SEVERE)\b', re.IGNORECASE),
        "ERROR": re.compile(r'\b(ERROR|EXCEPTION|FAIL|FAILED)\b', re.IGNORECASE),
        "WARNING": re.compile(r'\b(WARNING|WARN)\b', re.IGNORECASE),
        "INFO": re.compile(r'\b(INFO)\b', re.IGNORECASE),
        "DEBUG": re.compile(r'\b(DEBUG)\b', re.IGNORECASE)
    }
    
    def detect_severity(text: str) -> str:
        if "traceback (most recent call last)" in text.lower() or "traceback (" in text:
            return "ERROR"
        for level, pattern in severity_patterns.items():
            if pattern.search(text):
                return level
        return "INFO"
        
    in_traceback = False
    traceback_buffer = []
    
    for line in lines:
        is_traceback_start = (
            "traceback (most recent call last)" in line.lower() or 
            line.strip().startswith("Traceback (") or
            (line.strip().startswith("at ") and len(entries) > 0 and entries[-1]["severity"] == "ERROR")
        )
        
        if is_traceback_start:
            in_traceback = True
            traceback_buffer = [line]
            continue
            
        if in_traceback:
            if line.startswith(" ") or line.startswith("\t") or not line.strip():
                traceback_buffer.append(line)
            else:
                traceback_buffer.append(line)
                text = "\n".join(traceback_buffer)
                entries.append({
                    "text": text,
                    "severity": detect_severity(text),
                    "is_traceback": True
                })
                in_traceback = False
                traceback_buffer = []
            continue
            
        if line.strip():
            entries.append({
                "text": line,
                "severity": detect_severity(line),
                "is_traceback": False
            })
            
    if in_traceback and traceback_buffer:
        text = "\n".join(traceback_buffer)
        entries.append({
            "text": text,
            "severity": detect_severity(text),
            "is_traceback": True
        })
        
    return entries


# Funzione di filtraggio delle entries
def filter_entries(entries: list, selected_severities: list, search_query: str) -> list:
    filtered = []
    search_pattern = None
    if search_query.strip():
        try:
            search_pattern = re.compile(search_query, re.IGNORECASE)
        except re.error:
            search_pattern = None
            
    for entry in entries:
        # Filtra per severità
        if entry["severity"] not in selected_severities:
            continue
            
        # Filtra per query testuale o regex
        if search_query.strip():
            if search_pattern:
                if not search_pattern.search(entry["text"]):
                    continue
            else:
                if search_query.lower() not in entry["text"].lower():
                    continue
                    
        filtered.append(entry)
        
    return filtered


def colorize_log(text: str) -> str:
    """
    Colora sintatticamente il log in HTML per evidenziare date, loggers e livelli di severità.
    """
    import html
    escaped = html.escape(text)
    
    # 1. Parentesi quadre (logger/classi) es: [UserController]
    bracket_pattern = re.compile(r'\[([a-zA-Z0-9_]+)\]')
    escaped = bracket_pattern.sub(r'<span style="color: #a78bfa; font-weight: 600;">[\1]</span>', escaped)
    
    # 2. Date e timestamp es: 2026-06-25 16:02:22
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)')
    escaped = timestamp_pattern.sub(r'<span style="color: #64748b;">\1</span>', escaped)
    
    # 3. Livelli di severità e parole chiave (cromaticamente allineati alla nuova palette)
    colors = {
        "CRITICAL": "#ff5555",
        "FATAL": "#ff5555",
        "SEVERE": "#ff5555",
        "ERROR": "#ff6e6e",
        "FAIL": "#ff6e6e",
        "FAILED": "#ff6e6e",
        "EXCEPTION": "#ff6e6e",
        "WARNING": "#ffb86c",
        "WARN": "#ffb86c",
        "INFO": "#50fa7b",
        "DEBUG": "#8be9fd"
    }
    
    for keyword, col in colors.items():
        pattern = re.compile(rf'\b({re.escape(keyword)})\b', re.IGNORECASE)
        escaped = pattern.sub(f'<span style="color: {col}; font-weight: bold;">\\1</span>', escaped)
        
    # 4. Righe chiave Traceback
    traceback_pattern = re.compile(r'\b(Traceback \(most recent call last\):|File &quot;[^&]+&quot;, line \d+)\b')
    escaped = traceback_pattern.sub(r'<span style="color: #ffb86c; font-style: italic;">\1</span>', escaped)
    
    return escaped


def markdown_to_html(md_text: str) -> str:
    """
    Semplice parser Markdown-to-HTML per formattare il contenuto dei report di Gemini
    all'interno delle card personalizzate.
    """
    import html
    escaped = html.escape(md_text)
    
    # 1. Blocchi di codice: ```python ... ``` -> <pre class="code-block-preview"><code class="language-python">...</code></pre>
    code_block_pattern = re.compile(r'```([a-zA-Z0-9_-]*)\n(.*?)```', re.DOTALL)
    def replace_code_block(match):
        lang = match.group(1)
        code = match.group(2)
        return f'<pre class="code-block-preview"><code class="language-{lang}">{code}</code></pre>'
    escaped = code_block_pattern.sub(replace_code_block, escaped)
    
    # 2. Codice inline: `code` -> <code class="inline-code">code</code>
    escaped = re.sub(r'`([^`\n]+)`', r'<code class="inline-code">\1</code>', escaped)
    
    # 3. Grassetto: **testo** -> <strong>testo</strong>
    escaped = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escaped)
    
    # 4. Liste puntate: raggruppa righe con - o * in <ul><li>
    lines = escaped.split('\n')
    in_list = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('+ '):
            item_content = stripped[2:]
            if not in_list:
                new_lines.append('<ul class="report-list">')
                in_list = True
            new_lines.append(f'<li>{item_content}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('</ul>')
    
    escaped = '\n'.join(new_lines)
    
    # 5. Paragrafi ed a capo
    paragraphs = escaped.split('\n\n')
    formatted_paragraphs = []
    for p in paragraphs:
        p_stripped = p.strip()
        if not p_stripped:
            continue
        # Se è un tag blocco già strutturato, non racchiuderlo in <p>
        if p_stripped.startswith('<ul') or p_stripped.startswith('<pre') or p_stripped.startswith('</ul') or p_stripped.startswith('</pre'):
            formatted_paragraphs.append(p_stripped)
        else:
            p_formatted = p_stripped.replace('\n', '<br>')
            formatted_paragraphs.append(f'<p class="report-p">{p_formatted}</p>')
            
    return '\n'.join(formatted_paragraphs)


# SIDEBAR - Configurazione dell'Analisi
st.sidebar.markdown("### ⚙️ Impostazioni Analisi")

# API Key dall'ambiente
gemini_key = os.environ.get("GEMINI_API_KEY", "")
if not gemini_key:
    st.sidebar.error("❌ Chiave API mancante. Configura `GEMINI_API_KEY` nel file `.env` o tra le variabili d'ambiente per procedere.")
else:
    st.sidebar.success("🔑 Chiave API caricata.")

# Selezione Modello
model_option = st.sidebar.selectbox(
    "Modello Gemini",
    options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
    index=0,
    help="Scegli gemini-2.5-flash per risposte veloci. Scegli gemini-2.5-pro per log estremamente complessi."
)

# Parametri Generazione
temperature = 0.2

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtri Log")

severity_options = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
selected_severities = st.sidebar.multiselect(
    "Livelli di Severità da includere",
    options=severity_options,
    default=["CRITICAL", "ERROR", "WARNING"],
    help="Filtra i log includendo solo le severità selezionate."
)

search_query = st.sidebar.text_input(
    "Ricerca testo / regex",
    value="",
    help="Filtra i log contenenti questo testo o pattern regex."
)


# MAIN CONTENT
st.markdown('<h1 class="main-title">🔍 AI Log Analyzer</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Analizza i file di log di qualsiasi sistema o applicazione, filtra le anomalie e ottieni un report strutturato da Gemini AI.</p>', unsafe_allow_html=True)

# Upload del file
uploaded_file = st.file_uploader(
    "Carica un file di log (.txt, .log)", 
    type=["txt", "log"],
    help="Trascina e rilascia il file di log qui per iniziare il filtraggio."
)

if uploaded_file is not None:
    # Evita re-run spuri in caso di file identico
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_uploaded_key") != file_key:
        st.session_state["last_uploaded_key"] = file_key
        st.session_state["parsed_entries"] = None
        st.session_state["report"] = None
        st.session_state["token_count"] = None
        st.session_state["last_payload_hash"] = None
        
    # Caricamento ed elaborazione del file se non memorizzato nello stato della sessione
    if st.session_state.get("parsed_entries") is None:
        bytes_data = uploaded_file.getvalue()
        try:
            log_content = bytes_data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                log_content = bytes_data.decode("latin1")
            except Exception as e:
                st.error(f"Errore nella lettura del file: {e}")
                log_content = None
                
        if log_content:
            st.session_state["parsed_entries"] = parse_log_to_entries(log_content)
            
    parsed_entries = st.session_state.get("parsed_entries")
    
    if parsed_entries:
        total_lines = len(parsed_entries)
        
        # Calcolo conteggi severità per la dashboard statistica
        severity_counts = {"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0}
        for entry in parsed_entries:
            sev = entry["severity"]
            if sev in severity_counts:
                severity_counts[sev] += 1
                
        # Applica i filtri impostati dall'utente
        filtered = filter_entries(parsed_entries, selected_severities, search_query)
        filtered_count = len(filtered)
        
        # Calcolo percentuale
        percentage = (filtered_count / total_lines * 100) if total_lines > 0 else 0
        
        # Layout Metriche Generali
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{total_lines:,}</div><div class="metric-label">Voci Totali</div></div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #ff6e6e;">{filtered_count:,}</div><div class="metric-label">Voci Filtrate</div></div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{percentage:.2f}%</div><div class="metric-label">Quota Filtrata</div></div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sezione Grafici e Dettaglio livelli (Plotly)
        chart_col, details_col = st.columns([2, 1])
        
        with chart_col:
            # Prepara dati per Plotly
            severity_df = pd.DataFrame(list(severity_counts.items()), columns=["Severità", "Conteggio"])
            severity_df = severity_df[severity_df["Conteggio"] > 0]
            
            if not severity_df.empty:
                colors = {
                    "CRITICAL": "#ff5555",
                    "ERROR": "#ff6e6e",
                    "WARNING": "#ffb86c",
                    "INFO": "#50fa7b",
                    "DEBUG": "#8be9fd"
                }
                
                fig = px.pie(
                    severity_df, 
                    values="Conteggio", 
                    names="Severità",
                    color="Severità",
                    color_discrete_map=colors,
                    hole=0.4,
                    title="Distribuzione della Severità nei Log"
                )
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#ffffff',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5
                    ),
                    margin=dict(t=40, b=20, l=10, r=10),
                    height=250
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nessuna severità rilevata nel file log.")
                
        with details_col:
            st.markdown("<h4 style='text-align: center; color: white; font-family: \"Space Grotesk\", sans-serif; font-weight: 600;'>Conteggio Livelli</h4>", unsafe_allow_html=True)
            html_table = "<div class='badge-row-container'>"
            badge_colors = {
                "CRITICAL": "#ff5555",
                "ERROR": "#ff6e6e",
                "WARNING": "#ffb86c",
                "INFO": "#50fa7b",
                "DEBUG": "#8be9fd"
            }
            for sev, count in severity_counts.items():
                col = badge_colors.get(sev, "#94a3b8")
                html_table += f"<div class='badge-row'><span style='color: {col}; font-weight: bold;'>● {sev}</span><span style='color: white; font-weight: 600;'>{count:,}</span></div>"
            html_table += "</div>"
            st.markdown(html_table, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sezione log filtrati
        with st.expander("👁️ Visualizza le righe di log filtrate", expanded=True):
            if filtered_count > 0:
                # Slider dinamico tarato sul numero effettivo di righe filtrate
                max_val = max(1, filtered_count)
                max_lines = st.slider(
                    "Numero massimo di righe da inviare a Gemini", 
                    min_value=1, 
                    max_value=max_val, 
                    value=min(200, max_val),
                    help="Seleziona quante righe inviare per ottimizzare l'analisi e il contesto."
                )
                
                # Selezione ordinamento (Prime N vs Ultime N)
                slice_order = st.radio(
                    "Quali righe inviare a Gemini?",
                    options=["Ultime righe (Consigliato per catturare il crash finale)", "Prime righe"],
                    horizontal=True
                )
                
                filtered_texts = [entry["text"] for entry in filtered]
                
                if "Ultime" in slice_order:
                    logs_to_send = filtered_texts[-max_lines:]
                    order_label = "ultime"
                else:
                    logs_to_send = filtered_texts[:max_lines]
                    order_label = "prime"
                
                # Visualizzazione dell'anteprima con box HTML colorato ad altezza fissa e scroll nativo
                preview_text = "\n".join(logs_to_send)
                colorized_preview = colorize_log(preview_text)
                html_preview = f"<div style='margin-bottom: 8px; font-size: 0.9rem; color: #94a3b8;'>Anteprima dei log selezionati per l'invio ({len(logs_to_send)} righe):</div><div class='log-preview'>{colorized_preview}</div>"
                st.markdown(html_preview, unsafe_allow_html=True)
                
                if len(filtered_texts) > max_lines:
                    st.warning(f"Nota: Verranno inviate solo le {order_label} {max_lines} righe filtrate su {filtered_count} totali per ottimizzare il contesto.")
            else:
                st.info("Nessuna riga trovata con i filtri attuali. Prova ad includere più livelli di severità o a modificare la ricerca.")
                logs_to_send = []
                
        # Pulsante per avviare l'analisi con Gemini
        if len(logs_to_send) > 0:
            st.markdown("---")
            
            # Stima dei token (Calcolata in tempo reale localmente per evitare lag di rete durante lo slide)
            logs_payload = "\n".join(logs_to_send)
            token_count = len(logs_payload) // 4
            
            # Tariffe per 1M di token (in USD)
            PRICING = {
                "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
                "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
                "gemini-1.5-flash": {"input": 0.075, "output": 0.30}
            }
            
            pricing_info = PRICING.get(model_option, PRICING["gemini-2.5-flash"])
            input_cost = (token_count / 1_000_000) * pricing_info["input"]
            output_tokens_est = 500  # Stima di un report medio strutturato
            output_cost = (output_tokens_est / 1_000_000) * pricing_info["output"]
            total_cost = input_cost + output_cost
            
            # Badge di avvertimento sul costo/scelta modello
            cost_warning_html = ""
            if model_option == "gemini-2.5-pro" and token_count > 5000:
                cost_warning_html = f"<div class='cost-suggestion'>⚠️ <b>Suggerimento</b>: Con questa quantità di log, l'uso di <i>gemini-2.5-flash</i> costerebbe circa il 94% in meno (${((token_count / 1_000_000) * PRICING['gemini-2.5-flash']['input'] + (output_tokens_est / 1_000_000) * PRICING['gemini-2.5-flash']['output']):.5f} totali) pur mantenendo ottime performance.</div>"
                
            cost_card_html = f"""
            <div class="cost-card">
                <div class="cost-title">
                    <span>💰</span>
                    <span>Analisi Stima dei Costi (API Gemini)</span>
                </div>
                <div class="cost-grid">
                    <div class="cost-item">
                        <span class="cost-label">Token Input Stimati</span>
                        <span class="cost-val">{token_count:,}</span>
                    </div>
                    <div class="cost-item">
                        <span class="cost-label">Costo Input (Prompt)</span>
                        <span class="cost-val" style="color: #4ade80;">${input_cost:.6f}</span>
                    </div>
                    <div class="cost-item">
                        <span class="cost-label">Token Output Stimati</span>
                        <span class="cost-val">~{output_tokens_est}</span>
                    </div>
                    <div class="cost-item">
                        <span class="cost-label">Costo Output (Report)</span>
                        <span class="cost-val" style="color: #4ade80;">${output_cost:.6f}</span>
                    </div>
                </div>
                <div class="cost-total-row">
                    <span class="cost-total-label">Costo Totale Estimato</span>
                    <span class="cost-total-val">${total_cost:.6f}</span>
                </div>
                {cost_warning_html}
            </div>
            """
            st.markdown(cost_card_html, unsafe_allow_html=True)
                
            # Pulsante per avviare generazione del report
            if not gemini_key:
                st.error("Impossibile procedere: Chiave API Gemini non configurata. Imposta `GEMINI_API_KEY` nel file `.env` o nel sistema.")
            else:
                if st.button("🚀 Genera Report di Analisi con Gemini"):
                    with st.spinner("Gemini sta elaborando i log di errore..."):
                        try:
                            # Prepara il client Gemini
                            client = genai.Client(api_key=gemini_key)
                            
                            # Istruzioni di sistema dettagliate
                            system_instruction = (
                                "Sei un esperto software engineer, DevOps ed SRE senior. Ti verranno forniti i log estratti da un sistema o un'applicazione.\n"
                                "Analizza i log e produci un report strutturato compilando lo schema JSON richiesto.\n"
                                "Usa l'italiano per la risposta. Mantieni uno stile formale, chiaro e orientato alla risoluzione del problema.\n"
                                "Nei campi Pydantic:\n"
                                "- problem_summary: Riassumi i problemi riscontrati (eventi anomali rilevati, frequenza ed impatto complessivo).\n"
                                "- root_cause_analysis: Spiega la causa tecnica dettagliata (Root Cause Analysis) basandoti sulle stack trace, codici di errore e messaggi dei log.\n"
                                "- recommendations: Suggerisci raccomandazioni pratiche ed operative di risoluzione (bug fix per i dev, modifiche infrastrutturali o configurazioni)."
                            )
                            
                            user_prompt = (
                                "Ecco le righe di log di errore da analizzare:\n\n"
                                f"```log\n{logs_payload}\n```\n\n"
                                "Genera il report strutturato in base a queste informazioni."
                            )
                            
                            # Chiamata all'API Gemini con Structured Output (Pydantic)
                            response = client.models.generate_content(
                                model=model_option,
                                contents=user_prompt,
                                config=types.GenerateContentConfig(
                                    system_instruction=system_instruction,
                                    temperature=temperature,
                                    response_mime_type="application/json",
                                    response_schema=LogAnalysisReport,
                                )
                            )
                            
                            # Caricamento robusto della risposta strutturata
                            try:
                                report_obj = response.parsed
                                if not isinstance(report_obj, LogAnalysisReport):
                                    data = json.loads(response.text)
                                    report_obj = LogAnalysisReport(**data)
                            except Exception:
                                data = json.loads(response.text)
                                report_obj = LogAnalysisReport(**data)
                                
                            st.session_state["report"] = report_obj
                            st.success("✨ Report generato con successo!")
                            
                        except APIError as api_err:
                            st.error(f"Errore dell'API di Gemini: {api_err.message}")
                        except Exception as e:
                            st.error(f"Si è verificato un errore inaspettato: {e}")
                            
            # Mostra il report strutturato se presente nel session state
            if st.session_state.get("report") is not None:
                report_obj = st.session_state["report"]
                
                st.markdown("### 📊 Report di Analisi Gemini")
                
                points = [
                    {"data": report_obj.problem_summary, "idx": 1},
                    {"data": report_obj.root_cause_analysis, "idx": 2},
                    {"data": report_obj.recommendations, "idx": 3}
                ]
                
                for pt in points:
                    title = pt["data"].title
                    content = pt["data"].content
                    idx = pt["idx"]
                    
                    html_content = markdown_to_html(content)
                    st.markdown(f'<div class="report-card report-card-{idx}"><div class="report-title">{title}</div><div class="report-content">{html_content}</div></div>', unsafe_allow_html=True)
                    
                # Ricostruzione testo Markdown intero per il download
                markdown_report = f"""# Report di Analisi dei Log

## {report_obj.problem_summary.title}
{report_obj.problem_summary.content}

## {report_obj.root_cause_analysis.title}
{report_obj.root_cause_analysis.content}

## {report_obj.recommendations.title}
{report_obj.recommendations.content}
"""
                
                # Bottone per scaricare il report
                st.download_button(
                    label="💾 Scarica Report in Markdown",
                    data=markdown_report,
                    file_name="ai_log_analysis_report.md",
                    mime="text/markdown"
                )
                            
else:
    st.info("👋 Benvenuto! Carica un file di log (.txt o .log) per iniziare ad analizzarlo.")
    
    with st.expander("ℹ️ Come funziona?"):
        st.write("""
        1. **Carica il tuo log**: Trascina un file di testo contenente i log della tua applicazione.
        2. **Filtro automatico**: L'applicazione isolerà le righe contenenti errori (es: `ERROR`, `Exception`, `Traceback`).
        3. **Analisi Intelligente**: Clicca su 'Genera Report' per inviare i log filtrati all'API di Gemini.
        4. **Report in 3 Punti**: Gemini produrrà un report in italiano strutturato in:
           - **Sintesi delle Problematiche**: Panoramica delle anomalie e degli eventi riscontrati.
           - **Analisi delle Cause Principali**: Spiegazione tecnica dettagliata delle possibili cause (Root Cause Analysis).
           - **Raccomandazioni e Soluzioni**: Suggerimenti operativi e passi risolutivi di fix.
        """)
