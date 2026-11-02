# -*- coding: utf-8 -*-
"""Rankea todos los anunciantes de los barridos con la vara, sin abrir navegador.

Uso:  python scripts/revisar/rankear.py [--mercados ES IT] [--min-nivel mirar]
Escribe salidas/ranking.json (lo usan ficha.py y otros.py).
"""
import argparse
import os

from _comun import N


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mercados", nargs="*")
    ap.add_argument("--min-nivel", default="mirar", choices=N.NIVELES)
    a = ap.parse_args(argv)
    ads = N.cargar_barridos(mercados={m.upper() for m in a.mercados} if a.mercados else None)
    if not ads:
        raise SystemExit("sin barridos en %s" % N.SAL)
    pag = N.agrega(ads)
    u = N.NIVELES.index(a.min_nivel)
    cand = sorted((d for d in pag.values() if N.NIVELES.index(d["nivel"]) >= u),
                  key=lambda d: (-d["score"], -d["c7"]))
    print("anuncios: %d | anunciantes: %d | candidatos (>= %s): %d"
          % (len(ads), len(pag), a.min_nivel, len(cand)))
    print("\n%-3s %-30s %-11s %4s %4s %5s %3s %5s  %-12s %s"
          % ("MK", "ANUNCIANTE", "NIVEL", "TOT", "C7+", "MAXd", "DUP", "SC", "TIPO", "DESTINO"))
    for d in cand[:40]:
        print("%-3s %-30s %-11s %4d %4d %5d %3d %5.0f  %-12s %s"
              % (d["market"], d["page"][:30], d["nivel"], d["n"], d["c7"], d["max"], d["dup"],
                 d["score"], d["tipo_destino"], d["dest_principal"][:30]))
    out = [{k: v for k, v in d.items() if k not in ("edades", "dest")} for d in cand]
    N.guardar_json(os.path.join(N.SAL, "ranking.json"), out)
    print("\nguardado: salidas/ranking.json (%d)" % len(out))


if __name__ == "__main__":
    main()
