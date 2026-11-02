# -*- coding: utf-8 -*-
"""Barrido multi-nicho: muchas keywords por mercado en una sola sesion de navegador.

Uso:  python barrido.py BR "ebook|planilha|método|receitas|renda extra"
Guarda un JSON por keyword y uno agregado por mercado.
"""
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
MES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
       "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12,
       "jan": 1, "apr": 4, "aug": 8, "dec": 12}

CARD_JS = """() => {
  const spans = [...document.querySelectorAll('span')]
    .filter(s => (s.textContent || '').startsWith('Identificador de la biblioteca'));
  const out = [];
  for (const s of spans) {
    let n = s, card = null;
    for (let i = 0; i < 14 && n; i++) {
      n = n.parentElement; if (!n) break;
      const t = n.innerText || '';
      if (t.includes('Ver detalles') && t.length > 120) { card = n; break; }
    }
    if (card) out.push(card.innerText);
  }
  return out;
}"""


def pdate(s):
    s = s.strip().lower().replace("de ", "")
    m = re.match(r"(\d{1,2})\s+([a-z]+)\.?\s+(\d{4})", s)
    if not m:
        return None
    mes = m.group(2)[:4]
    for k, v in MES.items():
        if mes.startswith(k):
            return dt.date(int(m.group(3)), v, int(m.group(1)))
    return None


def parse_card(txt):
    i = re.search(r"Identificador de la biblioteca:\s*(\d+)", txt)
    if not i:
        return None
    f = re.search(r"En circulaci[oó]n desde el ([^\n]+)", txt)
    p = re.search(r"Ver detalles[^\n]*\n([^\n]+)\nPublicidad", txt)
    dom = re.search(r"\n([A-Z0-9][A-Z0-9.\-]{3,}\.[A-Z]{2,})\n", txt)
    cp = re.search(r"\nPublicidad\n([^\n]+)", txt)
    return {"id": i.group(1),
            "fecha": pdate(f.group(1)) if f else None,
            "page": p.group(1).strip() if p else None,
            "dest": dom.group(1).lower() if dom else None,
            "copy": cp.group(1).strip()[:170] if cp else None,
            "dup": ("varias versiones" in txt) or ("varios anuncios" in txt)}


def run(country, kws, rounds=9):
    out = {}
    hoy = dt.date.today()
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = b.new_context(locale="es-ES", viewport={"width": 1400, "height": 1000}, user_agent=UA)
        pg = ctx.new_page()
        for kw in kws:
            t0 = time.time()
            seen = {}
            total = None
            try:
                pg.goto("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                        "&country=%s&q=%s&search_type=keyword_unordered&media_type=all"
                        % (country, quote_plus(kw)), wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_timeout(5500)
                for _ in range(rounds):
                    for t in pg.evaluate(CARD_JS):
                        a = parse_card(t)
                        if a and a["id"] not in seen:
                            seen[a["id"]] = a
                    if total is None:
                        m = re.search(r'"search_results_connection":\{"count":(\d+)', pg.content())
                        if m:
                            total = int(m.group(1))
                    pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                    pg.wait_for_timeout(2100)
                for t in pg.evaluate(CARD_JS):
                    a = parse_card(t)
                    if a and a["id"] not in seen:
                        seen[a["id"]] = a
            except Exception as e:  # noqa: BLE001
                print("  ! fallo %s: %s" % (kw, repr(e)[:90]))
            for a in seen.values():
                a["edad"] = (hoy - a["fecha"]).days if a["fecha"] else None
                a["kw"] = kw
                a["country"] = country
            out[kw] = {"total_library": total, "ads": list(seen.values())}
            # guardado incremental: si se cuelga, no se pierde lo anterior
            try:
                os.makedirs(SAL, exist_ok=True)
                json.dump(out, open(os.path.join(SAL, "barrido_%s.json" % country), "w",
                                    encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
            except Exception:
                pass
            print("  [%s] %-20s ads=%-4d library=%-7s %.0fs"
                  % (country, kw, len(seen), total, time.time() - t0))
        b.close()
    return out


if __name__ == "__main__":
    country = sys.argv[1]
    kws = [k.strip() for k in sys.argv[2].split("|") if k.strip()]
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 9
    print("== %s: %d keywords, %d rondas" % (country, len(kws), rounds))
    res = run(country, kws, rounds)
    os.makedirs(SAL, exist_ok=True)
    f = os.path.join(SAL, "barrido_%s.json" % country)
    json.dump(res, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    tot = sum(len(v["ads"]) for v in res.values())
    print("== %s listo: %d anuncios en %d keywords -> %s" % (country, tot, len(res), f))
