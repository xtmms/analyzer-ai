import { FileCheck2, UploadCloud } from "lucide-react";
import { useCallback, useRef, useState, type ChangeEvent, type DragEvent } from "react";

interface UploadCardProps {
  fileName: string | null;
  onFileLoaded: (content: string, fileName: string) => void;
  onError: (message: string) => void;
}

const MAX_FILE_BYTES = 5_000_000;

export function UploadCard({ fileName, onFileLoaded, onError }: UploadCardProps) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const readFile = useCallback(
    (file: File) => {
      if (file.size > MAX_FILE_BYTES) {
        onError(`Il file supera il limite di ${(MAX_FILE_BYTES / 1_000_000).toFixed(0)}MB.`);
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        onFileLoaded(String(reader.result ?? ""), file.name);
      };
      reader.onerror = () => onError("Errore nella lettura del file.");
      reader.readAsText(file);
    },
    [onError, onFileLoaded],
  );

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) readFile(file);
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) readFile(file);
  }

  return (
    <div
      className={`glass-card cursor-pointer p-8 text-center transition ${
        dragActive ? "border-accent bg-accent-soft" : ""
      }`}
      onDragOver={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.log"
        className="hidden"
        onChange={handleChange}
      />
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-accent-soft">
        {fileName ? (
          <FileCheck2 className="h-6 w-6 text-accent" strokeWidth={1.75} />
        ) : (
          <UploadCloud className="h-6 w-6 text-accent" strokeWidth={1.75} />
        )}
      </div>
      <p className="mt-3 font-medium text-text">
        {fileName ? `File caricato: ${fileName}` : "Trascina un file di log qui, o clicca per selezionarlo"}
      </p>
      <p className="mt-1 text-sm text-text-muted">Formati supportati: .txt, .log — max 5MB</p>
    </div>
  );
}
