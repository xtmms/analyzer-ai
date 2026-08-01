"""Limiter condiviso da main.py (registrazione) e dalle route (decoratori),
in un modulo separato per evitare un import circolare tra i due."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
