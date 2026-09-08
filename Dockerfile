# Immagine di base leggera
FROM python:3.11-slim

# Imposta la working directory
WORKDIR /app

# Non copiare subito il codice, prima i requirements per sfruttare la cache di Docker
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice e gli asset
COPY config.py main.py ./
COPY core/ ./core/

# Crea la cartella di output
RUN mkdir -p output

# Definisci il comando di default per eseguire il CLI
ENTRYPOINT ["python", "main.py"]
