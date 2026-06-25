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
    /* Importa font moderno */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Titolo ed header principali */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #8892b0;
        margin-bottom: 2rem;
    }
    
    /* Box metriche custom */
    .metric-card {
        background-color: #1e222b;
        border: 1px solid #2d3139;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #4b6cb7;
    }
    .metric-val {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }
    
    /* Card per i 3 punti del report di Gemini */
    .report-card {
        background: rgba(30, 34, 43, 0.7);
        border-left: 5px solid #4b6cb7;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(10px);
    }
    .report-card-1 { border-left-color: #e056fd; } /* Viola per Punto 1 */
    .report-card-2 { border-left-color: #ff9f43; } /* Arancione per Punto 2 */
    .report-card-3 { border-left-color: #1dd1a1; } /* Verde/Azzurro per Punto 3 */
    
    .report-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        color: #ffffff;
    }
    
    /* Stile per i log e codice */
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }
    
    /* Pulsanti personalizzati */
    div.stButton > button {
        background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 15px rgba(75, 108, 183, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(75, 108, 183, 0.5) !important;
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
    escaped = bracket_pattern.sub(r'<span style="color: #a1c4fd; font-weight: 600;">[\1]</span>', escaped)
    
    # 2. Date e timestamp es: 2026-06-25 16:02:22
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)')
    escaped = timestamp_pattern.sub(r'<span style="color: #8892b0;">\1</span>', escaped)
    
    # 3. Livelli di severità e parole chiave
    colors = {
        "CRITICAL": "#e056fd",
        "FATAL": "#e056fd",
        "SEVERE": "#e056fd",
        "ERROR": "#ff4d4d",
        "FAIL": "#ff4d4d",
        "FAILED": "#ff4d4d",
        "EXCEPTION": "#ff4d4d",
        "WARNING": "#ff9f43",
        "WARN": "#ff9f43",
        "INFO": "#1dd1a1",
        "DEBUG": "#54a0ff"
    }
    
    for keyword, col in colors.items():
        pattern = re.compile(rf'\b({re.escape(keyword)})\b', re.IGNORECASE)
        escaped = pattern.sub(f'<span style="color: {col}; font-weight: bold;">\\1</span>', escaped)
        
    # 4. Righe chiave Traceback
    traceback_pattern = re.compile(r'\b(Traceback \(most recent call last\):|File &quot;[^&]+&quot;, line \d+)\b')
    escaped = traceback_pattern.sub(r'<span style="color: #ff9f43; font-style: italic;">\1</span>', escaped)
    
    return escaped


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
            st.markdown(f'<div class="metric-card"><div class="metric-val" style="color: #ff4d4d;">{filtered_count:,}</div><div class="metric-label">Voci Filtrate</div></div>', unsafe_allow_html=True)
            
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
                    "CRITICAL": "#e056fd",
                    "ERROR": "#ff4d4d",
                    "WARNING": "#ff9f43",
                    "INFO": "#1dd1a1",
                    "DEBUG": "#54a0ff"
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
            st.markdown("<h4 style='text-align: center; color: white;'>Conteggio Livelli</h4>", unsafe_allow_html=True)
            html_table = "<div style='display: flex; flex-direction: column; gap: 5px; margin-top: 15px;'>"
            badge_colors = {
                "CRITICAL": "#e056fd",
                "ERROR": "#ff4d4d",
                "WARNING": "#ff9f43",
                "INFO": "#1dd1a1",
                "DEBUG": "#54a0ff"
            }
            for sev, count in severity_counts.items():
                col = badge_colors.get(sev, "#8892b0")
                html_table += f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: #1e222b; border: 1px solid #2d3139; border-radius: 6px; padding: 6px 12px;'><span style='color: {col}; font-weight: bold;'>● {sev}</span><span style='color: white; font-weight: 600;'>{count:,}</span></div>"
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
                html_preview = f"<div style='margin-bottom: 5px; font-size: 0.9rem; color: #8892b0;'>Anteprima dei log selezionati per l'invio ({len(logs_to_send)} righe):</div><pre style='background-color: #1e222b; color: #ffffff; padding: 15px; border: 1px solid #2d3139; border-radius: 8px; height: 300px; overflow-y: auto; overflow-x: auto; font-family: \"JetBrains Mono\", monospace; font-size: 0.85rem; white-space: pre; line-height: 1.4;'>{colorized_preview}</pre>"
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
                cost_warning_html = f"<div style='font-size: 0.8rem; color: #ff9f43; margin-top: 8px;'>⚠️ <b>Suggerimento</b>: Con questa quantità di log, l'uso di <i>gemini-2.5-flash</i> costerebbe circa il 94% in meno (${((token_count / 1_000_000) * PRICING['gemini-2.5-flash']['input'] + (output_tokens_est / 1_000_000) * PRICING['gemini-2.5-flash']['output']):.5f} totali) pur mantenendo ottime performance.</div>"
                
            cost_card_html = f"<div style='background-color: #1e222b; border: 1px solid #2d3139; border-radius: 8px; padding: 15px; margin-bottom: 20px;'><div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'><span style='font-size: 1.2rem;'>💰</span><span style='font-weight: bold; color: white; font-size: 1rem;'>Analisi Stima dei Costi (API Gemini)</span></div><div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;'><div><span style='color: #8892b0;'>Token Input Stimati:</span> <strong style='color: white;'>{token_count:,}</strong></div><div><span style='color: #8892b0;'>Costo Input (Prompt):</span> <strong style='color: #1dd1a1;'>${input_cost:.6f}</strong></div><div><span style='color: #8892b0;'>Token Output Stimati:</span> <strong style='color: white;'>~{output_tokens_est}</strong></div><div><span style='color: #8892b0;'>Costo Output (Report):</span> <strong style='color: #1dd1a1;'>${output_cost:.6f}</strong></div></div><hr style='border-color: #2d3139; margin: 10px 0;'><div style='display: flex; justify-content: space-between; align-items: center;'><span style='font-weight: bold; color: white; font-size: 0.95rem;'>Costo Totale Stimato:</span><strong style='color: #1dd1a1; font-size: 1.1rem;'>${total_cost:.6f}</strong></div>{cost_warning_html}</div>"
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
                    
                    st.markdown(f'<div class="report-card report-card-{idx}"><div class="report-title">{title}</div></div>', unsafe_allow_html=True)
                    st.markdown(content)
                    
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
