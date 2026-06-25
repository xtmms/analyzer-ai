import streamlit as st
import re
import os
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

# Carica le variabili d'ambiente da un file .env se presente
load_dotenv()

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="QA Log Analyzer",
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


# Funzione di filtraggio dei log
def filter_error_logs(log_content: str, keywords: list) -> list:
    """
    Analizza il log riga per riga e restituisce solo quelle che contengono parole chiave di errore
    o che fanno parte di un blocco di Traceback.
    """
    lines = log_content.splitlines()
    filtered = []
    
    # Crea regex per le parole chiave selezionate (case-insensitive)
    # Es. \b(ERROR|CRITICAL|FATAL|EXCEPTION|SEVERE|FAIL|FAILED)\b
    keywords_escaped = [re.escape(k.strip()) for k in keywords if k.strip()]
    if not keywords_escaped:
        return []
        
    keyword_pattern = re.compile(r'\b(' + '|'.join(keywords_escaped) + r')\b', re.IGNORECASE)
    
    in_traceback = False
    traceback_buffer = []
    
    for line in lines:
        # Rileva l'inizio di un traceback di Python (o pattern simile in Java/JS stack traces)
        is_traceback_start = (
            "traceback (most recent call last)" in line.lower() or 
            line.strip().startswith("Traceback (") or
            (line.strip().startswith("at ") and len(filtered) > 0 and "Exception" in filtered[-1])
        )
        
        if is_traceback_start:
            in_traceback = True
            traceback_buffer = [line]
            continue
            
        if in_traceback:
            # Le linee del traceback di solito iniziano con uno spazio o una tabulazione, 
            # oppure contengono percorsi di file o specifiche di riga.
            # Terminiamo il traceback se incontriamo una riga non vuota che non inizia con uno spazio.
            if line.startswith(" ") or line.startswith("\t") or not line.strip():
                traceback_buffer.append(line)
                continue
            else:
                # Questa riga descrive solitamente l'eccezione finale (es: ValueError: ...)
                traceback_buffer.append(line)
                filtered.append("\n".join(traceback_buffer))
                in_traceback = False
                traceback_buffer = []
                continue
                
        # Per le righe standard, eseguiamo il match con le parole chiave
        if keyword_pattern.search(line):
            filtered.append(line)
            
    # Se il file finisce mentre siamo in un traceback, salviamo il buffer
    if in_traceback and traceback_buffer:
        filtered.append("\n".join(traceback_buffer))
        
    return filtered


# SIDEBAR - Configurazione dell'Analisi
st.sidebar.markdown("### ⚙️ Impostazioni Analisi")

# Recupero chiave API dall'ambiente (configurata a codice/sistema)
gemini_key = os.environ.get("GEMINI_API_KEY", "")

if not gemini_key:
    st.sidebar.error("❌ Chiave API mancante. Configura `GEMINI_API_KEY` nel file `.env` o tra le variabili d'ambiente per procedere.")
else:
    st.sidebar.success("🔑 Chiave API caricata dall'ambiente.")

# 2. Selezione Modello
model_option = st.sidebar.selectbox(
    "Modello Gemini",
    options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
    index=0,
    help="Scegli gemini-2.5-flash per risposte veloci ed economiche. Scegli gemini-2.5-pro per log estremamente complessi o analisi dettagliate."
)

# 3. Parametri Generazione
temperature = st.sidebar.slider(
    "Temperatura", 
    min_value=0.0, 
    max_value=1.0, 
    value=0.2, 
    step=0.1,
    help="Valori bassi (es. 0.2) rendono la risposta più deterministica e aderente ai fatti. Valori alti (es. 0.7) favoriscono la creatività."
)

# 4. Parole chiave di Errore
keywords_input = st.sidebar.text_area(
    "Parole chiave per il filtro",
    value="ERROR, CRITICAL, FATAL, EXCEPTION, SEVERE, FAIL, FAILED, Traceback",
    help="Lista di parole chiave separate da virgola da cercare nelle righe di log."
)
keywords_list = [k.strip() for k in keywords_input.split(",") if k.strip()]


# MAIN CONTENT
st.markdown('<h1 class="main-title">🔍 QA Log Analyzer</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Analizza i file di log delle tue sessioni di test, filtra le anomalie e ottieni un report strutturato da Gemini AI.</p>', unsafe_allow_html=True)

# Upload del file
uploaded_file = st.file_uploader(
    "Carica un file di log (.txt, .log)", 
    type=["txt", "log"],
    help="Trascina e rilascia il file di log qui per iniziare il filtraggio."
)

if uploaded_file is not None:
    # Lettura del contenuto del file log
    try:
        log_content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        try:
            # Fallback se non è UTF-8 (es. ANSI/ISO-8859-1)
            log_content = uploaded_file.read().decode("latin1")
        except Exception as e:
            st.error(f"Errore nella lettura del file: {e}")
            log_content = None
            
    if log_content:
        # Analisi preliminare delle righe
        total_lines = len(log_content.splitlines())
        
        # Filtro delle righe di errore
        filtered_errors = filter_error_logs(log_content, keywords_list)
        error_lines_count = len(filtered_errors)
        
        # Calcolo percentuale di errori
        error_percentage = (error_lines_count / total_lines * 100) if total_lines > 0 else 0
        
        # Layout Metriche
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{total_lines:,}</div>
                <div class="metric-label">Righe Totali</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #ff4d4d;">{error_lines_count:,}</div>
                <div class="metric-label">Righe con Errori/Eccezioni</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{error_percentage:.2f}%</div>
                <div class="metric-label">Percentuale Errori</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sezione log filtrati
        with st.expander("👁️ Visualizza le righe di errore filtrate", expanded=True):
            if error_lines_count > 0:
                # Uniamo le righe filtrate per mostrarle in un box di codice
                filtered_text_preview = "\n".join(filtered_errors)
                st.code(filtered_text_preview, language="log")
                
                # Sezione per limitare i log inviati a Gemini per evitare di superare i limiti
                max_lines = st.slider("Numero massimo di righe di errore da inviare a Gemini", min_value=10, max_value=500, value=200)
                
                # Taglio delle righe se superano il limite
                logs_to_send = filtered_errors[:max_lines]
                if len(filtered_errors) > max_lines:
                    st.warning(f"Nota: Verranno inviate solo le prime {max_lines} righe di errore a Gemini su {error_lines_count} totali per ottimizzare il contesto.")
            else:
                st.info("Nessuna riga di errore trovata con i filtri attuali. Prova a modificare le parole chiave nel pannello laterale.")
                logs_to_send = []
                
        # Bottone per avviare l'analisi con Gemini
        if len(logs_to_send) > 0:
            st.markdown("---")
            
            # Controllo se la chiave è presente prima di permettere l'invio
            if not gemini_key:
                st.error("Impossibile procedere: Chiave API Gemini non configurata. Imposta `GEMINI_API_KEY` nel file `.env` o nel sistema.")
            else:
                if st.button("🚀 Genera Report di Analisi con Gemini"):
                    with st.spinner("Gemini sta elaborando i log di errore..."):
                        try:
                            # Prepara il client Gemini
                            client = genai.Client(api_key=gemini_key)
                            
                            # Formatta il testo dei log da inviare
                            logs_payload = "\n".join(logs_to_send)
                            
                            # Istruzioni di sistema dettagliate per richiedere i 3 punti strutturati
                            system_instruction = (
                                "Sei un analista QA e debugger senior. Ti verranno forniti i log di errore estratti da un'applicazione.\n"
                                "Analizza i log e produci un report strutturato ESCLUSIVAMENTE in questi 3 punti principali:\n\n"
                                "1. Sintesi delle Problematiche: Descrivi a alto livello quali errori si sono verificati e con quale frequenza/impatto.\n"
                                "2. Analisi delle Cause Principali: Esegui una Root Cause Analysis basandoti sulle stack trace e i messaggi forniti.\n"
                                "3. Raccomandazioni e Soluzioni: Suggerisci passi concreti per riprodurre o testare la regressione (per il QA) e possibili fix (per i dev).\n\n"
                                "Usa l'italiano per la risposta. Mantieni uno stile formale, chiaro e orientato alla risoluzione del problema.\n"
                                "Per ciascuno dei 3 punti, inserisci un titolo chiaro e poi il contenuto in Markdown."
                            )
                            
                            user_prompt = (
                                "Ecco le righe di log di errore da analizzare:\n\n"
                                f"```log\n{logs_payload}\n```\n\n"
                                "Genera il report strutturato in 3 punti in base a queste informazioni."
                            )
                            
                            # Chiamata all'API Gemini
                            response = client.models.generate_content(
                                model=model_option,
                                contents=user_prompt,
                                config=types.GenerateContentConfig(
                                    system_instruction=system_instruction,
                                    temperature=temperature,
                                )
                            )
                            
                            report_text = response.text
                            
                            st.success("✨ Report generato con successo!")
                            
                            # Visualizzazione del report strutturato
                            st.markdown("### 📊 Report di Analisi Gemini")
                            
                            # Proviamo a dividere il report nei 3 punti in base a regex
                            p1 = re.search(r'(?:^|\n)\s*(?:###?\s*|##\s*|\*\*)*1\.\s*(.*?)(?=\n\s*(?:###?\s*|##\s*|\*\*)*2\.\s*|\Z)', report_text, re.DOTALL | re.IGNORECASE)
                            p2 = re.search(r'(?:^|\n)\s*(?:###?\s*|##\s*|\*\*)*2\.\s*(.*?)(?=\n\s*(?:###?\s*|##\s*|\*\*)*3\.\s*|\Z)', report_text, re.DOTALL | re.IGNORECASE)
                            p3 = re.search(r'(?:^|\n)\s*(?:###?\s*|##\s*|\*\*)*3\.\s*(.*?)(?=\n\s*(?:###?\s*|##\s*|\*\*)*4\.\s*|\Z)', report_text, re.DOTALL | re.IGNORECASE)
                            
                            if p1 and p2 and p3:
                                blocchi_validi = [p1.group(1).strip(), p2.group(1).strip(), p3.group(1).strip()]
                                # Mostra i tre punti in card dedicate con bordi colorati diversi
                                for idx, blocco in enumerate(blocchi_validi):
                                    # Determina il titolo del punto (prima riga del blocco)
                                    linee = blocco.split('\n')
                                    titolo = linee[0].replace('**', '').replace('###', '').replace('##', '').strip()
                                    contenuto = '\n'.join(linee[1:]) if len(linee) > 1 else ""
                                    
                                    # Se il blocco non ha un'intestazione come prima riga, o la prima riga è troppo lunga, usiamo un titolo di default
                                    if len(linee) == 1 or len(titolo) > 80:
                                        if idx == 0:
                                            titolo = "1. Sintesi delle Problematiche"
                                        elif idx == 1:
                                            titolo = "2. Analisi delle Cause Principali"
                                        else:
                                            titolo = "3. Raccomandazioni e Soluzioni"
                                        contenuto = blocco
                                    
                                    st.markdown(f"""
                                    <div class="report-card report-card-{idx+1}">
                                        <div class="report-title">{titolo}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.markdown(contenuto)
                            else:
                                # Fallback se la regex non trova la struttura attesa: mostriamo tutto in un box organizzato
                                st.markdown(f"""
                                <div class="report-card report-card-1">
                                    <div class="report-title">Report di Analisi</div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(report_text)
                                
                            # Bottone per scaricare il report
                            st.download_button(
                                label="💾 Scarica Report in Markdown",
                                data=report_text,
                                file_name="qa_log_analysis_report.md",
                                mime="text/markdown"
                            )
                            
                        except APIError as api_err:
                            st.error(f"Errore dell'API di Gemini: {api_err.message}")
                        except Exception as e:
                            st.error(f"Si è verificato un errore inaspettato: {e}")
                            
else:
    # Schermata iniziale se non è caricato alcun file
    st.info("👋 Benvenuto! Carica un file di log (.txt o .log) per iniziare ad analizzarlo.")
    
    # Esempio di come formattare il log
    with st.expander("ℹ️ Come funziona?"):
        st.write("""
        1. **Carica il tuo log**: Trascina un file di testo contenente i log della tua applicazione.
        2. **Filtro automatico**: L'applicazione isolerà le righe contenenti errori (es: `ERROR`, `Exception`, `Traceback`).
        3. **Analisi Intelligente**: Clicca su 'Genera Report' per inviare i log filtrati all'API di Gemini.
        4. **Report in 3 Punti**: Gemini produrrà un report in italiano strutturato in:
           - **Sintesi delle Problematiche**: Panoramica degli errori riscontrati.
           - **Analisi delle Cause Principali**: Spiegazione dettagliata delle possibili cause.
           - **Raccomandazioni e Soluzioni**: Passi da seguire per QA e sviluppatori.
        """)
