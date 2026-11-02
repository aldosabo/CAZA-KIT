# -*- coding: utf-8 -*-
"""Caza exhaustiva por oficios, secuencial y con guardado incremental.

Uso: python caza_exhaustiva.py ES IT
"""
import datetime as dt
import json
import os
import re
import sys
import time
from urllib.parse import quote_plus

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from barrido import CARD_JS, parse_card  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAL = os.path.join(BASE, "salidas")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

KEYWORDS = {
    "ES": ["logopedia", "terapia ocupacional", "fisioterapia ejercicios", "nutricionista planillas",
           "manualidades patrones", "costura moldes", "profesores de música",
           "educación especial pictogramas", "wedding planner", "contadores plantillas",
           "oposiciones temario", "profesores de yoga"],
    "IT": ["logopedia", "schede didattiche", "terapia occupazionale", "nutrizionista schede",
           "modelli cucito", "schemi cuoio", "maestri di musica", "autismo schede",
           "wedding planner", "commercialisti modelli", "preparazione concorsi", "yoga sequenze"],
    "BR": ["fonoaudiologia", "terapia ocupacional", "nutrição planilhas", "moldes costura",
           "gráficos crochê", "atividades professoras", "planilhas casamento", "apostilas concurso"],
    "MX": ["logopedia", "terapia ocupacional", "nutriólogos planillas", "manualidades moldes",
           "profesores material didáctico", "contadores plantillas", "wedding planner"],
}

ROUNDS = 4


def run_market(pg, mk):
    kws = KEYWORDS[mk]
    out = {}
    hoy = dt.date.today()
    for kw in kws:
        t0 = time.time()
        seen = {}
        total = None
        try:
            pg.goto("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                    "&country=%s&q=%s&search_type=keyword_unordered&media_type=all"
                    % (mk, quote_plus(kw)), wait_until="domcontentloaded", timeout=40000)
            pg.wait_for_timeout(4500)
            for _ in range(ROUNDS):
                for t in pg.evaluate(CARD_JS):
                    a = parse_card(t)
                    if a and a["id"] not in seen:
                        seen[a["id"]] = a
                if total is None:
                    m = re.search(r'"search_results_connection":\{"count":(\d+)', pg.content())
                    if m:
                        total = int(m.group(1))
                pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                pg.wait_for_timeout(1900)
            for t in pg.evaluate(CARD_JS):
                a = parse_card(t)
                if a and a["id"] not in seen:
                    seen[a["id"]] = a
        except Exception as e:  # noqa: BLE001
            print("  ! fallo %-24s %s" % (kw, repr(e)[:70]))
        for a in seen.values():
            a["edad"] = (hoy - a["fecha"]).days if a["fecha"] else None
            a["kw"] = kw
        out[kw] = {"total_library": total, "ads": list(seen.values())}
        # guardado incremental por keyword
        f = os.path.join(SAL, "exhaustiva_%s.json" % mk)
        json.dump(out, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        print("  [%s] %-26s ads=%-4d library=%-7s %.0fs"
              % (mk, kw[:26], len(seen), total, time.time() - t0))
    return out


def main():
    markets = [m.upper() for m in sys.argv[1:]] or ["ES", "IT"]
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = b.new_context(locale="es-ES", viewport={"width": 1400, "height": 1000}, user_agent=UA)
        pg = ctx.new_page()
        for mk in markets:
            print("== %s (%d keywords)" % (mk, len(KEYWORDS[mk])))
            run_market(pg, mk)
        b.close()
    print("== FIN")


if __name__ == "__main__":
    main()
