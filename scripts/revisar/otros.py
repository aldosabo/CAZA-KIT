# -*- coding: utf-8 -*-
"""Candidatos del ranking que aún NO se han revisado (no están en historico.csv).

Uso:  python scripts/revisar/otros.py [--min-c7 5] [--longevos 180]
"""
import argparse
import csv
import os

from _comun import N


def ya_vistos():
    f = os.path.join(N.SAL, "historico.csv")
    if not os.path.exists(f):
        return set()
    with open(f, encoding="utf-8") as fh:
        return {(r["market"], r["page"]) for r in csv.DictReader(fh)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-c7", type=int, default=5)
    ap.add_argument("--longevos", type=int, default=180, help="días para la lista de longevos")
    a = ap.parse_args(argv)
    data = N.cargar_json(os.path.join(N.SAL, "ranking.json"))
    if data is None:
        raise SystemExit("falta salidas/ranking.json: python scripts/revisar/rankear.py")
    vistos = ya_vistos()
    rows = [d for d in data if (d["market"], d["page"]) not in vistos and d["c7"] >= a.min_c7
            and d["tipo_destino"] not in N.DESCARTE_DESTINO]
    print("%-3s %-3s %-30s %-11s %5s %5s %5s %-28s %s"
          % ("#", "MK", "ANUNCIANTE", "NIVEL", "C7+", "TOT", "MAXd", "DESTINO", "COPY"))
    print("-" * 132)
    for i, d in enumerate(rows[:32], 1):
        print("%-3d %-3s %-30s %-11s %5d %5d %5d %-28s %s"
              % (i, d["market"], d["page"][:30], d["nivel"], d["c7"], d["n"], d["max"],
                 (d["dest_principal"] or "-")[:28], (d["copies"] or [""])[0][:50]))
    print("\nsin revisar con cohorte >= %d: %d (ya en histórico: %d)" % (a.min_c7, len(rows), len(vistos)))
    viejos = sorted((d for d in rows if d["max"] >= a.longevos), key=lambda x: -x["max"])
    print("\nLONGEVOS (>= %d días corriendo): %d" % (a.longevos, len(viejos)))
    for d in viejos[:14]:
        print("  %-30s %s  c7=%-3d max=%-5d %s" % (d["page"][:30], d["market"], d["c7"], d["max"],
                                                  (d["dest_principal"] or "-")[:30]))


if __name__ == "__main__":
    main()
