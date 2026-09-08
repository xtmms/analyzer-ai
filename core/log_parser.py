"""
Parsing, filtraggio, deduplicazione e troncamento delle righe di log.

Tutte le funzioni qui sono pure (input -> output, nessuno stato globale,
nessuna chiamata di rete) e sono coperte da test in tests/test_log_parser.py.
Se devi modificare come i log vengono interpretati o preparati per l'invio
all'AI, questo è l'unico file che ti serve leggere.
"""
import re

from config import MAX_ENTRY_CHARS, DEFAULT_MAX_LINES

_SEVERITY_PATTERNS = {
    "CRITICAL": re.compile(r"\b(CRITICAL|FATAL|SEVERE)\b", re.IGNORECASE),
    "ERROR": re.compile(r"\b(ERROR|EXCEPTION|FAIL|FAILED)\b", re.IGNORECASE),
    "WARNING": re.compile(r"\b(WARNING|WARN)\b", re.IGNORECASE),
    "INFO": re.compile(r"\b(INFO)\b", re.IGNORECASE),
    "DEBUG": re.compile(r"\b(DEBUG)\b", re.IGNORECASE),
}

# Timestamp tipo "2026-06-25 16:02:22" o "2026-06-25T16:02:22.123" ad inizio riga,
# usato per normalizzare le righe prima del confronto in dedupe_entries().
_LEADING_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?\s*")


def mask_pii_and_secrets(text: str) -> str:
    """Oscura dati sensibili (PII e segreti) tramite Regex."""
    # IPv4
    text = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b").sub("[IPV4_MASKED]", text)
    # Email
    text = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b").sub("[EMAIL_MASKED]", text)
    # UUIDs
    text = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b").sub("[UUID_MASKED]", text)
    # Basic Bearer / JWT token (eyJ...)
    text = re.compile(r"\b(Bearer\s+)?eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b").sub("Bearer [JWT_MASKED]", text)
    return text


def detect_severity(text: str) -> str:
    """Determina la severità di un blocco di testo (riga singola o traceback)."""
    if "traceback (most recent call last)" in text.lower() or "traceback (" in text:
        return "ERROR"
    for level, pattern in _SEVERITY_PATTERNS.items():
        if pattern.search(text):
            return level
    return "INFO"


def parse_junit_xml(xml_content: str) -> list[dict]:
    import xml.etree.ElementTree as ET
    entries = []
    try:
        root = ET.fromstring(xml_content)
        for testcase in root.iter('testcase'):
            name = testcase.get('name', 'Unknown test')
            classname = testcase.get('classname', '')
            full_name = f"{classname}.{name}" if classname else name
            
            for child in testcase:
                if child.tag in ('failure', 'error'):
                    message = child.get('message', '')
                    stack_trace = child.text or ''
                    
                    text = f"TEST FAILED: {full_name}\nMESSAGE: {message}\nTRACEBACK:\n{stack_trace.strip()}"
                    entries.append({
                        "text": text,
                        "severity": "ERROR",
                        "is_traceback": True
                    })
    except ET.ParseError:
        pass
    return entries


def extract_json_failures(data) -> list[dict]:
    entries = []
    if isinstance(data, dict):
        if data.get("status") in ("failed", "fail") or data.get("state") == "failed" or data.get("outcome") == "failed":
            name = data.get("name") or data.get("title", "Unknown test")
            err = data.get("err") or data.get("error") or {}
            message = err.get("message") if isinstance(err, dict) else str(err)
            stack = err.get("stack") if isinstance(err, dict) else ""
            
            text = f"TEST FAILED: {name}\nMESSAGE: {message}\nTRACEBACK:\n{stack}"
            entries.append({
                "text": text,
                "severity": "ERROR",
                "is_traceback": True
            })
        for v in data.values():
            entries.extend(extract_json_failures(v))
    elif isinstance(data, list):
        for item in data:
            entries.extend(extract_json_failures(item))
    return entries


def parse_log_to_entries(log_content: str) -> list[dict]:
    """
    Parsa l'intero log riga per riga, raggruppando le stack trace Traceback
    in elementi logici multi-riga. Rileva il livello di severità di ciascun
    elemento. Tenta prima il parsing di JSON (test report) e XML (JUnit).

    Ritorna una lista di dict: {"text": str, "severity": str, "is_traceback": bool}
    """
    log_content_stripped = log_content.strip()
    
    # Auto-routing JSON
    if log_content_stripped.startswith('{') or log_content_stripped.startswith('['):
        import json
        try:
            data = json.loads(log_content_stripped)
            entries = extract_json_failures(data)
            if entries:
                return entries
        except json.JSONDecodeError:
            pass

    # Auto-routing XML
    if log_content_stripped.startswith('<?xml') or log_content_stripped.startswith('<testsuite'):
        entries = parse_junit_xml(log_content_stripped)
        if entries:
            return entries

    # Fallback lograw
    lines = log_content.splitlines()
    entries: list[dict] = []

    in_traceback = False
    traceback_buffer: list[str] = []

    for line in lines:
        is_traceback_start = (
            "traceback (most recent call last)" in line.lower()
            or line.strip().startswith("Traceback (")
            or (
                line.strip().startswith("at ")
                and len(entries) > 0
                and entries[-1]["severity"] == "ERROR"
            )
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
                entries.append(
                    {"text": text, "severity": detect_severity(text), "is_traceback": True}
                )
                in_traceback = False
                traceback_buffer = []
            continue

        if line.strip():
            entries.append(
                {"text": line, "severity": detect_severity(line), "is_traceback": False}
            )

    if in_traceback and traceback_buffer:
        text = "\n".join(traceback_buffer)
        entries.append({"text": text, "severity": detect_severity(text), "is_traceback": True})

    return entries


def filter_entries(entries: list[dict], selected_severities: list[str], search_query: str) -> list[dict]:
    """Filtra le entry per severità e per testo/regex di ricerca."""
    filtered = []
    search_pattern = None
    if search_query.strip():
        try:
            search_pattern = re.compile(search_query, re.IGNORECASE)
        except re.error:
            search_pattern = None

    for entry in entries:
        if entry["severity"] not in selected_severities:
            continue

        if search_query.strip():
            if search_pattern:
                if not search_pattern.search(entry["text"]):
                    continue
            else:
                if search_query.lower() not in entry["text"].lower():
                    continue

        filtered.append(entry)

    return filtered


def dedupe_entries(entries: list[dict]) -> list[dict]:
    """
    Comprime righe consecutive identiche (a meno del timestamp) in una sola
    entry con contatore, per ridurre i token inviati all'AI su log ripetitivi
    (es. health-check falliti ogni secondo, stesso stack trace ripetuto N volte).

    Non tocca le entry di traceback multi-riga: vengono confrontate per
    uguaglianza esatta del testo dopo la rimozione del solo timestamp iniziale
    dell'eventuale prima riga.
    """
    if not entries:
        return []

    def normalize(text: str) -> str:
        return _LEADING_TIMESTAMP.sub("", text, count=1).strip()

    deduped: list[dict] = []
    prev_norm = None

    for entry in entries:
        norm = normalize(entry["text"])
        if deduped and norm == prev_norm:
            last = deduped[-1]
            last["count"] = last.get("count", 1) + 1
        else:
            new_entry = dict(entry)
            new_entry["count"] = 1
            deduped.append(new_entry)
            prev_norm = norm

    # Applica il suffisso "(xN)" solo dove serve, per non sporcare il testo
    # delle entry non ripetute
    for entry in deduped:
        if entry["count"] > 1:
            entry["text"] = f"{entry['text']}  [ripetuta x{entry['count']}]"

    return deduped


def truncate_entry_text(text: str, max_chars: int = MAX_ENTRY_CHARS) -> str:
    """
    Tronca il testo di una entry troppo lunga (tipicamente una traceback enorme)
    mantenendo testa e coda, che di solito contengono l'informazione più utile
    (tipo eccezione all'inizio, punto di fallimento reale in fondo).
    """
    if len(text) <= max_chars:
        return text

    head_chars = max_chars // 2
    tail_chars = max_chars - head_chars
    omitted = len(text) - max_chars
    return (
        f"{text[:head_chars]}\n"
        f"... [{omitted} caratteri troncati per ottimizzare i token] ...\n"
        f"{text[-tail_chars:]}"
    )


def smart_truncate_entries(entries: list[dict], max_lines: int = DEFAULT_MAX_LINES) -> list[dict]:
    """
    Seleziona i chunk più importanti se il log supera max_lines.
    Dà priorità a righe con ERROR, CRITICAL o is_traceback=True,
    e preleva contesto circostante.
    """
    if len(entries) <= max_lines:
        return entries
    
    error_indices = [i for i, e in enumerate(entries) if e["severity"] in ("ERROR", "CRITICAL") or e["is_traceback"]]
    
    if not error_indices:
        return entries[-max_lines:]
        
    selected_indices = set()
    lines_per_error = max(10, max_lines // len(error_indices))
    
    for idx in error_indices:
        start = max(0, idx - (lines_per_error // 2))
        end = min(len(entries), idx + (lines_per_error // 2) + 1)
        for i in range(start, end):
            selected_indices.add(i)
            
    current_idx = len(entries) - 1
    while len(selected_indices) < max_lines and current_idx >= 0:
        selected_indices.add(current_idx)
        current_idx -= 1
        
    sorted_indices = sorted(list(selected_indices))[:max_lines]
    
    result = []
    prev_i = -1
    for i in sorted_indices:
        if prev_i != -1 and i > prev_i + 1:
            result.append({"text": "\n... [SNIP] ...\n", "severity": "INFO", "is_traceback": False})
        result.append(entries[i])
        prev_i = i
        
    return result


def prepare_entries_for_send(
    entries: list[dict], dedupe: bool = True, max_entry_chars: int = MAX_ENTRY_CHARS
) -> list[str]:
    """
    Pipeline completa di preparazione delle entry prima dell'invio all'AI:
    smart truncation + dedupe opzionale + troncamento per-entry + masking PII.
    Ritorna la lista di testi pronti da unire con "\\n" nel payload finale.
    """
    working = smart_truncate_entries(entries)
    if dedupe:
        working = dedupe_entries(working)
    
    final_texts = []
    for e in working:
        text = truncate_entry_text(e["text"], max_entry_chars)
        text = mask_pii_and_secrets(text)
        final_texts.append(text)
        
    return final_texts
