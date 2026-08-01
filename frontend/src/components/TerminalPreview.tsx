interface TerminalPreviewProps {
  colorizedHtml: string;
  numLines: number;
}

export function TerminalPreview({ colorizedHtml, numLines }: TerminalPreviewProps) {
  return (
    <div className="glass-card overflow-hidden">
      <div className="flex items-center gap-2 border-b border-white/10 bg-black/30 px-4 py-2.5">
        <span className="h-3 w-3 rounded-full bg-[#ff5f56]" />
        <span className="h-3 w-3 rounded-full bg-[#ffbd2e]" />
        <span className="h-3 w-3 rounded-full bg-[#27c93f]" />
        <span className="ml-2 text-xs text-text-muted">terminal — {numLines} righe selezionate</span>
      </div>
      <pre
        className="max-h-96 overflow-auto whitespace-pre-wrap break-words p-4 font-mono text-xs leading-relaxed text-text"
        dangerouslySetInnerHTML={{ __html: colorizedHtml || "// Nessuna riga da mostrare" }}
      />
    </div>
  );
}
