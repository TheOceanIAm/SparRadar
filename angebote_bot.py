#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sendet montags eine Telegram-Push mit Angebotslinks für Friedrichshain 10245.
- Standard-Sendezeit: 08:00 Europe/Berlin (konfigurierbar via SEND_TIME Umgebungsvariable)
- Läuft perfekt in GitHub Actions (oder lokal)
"""
import os
import sys
import datetime as dt
import requests
import pytz

# Umgebungsvariablen
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SEND_TIME = os.getenv("SEND_TIME", "08:00")  # HH:MM lokale Zeit (Europe/Berlin)

EU_TZ = pytz.timezone("Europe/Berlin")

# Angebotsquellen – du kannst hier deine Lieblingsfilial-Links einsetzen
SOURCES = [
    ("PENNY", "https://www.penny.de/angebote/"),
    ("Netto", "https://www.netto-online.de/angebote/"),
    ("REWE", "https://www.rewe.de/angebote/"),
    ("ALDI Nord", "https://www.aldi-nord.de/angebote.html"),
    ("BUDNI", "https://www.budni.de/angebote"),
]

def is_monday_and_send_time(now: dt.datetime, send_time: str) -> bool:
    """
    True nur dann, wenn heute Montag ist und die Stunde genau der Wunschzeit entspricht.
    So wird in GitHub Actions nur 1x versendet.
    """
    if now.weekday() != 0:  # Montag = 0
        return False
    try:
        hh, mm = [int(x) for x in send_time.split(":", 1)]
    except Exception:
        hh, mm = 8, 0
    return (now.hour == hh) and (now.minute >= mm)

def current_week_range_local(now: dt.datetime) -> tuple[str, str]:
    """Gibt den Montag–Sonntag Bereich der aktuellen Woche als Strings zurück."""
    monday = now - dt.timedelta(days=now.weekday())
    sunday = monday + dt.timedelta(days=6)
    fmt = "%d.%m.%Y"
    return monday.strftime(fmt), sunday.strftime(fmt)

def build_message(now: dt.datetime) -> str:
    start, end = current_week_range_local(now)
    header = f"🛒 Angebote Friedrichshain 10245 – Woche {start} bis {end}"
    lines = [header, ""]
    for name, url in SOURCES:
        lines.append(f"• {name} → {url}")
    lines.append("")
    lines.append("Tipp: Seiten einmal öffnen & PLZ/Filiale setzen, dann merken sie sich die Auswahl.")
    return "\n".join(lines)

def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    r = requests.post(api, data=payload, timeout=15)
    r.raise_for_status()

def main() -> int:
    if not BOT_TOKEN or not CHAT_ID:
        print("Fehlende TELEGRAM_BOT_TOKEN oder TELEGRAM_CHAT_ID in Secrets", file=sys.stderr)
        return 2

    now = dt.datetime.now(EU_TZ)

    if not is_monday_and_send_time(now, SEND_TIME):
        print("Heute ist kein Montag oder noch vor/nach der Sendezeit – kein Versand.")
        return 0

    msg = build_message(now)
    try:
        send_telegram_message(BOT_TOKEN, CHAT_ID, msg)
        print("Angebotsliste gesendet ✅")
        return 0
    except Exception as e:
        print(f"Sende-Fehler: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
