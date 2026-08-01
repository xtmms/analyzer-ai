"""Garantisce che la root del progetto sia su sys.path per gli import assoluti
(`import config`, `from core... import ...`) usati sia da app.py che dai test,
indipendentemente da dove viene lanciato `pytest`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
