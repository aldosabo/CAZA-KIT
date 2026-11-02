# -*- coding: utf-8 -*-
"""Búsqueda rápida de UNA keyword: tabla de anunciantes con nivel de la vara.

Uso:  python scripts/cazar_lib.py ES "logopedia" --rondas 8
Útil para tantear una keyword antes de meterla en un barrido.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("country")
    ap.add_argument("keyword")
    ap.add_argument("--rondas", type=int, default=8)
    a = ap.parse_args(argv)
    country = a.country.upper()
    with N.playwright() as p:
        b, _, pg = N.abrir_navegador(p)
        try:
            ads, total = N.buscar(pg, country, a.keyword, a.rondas)
        finally:
            b.close()
    for x in ads:
        x["mk"], x["kw"] = country, a.keyword
    pag = sorted(N.agrega(ads).values(), key=lambda d: (-d["score"], -d["c7"]))
    print("[%s | %s] %d anuncios leídos (Library declara %s), %d anunciantes"
          % (country, a.keyword, len(ads), total, len(pag)))
    print("\n%-30s %-11s %4s %4s %5s %3s  %s" % ("ANUNCIANTE", "NIVEL", "TOT", "C7+", "MAXd", "DUP", "DESTINO"))
    for d in pag[:15]:
        print("%-30s %-11s %4d %4d %5d %3d  %s [%s]" % (d["page"][:30], d["nivel"], d["n"], d["c7"], d["max"],
                                                      d["dup"], d["dest_principal"][:28], d["tipo_destino"]))
    f = os.path.join(N.SAL, "caza_%s_%s.json" % (country, N.slug(a.keyword)))
    N.guardar_json(f, {"country": country, "keyword": a.keyword, "library_total": total,
                       "leidos": len(ads), "ads": ads})
    print("\nguardado:", f)


if __name__ == "__main__":
    main()
