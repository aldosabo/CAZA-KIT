# -*- coding: utf-8 -*-
"""Profundizar en un candidato: resuelve su page_id, cuenta su arsenal y abre la landing.

Uso:
  python scripts/profundizar.py ES "Mundo de La Costura" --dest mundodelacostura.com
  python scripts/profundizar.py ES "Mundo de La Costura" --mercados ES MX AR CO   # hueco de arbitraje

Con --mercados cuenta el arsenal del mismo page_id en varios países: donde el
anunciante NO está es donde se puede modelar.
"""
import argparse
import datetime as dt
import difflib
import os
import re
import sys
import unicodedata
from urllib.parse import quote_plus

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N  # noqa: E402


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


def mejor_par(nombre, pares):
    best, score = None, 0.0
    for pid, pname in pares:
        r = difflib.SequenceMatcher(None, norm(nombre), norm(pname)).ratio()
        if r > score:
            best, score = (pid, pname), r
    return best, score


def resolve_page_id(pg, country, name):
    pg.goto("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
            "&country=%s&q=%s&search_type=page&media_type=all" % (country, quote_plus(name)),
            wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(5000)
    html = pg.content()
    pares = re.findall(r'"page_id":"(\d+)","page_is_deleted":\w+,"snapshot":\{[^}]*?"page_name":"([^"]+)"', html)
    if not pares:
        pares = [(b, a) for a, b in re.findall(r'"page_name":"([^"]+)".{0,400}?"page_id":"(\d+)"', html)]
    best, score = mejor_par(name, pares)
    return best, score, len(pares)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("country")
    ap.add_argument("name")
    ap.add_argument("--dest", default=None, help="dominio o URL de la landing")
    ap.add_argument("--page-id", default=None, help="si ya lo conoces, se salta la resolución")
    ap.add_argument("--mercados", nargs="*", default=None, help="países donde contar el arsenal")
    ap.add_argument("--rondas", type=int, default=8)
    a = ap.parse_args(argv)
    country = a.country.upper()
    res = {"country": country, "name": a.name, "fecha": dt.date.today().isoformat()}

    with N.playwright() as p:
        b, _, pg = N.abrir_navegador(p)
        try:
            if a.page_id:
                pid, pname, score = a.page_id, a.name, 1.0
            else:
                best, score, n = resolve_page_id(pg, country, a.name)
                if not best:
                    sys.exit("No se pudo resolver page_id. Pásalo con --page-id (sale en la URL del anunciante).")
                pid, pname = best
                print("page_id: %s  (%s, similitud %.2f, %d candidatos)" % (pid, pname, score, n))
                if score < 0.6:
                    print("  ! similitud baja: comprueba que es el anunciante correcto")
            res.update(page_id=pid, page_name=pname, similitud=round(score, 2), arsenal={})

            for mk in [m.upper() for m in (a.mercados or [country])]:
                url = N.LIBRARY_PAGE.format(country=mk, pid=pid)
                ads, total = N.buscar(pg, mk, "", a.rondas, url=url)
                edades = sorted((x["edad"] for x in ads if x["edad"] is not None and x["edad"] >= 7),
                                reverse=True)
                niv = N.nivel(len(edades), edades[0] if edades else 0,
                              sum(1 for x in ads if x["dup"]))
                print("arsenal %s: %d leídos | library %s | cohorte7+ %d | nivel %s | edades %s"
                      % (mk, len(ads), total, len(edades), niv, edades[:8]))
                res["arsenal"][mk] = {"leidos": len(ads), "library_total": total, "cohorte7": len(edades),
                                      "nivel": niv, "edades": edades[:12], "link": url}
            if a.mercados:
                vacios = [m for m, v in res["arsenal"].items() if not v["leidos"]]
                if vacios:
                    print("hueco de arbitraje (no anuncia allí): %s" % ", ".join(vacios))
                res["hueco"] = vacios

            if a.dest:
                e = N.abrir_landing(b, a.dest if a.dest.startswith("http") else "https://" + a.dest)
                print("\nEMBUDO: %s · %s — %s" % (e.get("veredicto"),
                                                e.get("tipo"), e.get("motivo")))
                print("  %s | precios: %s | plataforma: %s"
                      % (e.get("title", ""), e.get("precios"), e.get("plataforma")))
                res["embudo"] = e
        finally:
            b.close()

    f = os.path.join(N.SAL, "prof_%s_%s.json" % (country, N.slug(a.name, 22)))
    N.guardar_json(f, res)
    print("\nguardado:", f)


if __name__ == "__main__":
    main()
