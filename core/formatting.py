"""
Formattazione testuale: syntax highlighting dei log e conversione Markdown -> HTML
per il rendering dei report Gemini nelle card custom della UI.

Nessuna dipendenza da Streamlit: queste funzioni ritornano stringhe HTML pronte
per st.markdown(..., unsafe_allow_html=True), ma non chiamano mai Streamlit.
"""
import html
import re

from config import SEVERITY_COLORS

_BRACKET_PATTERN = re.compile(r"\[([a-zA-Z0-9_]+)\]")
_TIMESTAMP_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)")
_TRACEBACK_PATTERN = re.compile(
    r"\b(Traceback \(most recent call last\):|File &quot;[^&]+&quot;, line \d+)\b"
)
_CODE_BLOCK_PATTERN = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)```", re.DOTALL)


def colorize_log(text: str) -> str:
    """Colora sintatticamente il log in HTML: logger, timestamp, severità, traceback."""
    escaped = html.escape(text)

    escaped = _BRACKET_PATTERN.sub(
        r'<span style="color: #a78bfa; font-weight: 600;">[\1]</span>', escaped
    )
    escaped = _TIMESTAMP_PATTERN.sub(r'<span style="color: #64748b;">\1</span>', escaped)

    for keyword, col in SEVERITY_COLORS.items():
        pattern = re.compile(rf"\b({re.escape(keyword)})\b", re.IGNORECASE)
        escaped = pattern.sub(f'<span style="color: {col}; font-weight: bold;">\\1</span>', escaped)

    escaped = _TRACEBACK_PATTERN.sub(
        r'<span style="color: #ffb86c; font-style: italic;">\1</span>', escaped
    )

    return escaped


def markdown_to_html(md_text: str) -> str:
    """
    Parser Markdown -> HTML minimale (code block, inline code, bold, liste, paragrafi),
    sufficiente per i contenuti generati da Gemini nello schema LogAnalysisReport.
    Non è un parser Markdown generico: se il contenuto atteso cambia forma, estendilo qui.
    """
    escaped = html.escape(md_text)

    def replace_code_block(match: re.Match) -> str:
        lang = match.group(1)
        code = match.group(2)
        return f'<pre class="code-block-preview"><code class="language-{lang}">{code}</code></pre>'

    escaped = _CODE_BLOCK_PATTERN.sub(replace_code_block, escaped)
    escaped = re.sub(r"`([^`\n]+)`", r'<code class="inline-code">\1</code>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)

    lines = escaped.split("\n")
    in_list = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "+ ")):
            item_content = stripped[2:]
            if not in_list:
                new_lines.append('<ul class="report-list">')
                in_list = True
            new_lines.append(f"<li>{item_content}</li>")
        else:
            if in_list:
                new_lines.append("</ul>")
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append("</ul>")

    escaped = "\n".join(new_lines)

    paragraphs = escaped.split("\n\n")
    formatted_paragraphs = []
    for p in paragraphs:
        p_stripped = p.strip()
        if not p_stripped:
            continue
        if p_stripped.startswith(("<ul", "<pre", "</ul", "</pre")):
            formatted_paragraphs.append(p_stripped)
        else:
            p_formatted = p_stripped.replace("\n", "<br>")
            formatted_paragraphs.append(f'<p class="report-p">{p_formatted}</p>')

    return "\n".join(formatted_paragraphs)


def build_markdown_report(report_obj) -> str:
    """Serializza un LogAnalysisReport in un .md scaricabile (usato dal download button)."""
    return f"""# Report di Analisi dei Log

## {report_obj.problem_summary.title}
{report_obj.problem_summary.content}

## {report_obj.root_cause_analysis.title}
{report_obj.root_cause_analysis.content}

## {report_obj.recommendations.title}
{report_obj.recommendations.content}
"""
