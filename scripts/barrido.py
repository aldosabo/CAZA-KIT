# -*- coding: utf-8 -*-
"""Barrido por keywords en un mercado, en una sola sesión de navegador.

Uso:
  python scripts/barrido.py ES "logopedia|costura moldes|wedding planner" 4
  python scripts/barrido.py IT --banco            # usa las keywords de oficio del banco
  python scripts/barrido.py ES "..." 4 --nuevo    # empieza de cero (si no, reanuda)

Guarda salidas/barrido_<PAIS>.json tras CADA keyword. Si se corta, relanzar continúa
donde se quedó (las keywords ya leídas se saltan).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N  # noqa: E402
from caza_exhaustiva import KEYWORDS  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pais", help="código de país: ES, IT, MX, BR, AR, CO...")
    ap.add_argument("keywords", nargs="?", default="", help='"kw1|kw2|kw3"')
    ap.add_argument("rondas", nargs="?", type=int, default=5, help="scrolls por keyword (4-6)")
    ap.add_argument("--banco", action="store_true", help="usar las keywords de oficio del mercado")
    ap.add_argument("--nuevo", action="store_true", help="no reanudar: sobrescribe el barrido")
    ap.add_argument("--ver", action="store_true", help="navegador visible (depurar)")
    a = ap.parse_args(argv)

    pais = a.pais.upper()
    kws = [k.strip() for k in a.keywords.split("|") if k.strip()]
    if a.banco:
        kws += [k for k in KEYWORDS.get(pais, []) if k not in kws]
    if not kws:
        ap.error("sin keywords: pásalas entre comillas separadas por | o usa --banco")

    f = os.path.join(N.SAL, "barrido_%s.json" % pais)
    if a.nuevo and os.path.exists(f):
        os.remove(f)
    print("== %s: %d keywords, %d rondas -> %s" % (pais, len(kws), a.rondas, f))
    with N.playwright() as p:
        b, _, pg = N.abrir_navegador(p, headless=not a.ver)
        try:
            res = N.barrer(pg, pais, kws, a.rondas, f)
        finally:
            b.close()
    tot = sum(len(v.get("ads", [])) for v in res.values())
    fallos = [k for k, v in res.items() if v.get("error")]
    vacias = [k for k, v in res.items() if not v.get("ads")]
    print("== %s listo: %d anuncios en %d keywords" % (pais, tot, len(res)))
    if vacias:
        print("   ! keywords sin anuncios: %s" % ", ".join(vacias))
        if len(vacias) == len(res):
            print("   ! NINGUNA trajo anuncios: mata Chrome huérfanos, revisa la red o usa --ver.")
    if fallos:
        print("   ! con error (relanza el mismo comando y se reintentan): %s" % ", ".join(fallos))
    print("siguiente: python scripts/caza_final.py")


if __name__ == "__main__":
    main()
