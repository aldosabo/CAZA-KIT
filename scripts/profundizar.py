# -*- coding: utf-8 -*-
"""Paso 2 y 3 de la caza: arsenal por pais (page_id) + verificacion de embudo."""
import argparse
import datetime as dt
import difflib
import json
import os
import re
import sys
import unicodedata
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAL = os.path.join(BASE, "salidas")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
DEC = json.JSONDecoder()
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


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


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


def cards_of(pg):
    out = []
    for t in pg.evaluate(CARD_JS):
        i = re.search(r"Identificador de la biblioteca:\s*(\d+)", t)
        if not i:
            continue
        f = re.search(r"En circulaci[oó]n desde el ([^\n]+)", t)
        out.append({"id": i.group(1), "fecha": pdate(f.group(1)) if f else None})
    return out


def resolve_page_id(pg, country, name):
    pg.goto("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
            "&country=%s&q=%s&search_type=page&media_type=all" % (country, quote_plus(name)),
            wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(5000)
    html = pg.content()
    pares = re.findall(r'"page_id":"(\d+)","page_is_deleted":\w+,"snapshot":\{[^}]*?"page_name":"([^"]+)"', html)
    if not pares:
        pares = re.findall(r'"page_name":"([^"]+)".{0,400}?"page_id":"(\d+)"', html)
        pares = [(b, a) for a, b in pares]
    best, score = None, 0.0
    for pid, pname in pares:
        r = difflib.SequenceMatcher(None, norm(name), norm(pname)).ratio()
        if r > score:
            best, score = (pid, pname), r
    return best, score, len(pares)


def arsenal(pg, country, pid, rounds=10):
    pg.goto("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
            "&country=%s&view_all_page_id=%s&search_type=page&media_type=all" % (country, pid),
            wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(5500)
    seen = {}
    total = None
    for _ in range(rounds):
        for c in cards_of(pg):
            seen[c["id"]] = c
        if total is None:
            m = re.search(r'"search_results_connection":\{"count":(\d+)', pg.content())
            if m:
                total = int(m.group(1))
        pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(2200)
    for c in cards_of(pg):
        seen[c["id"]] = c
    return list(seen.values()), total


def embudo(pg, url):
    info = {"url": url}
    try:
        r = pg.goto(url, wait_until="domcontentloaded", timeout=45000)
        pg.wait_for_timeout(5000)
        info["status"] = r.status if r else None
        info["final_url"] = pg.url
        info["title"] = pg.title()
        txt = pg.inner_text("body")
        info["len"] = len(txt)
        info["h1"] = (pg.eval_on_selector("h1", "e => e.innerText") if pg.query_selector("h1") else "")[:120]
        info["videos"] = pg.eval_on_selector_all("video, iframe[src*='youtube'], iframe[src*='vimeo']", "e => e.length")
        info["precios"] = re.findall(r"(?:R\$|€|\$|US\$)\s?\d{1,3}(?:[.,]\d{2})?", txt)[:6]
        info["checkout"] = bool(re.search(r"(comprar|adquirir|buy now|add to cart|finalizar compra|pagar|checkout)", txt, re.I))
        info["plataforma"] = next((p for p in ("hotmart", "kiwify", "payhip", "gumroad", "stripe", "paypal",
                                               "eduzz", "braip", "cakto", "greenn", "perfect pay")
                                   if p in (txt + pg.url).lower()), None)
        info["muestra"] = re.sub(r"\s+", " ", txt)[:400]
    except Exception as e:  # noqa: BLE001
        info["error"] = repr(e)[:200]
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("name")
    ap.add_argument("--dest", default=None)
    a = ap.parse_args()
    hoy = dt.date.today()
    res = {"country": a.country, "name": a.name}

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = b.new_context(locale="es-ES", viewport={"width": 1400, "height": 1000}, user_agent=UA)
        pg = ctx.new_page()

        best, score, n = resolve_page_id(pg, a.country, a.name)
        if not best:
            print("NO se pudo resolver page_id")
            b.close()
            return
        pid, pname = best
        print("page_id resuelto: %s  (%s, similitud %.2f, %d pares)" % (pid, pname, score, n))
        res.update({"page_id": pid, "page_name": pname, "similitud": round(score, 2)})

        ads, total = arsenal(pg, a.country, pid)
        c7 = [x for x in ads if x["fecha"] and (hoy - x["fecha"]).days >= 7]
        edades = sorted(((hoy - x["fecha"]).days for x in c7), reverse=True)
        print("arsenal %s: leidos %d | library declara %s | cohorte7+ %d | edades %s"
              % (a.country, len(ads), total, len(c7), edades[:10]))
        res.update({"leidos": len(ads), "library_total": total, "cohorte7": len(c7),
                    "edades": edades[:12],
                    "link": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                            "&country=%s&view_all_page_id=%s&search_type=page&media_type=all"
                            % (a.country, pid)})

        if a.dest:
            e = embudo(pg, a.dest if a.dest.startswith("http") else "https://" + a.dest)
            print("\nEMBUDO:", json.dumps(e, ensure_ascii=False)[:900])
            res["embudo"] = e
        b.close()

    os.makedirs(SAL, exist_ok=True)
    f = os.path.join(SAL, "prof_%s_%s.json" % (a.country, re.sub(r"\W+", "_", a.name)[:22]))
    json.dump(res, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print("\nguardado:", f)


if __name__ == "__main__":
    main()
