import requests, hashlib, os, json
from datetime import datetime
from bs4 import BeautifulSoup

EVENT_URL          = os.environ.get("EVENT_URL", "https://xceed.me/es/san-sebastian/event/deusto-fest-19/228319")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = os.environ.get("TELEGRAM_CHAT_IDS", "").split(",")
STATE_FILE         = "last_state.json"

AVAILABLE_KW = ["comprar","buy","get tickets","tickets","available","disponible"]
SOLD_OUT_KW  = ["agotado","sold out","no disponible","unavailable","waitlist"]
HEADERS      = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status(); return r.text

def extract(html):
    soup = BeautifulSoup(html, "html.parser")
    for sel in [{"class":"ticket"},{"class":"tickets"},{"id":"tickets"}]:
        s = soup.find(attrs=sel)
        if s: return s.get_text(" ", strip=True).lower()
    return soup.get_text(" ", strip=True).lower()

def status(text):
    for kw in SOLD_OUT_KW:
        if kw in text: return "sold_out"
    for kw in AVAILABLE_KW:
        if kw in text: return "available"
    return "unknown"

def load():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {"hash":"","status":""}

def save(h, s):
    json.dump({"hash": h, "status": s}, open(STATE_FILE, "w"))

def telegram(msg):
    if not TELEGRAM_BOT_TOKEN: return
    for chat_id in TELEGRAM_CHAT_IDS:
        chat_id = chat_id.strip()
        if chat_id:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
                timeout=10
            )

def main():
    html  = fetch(EVENT_URL)
    h     = hashlib.md5(html.encode()).hexdigest()
    st    = status(extract(html))
    prev  = load()
    print(f"Estado: {st} | Anterior: {prev['status']}")

    if st == "available" and prev["status"] in ("sold_out", "unknown", ""):
        telegram(f"🎟️ <b>¡ENTRADAS DISPONIBLES!</b>\n\n👉 <a href='{EVENT_URL}'>Comprar ahora</a>")
        print("🔔 ALERTA ENVIADA")
    elif h != prev["hash"] and prev["hash"]:
        telegram(f"👀 <b>Página cambiada</b> (estado: {st})\n\n👉 <a href='{EVENT_URL}'>Ver evento</a>")
    else:
        print("Sin cambios")
    save(h, st)

main()