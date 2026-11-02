# -*- coding: utf-8 -*-
"""Cazador v2 sobre la Biblioteca de Anuncios (sin conector oficial).

- Pagina hasta el fondo (la app carga por lotes al llegar al final).
- Extrae cada tarjeta del DOM: id, fecha de inicio, anunciante, dominio, copy.
- Enriquece con page_id desde el JSON embebido cuando esta disponible.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAL = os.path.join(BASE, "salidas")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
DEC = json.JSONDecoder()

MES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7,
       "ago": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12,
       "jan": 1, "apr": 4, "aug": 8, "dec": 12}

CARD_JS = """() => {
  const spans = [...document.querySelectorAll('span')]
    .filter(s => (s.textContent || '').startsWith('Identificador de la biblioteca'));
  const out = [];
  for (const s of spans) {
    let n = s, card = null;
    for (let i = 0; i < 14 && n; i++) {
      n = n.parentElement;
      if (!n) break;
      const t = n.innerText || '';
      if (t.includes('Ver detalles') && t.length > 120) { card = n; break; }
    }
    if (card) out.push(card.innerText);
  }
  return out;
}"""


def parse_date(s):
    s = s.strip().lower().replace("de ", "")
    m = re.match(r"(\d{1,2})\s+([a-záéíóú]+)\.?\s+(\d{4})", s)
    if m:
        d, mes, y = int(m.group(1)), m.group(2)[:4], int(m.group(3))
        for k, v in MES.items():
            if mes.startswith(k):
                return dt.date(y, v, d)
    return None


def parse_card(txt):
    d = {}
    m = re.search(r"Identificador de la biblioteca:\s*(\d+)", txt)
    if not m:
        return None
    d["id"] = m.group(1)
    m = re.search(r"En circulaci[oó]n desde el ([^\n]+)", txt) or \
        re.search(r"Started running on ([^\n]+)", txt)
    d["fecha"] = parse_date(m.group(1)) if m else None
    # anunciante: lo que hay entre "Ver detalles..." y "Publicidad"
    m = re.search(r"Ver detalles[^\n]*\n([^\n]+)\nPublicidad", txt)
    d["page"] = m.group(1).strip() if m else None
    # dominio destino (linea en mayusculas con punto)
    m = re.search(r"\n([A-Z0-9][A-Z0-9.\-]{3,}\.[A-Z]{2,})\n", txt)
    d["dest"] = m.group(1).lower() if m else None
    # copy: primera linea tras "Publicidad"
    m = re.search(r"\nPublicidad\n([^\n]+)", txt)
    d["copy"] = m.group(1).strip()[:160] if m else None
    d["dup"] = "varias versiones" in txt or "varios anuncios" in txt
    return d


def scrape(country, kw, rounds=12):
    ads, total = {}, None
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = b.new_context(locale="es-ES", viewport={"width": 1400, "height": 1000}, user_agent=UA)
        pg = ctx.new_page()
        pg.goto("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                "&country=%s&q=%s&search_type=keyword_unordered&media_type=all"
                % (country, quote_plus(kw)), wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(6000)
        for i in range(rounds):
            for t in pg.evaluate(CARD_JS):
                a = parse_card(t)
                if a and a["id"] not in ads:
                    ads[a["id"]] = a
            html = pg.content()
            if total is None:
                m = re.search(r'"search_results_connection":\{"count":(\d+)', html)
                if m:
                    total = int(m.group(1))
            pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            pg.wait_for_timeout(2300)
        # ultima pasada
        for t in pg.evaluate(CARD_JS):
            a = parse_card(t)
            if a and a["id"] not in ads:
                ads[a["id"]] = a
        b.close()
    return list(ads.values()), total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("keyword")
    ap.add_argument("--rounds", type=int, default=12)
    a = ap.parse_args()

    t0 = time.time()
    ads, total = scrape(a.country, a.keyword, a.rounds)
    hoy = dt.date.today()
    print("[%s | %s] leidos %d ads (Library declara %s) en %.0fs | hoy=%s"
          % (a.country, a.keyword, len(ads), total, time.time() - t0, hoy))

    for x in ads:
        x["edad"] = (hoy - x["fecha"]).days if x["fecha"] else None

    pages = {}
    for x in ads:
        k = x["page"] or "?"
        d = pages.setdefault(k, {"page": k, "total": 0, "c7": 0, "edades": [],
                                 "dest": {}, "copies": [], "dup": 0})
        d["total"] += 1
        if x["edad"] is not None and x["edad"] >= 7:
            d["c7"] += 1
            d["edades"].append(x["edad"])
        if x["dest"]:
            d["dest"][x["dest"]] = d["dest"].get(x["dest"], 0) + 1
        if x["copy"]:
            d["copies"].append(x["copy"])
        if x["dup"]:
            d["dup"] += 1

    rows = sorted(pages.values(), key=lambda d: (-d["c7"], -d["total"]))
    print("\n%-32s %4s %5s %4s  %s" % ("ANUNCIANTE", "TOT", "C7+", "DUP", "DESTINO"))
    for d in rows[:15]:
        dest = max(d["dest"].items(), key=lambda x: x[1])[0] if d["dest"] else "-"
        esc = "/".join(str(e) for e in sorted(set(d["edades"]))[:8])
        print("%-32s %4d %5d %4d  %-28s %s" % (str(d["page"])[:32], d["total"], d["c7"], d["dup"],
                                               dest[:28], esc))

    os.makedirs(SAL, exist_ok=True)
    f = os.path.join(SAL, "caza_%s_%s.json" % (a.country, re.sub(r"\W+", "_", a.keyword)[:24]))
    json.dump({"country": a.country, "keyword": a.keyword, "library_total": total,
               "leidos": len(ads), "pages": rows, "ads": ads},
              open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print("\nguardado:", f)


if __name__ == "__main__":
    main()
