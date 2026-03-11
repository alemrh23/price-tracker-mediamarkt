import json
import os
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URL = "https://canarias.mediamarkt.es/products/plancha-de-vapor-philips-dst7031-70-250-g-apagado-automatico-300-ml-verde-opalo-menta"
STATE_FILE = "state.json"

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)

def _to_float(x) -> float | None:
    if x is None:
        return None
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None

def extract_price_from_jsonld(soup: BeautifulSoup) -> float | None:
    """
    Intenta extraer el precio desde JSON-LD (lo más estable cuando existe).
    """
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = tag.string
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]
        for obj in items:
            if not isinstance(obj, dict):
                continue
            offers = obj.get("offers")
            # offers puede ser dict o lista
            if isinstance(offers, dict):
                p = _to_float(offers.get("price"))
                if p is not None:
                    return p
            elif isinstance(offers, list):
                for off in offers:
                    if isinstance(off, dict):
                        p = _to_float(off.get("price"))
                        if p is not None:
                            return p
    return None

def extract_price_fallback_text(soup: BeautifulSoup) -> float | None:
    """
    Plan B: busca el primer patrón '123,45 €' en el texto visible.
    Menos fiable, pero útil si cambia el JSON-LD.
    """
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(\d{1,5}[.,]\d{2})\s*€", text)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))

def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main() -> None:
    r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    price = extract_price_from_jsonld(soup) or extract_price_fallback_text(soup)
    if price is None:
        raise RuntimeError("No pude extraer el precio. Probablemente cambió el HTML o hay bloqueo anti-bot.")

    state = load_state()
    prev = state.get("last_price")

    state["last_checked_utc"] = datetime.now(timezone.utc).isoformat()
    state["last_price"] = price
    save_state(state)

    # Salidas para GitHub Actions
    print(f"PRICE={price}")
    if prev is None:
        print("FIRST_RUN=1")
        return

    changed = float(prev) != float(price)
    print(f"CHANGED={'1' if changed else '0'}")
    print(f"PREV_PRICE={prev}")

if __name__ == "__main__":
    main()
