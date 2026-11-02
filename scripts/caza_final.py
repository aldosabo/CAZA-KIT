# -*- coding: utf-8 -*-
"""Caza final: une todos los barridos por oficio, rankea y verifica embudos."""
import glob
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAL = os.path.join(BASE, "salidas")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

RETAIL = ("amazon", "shein", "shopee", "mercadolivre", "aliexpress", "mercadolibre", "temu",
          "ebay", "walmart", "target", "etsy", "ikea", "leroy", "carrefour", "americanas",
          "play.google", "apps.apple", "itunes", "tiktok", "instagram", "facebook.com",
          "whatsapp", "adobe", "canva", "spagna", "confprofessioni")

MIN_C7, TOP = 5, 10


def fuentes():
    for f in glob.glob(os.path.join(SAL, "exhaustiva_*.json")) + \
             [os.path.join(SAL, "barrido_ES.json"), os.path.join(SAL, "barrido_IT.json")]:
        if os.path.exists(f):
            yield os.path.basename(f), json.load(open(f, encoding="utf-8"))


def agrega():
    ads, pag = {}, {}
    for nombre, data in fuentes():
        mk = nombre.split("_")[1].split(".")[0]
        for kw, blk in data.items():
            for a in blk.get("ads", []):
                if a.get("id") in ads:
                    continue
                ads[a.get("id")] = 1
                k = (mk, a.get("page") or "?")
                d = pag.setdefault(k, {"n": 0, "c7": 0, "ages": [], "dest": {}, "dup": 0,
                                       "copy": [], "kw": set()})
                d["n"] += 1
                d["kw"].add(kw)
                e = a.get("edad")
                if e is not None and e >= 7:
                    d["c7"] += 1
                    d["ages"].append(e)
                if a.get("dup"):
                    d["dup"] += 1
                if a.get("dest"):
                    d["dest"][a["dest"]] = d["dest"].get(a["dest"], 0) + 1
                if a.get("copy"):
                    d["copy"].append(a["copy"])
    return ads, pag


def clases(pg, url):
    d = {"url": url}
    ctx = pg.context.browser.new_context(locale="es-ES", viewport={"width": 1280, "height": 900},
                                         user_agent=UA)
    p2 = ctx.new_page()
    ok = False
    for u in (url, url.replace("https://www.", "https://"), url.replace("https://", "https://www.")):
        try:
            r = p2.goto(u, wait_until="domcontentloaded", timeout=25000)
            ok = True
            break
        except Exception:
            continue
    try:
        if not ok:
            raise RuntimeError("no resuelve")
        p2.wait_for_timeout(3000)
        txt = re.sub(r"\s+", " ", p2.inner_text("body"))
        d["title"] = p2.title()[:70]
        d["precios"] = re.findall(r"(?:R\$|€|\$|US\$)\s?\d{1,3}(?:[.,]\d{2})?", txt)[:3]
        d["descarga"] = bool(re.search(r"(descarg|inmediat|download|immediat)", txt, re.I))
        d["checkout"] = bool(re.search(r"(comprar|acquista|buy now|add to cart|checkout|carrito|"
                                       r"iscriviti|inscr[ií]bete|pagar|precio)", txt, re.I))
        d["curso"] = bool(re.search(r"(curso|videolez|lezioni|lecciones|moduli|m[oó]dulos|classi|"
                                    r"talleres|workshop)", txt, re.I))
        d["pdf"] = bool(re.search(r"\bpdf\b|imprimible|stampabil|printable|fichas|schede", txt, re.I))
        d["muestra"] = txt[:130]
    except Exception as e:  # noqa: BLE001
        d["error"] = repr(e)[:80]
    try:
        ctx.close()
    except Exception:
        pass
    return d


def main():
    ads, pag = agrega()
    print("anuncios únicos: %d | anunciantes: %d" % (len(ads), len(pag)))

    cands = []
    for (mk, page), d in pag.items():
        dest = max(d["dest"].items(), key=lambda x: x[1])[0] if d["dest"] else ""
        if d["c7"] < MIN_C7 or not dest or any(r in dest for r in RETAIL):
            continue
        cands.append({"market": mk, "page": page, "c7": d["c7"], "n": d["n"],
                      "max": max(d["ages"]) if d["ages"] else 0, "dup": d["dup"], "dest": dest,
                      "copy": d["copy"][0][:70] if d["copy"] else "", "kw": sorted(d["kw"])[:2]})
    cands.sort(key=lambda x: (-x["c7"], -x["max"]))
    tot_c3 = sum(1 for (mk, p), d in pag.items() if d["c7"] >= 3)

    print("\n%-3s %-28s %4s %4s %5s %3s %-30s %s"
          % ("MK", "ANUNCIANTE", "C7+", "TOT", "MAXd", "DUP", "DESTINO", "COPY"))
    print("-" * 140)
    for c in cands[:24]:
        print("%-3s %-28s %4d %4d %5d %3d %-30s %s"
              % (c["market"], c["page"][:28], c["c7"], c["n"], c["max"], c["dup"],
                 c["dest"][:30], c["copy"]))
    print("\ncon cohorte>=3: %d de %d (%.1f %%) | con destino y cohorte>=%d: %d"
          % (tot_c3, len(pag), 100.0 * tot_c3 / len(pag), MIN_C7, len(cands)))

    verif = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        pg = b.new_page()
        for c in cands[:TOP]:
            url = c["dest"] if c["dest"].startswith("http") else "https://" + c["dest"]
            d = clases(pg, url)
            d.update({k: c[k] for k in ("page", "market", "c7", "max", "dup", "copy")})
            verif.append(d)
            if "error" in d:
                print("\n### %-26s [%s] c7=%d  ERROR: %s" % (c["page"][:26], c["market"], c["c7"], d["error"]))
            else:
                tipo = ("INFOPRODUCTO" if (d["descarga"] or d["pdf"]) and d["checkout"]
                        else "formación" if d["curso"] else "sin oferta clara")
                print("\n### %-26s [%s] c7=%d max=%dd dup=%d  → %s"
                      % (c["page"][:26], c["market"], c["c7"], c["max"], c["dup"], tipo))
                print("    %s | precios=%s" % (d.get("title", "")[:64], d["precios"]))
                print("    >", d["muestra"][:120])
        b.close()

    ok = [d for d in verif if "error" not in d]
    info = [d for d in ok if (d["descarga"] or d["pdf"]) and d["checkout"]]
    print("\nVERIFICADOS %d/%d | infoproducto claro: %d | tasa de modelo: %.0f %% de los verificados"
          % (len(ok), len(verif), len(info), 100.0 * len(info) / max(len(verif), 1)))

    json.dump({"candidatos": cands, "verificados": verif},
              open(os.path.join(SAL, "caza_final.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("guardado: salidas/caza_final.json")


if __name__ == "__main__":
    main()
