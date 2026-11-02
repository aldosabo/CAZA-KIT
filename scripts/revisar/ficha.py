# -*- coding: utf-8 -*-
"""Ficha de uno o varios anunciantes del ranking.

Uso:  python scripts/revisar/ficha.py "Mundo de La Costura" "Fono Aprende"
      python scripts/revisar/ficha.py --buscar costura      # coincidencia parcial
"""
import argparse
import os

from _comun import N


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("nombres", nargs="*")
    ap.add_argument("--buscar", help="texto parcial en el nombre o el destino")
    a = ap.parse_args(argv)
    data = N.cargar_json(os.path.join(N.SAL, "ranking.json"))
    if data is None:
        raise SystemExit("falta salidas/ranking.json: python scripts/revisar/rankear.py")
    obj = {n.lower() for n in a.nombres}
    q = (a.buscar or "").lower()
    hits = [d for d in data if d["page"].lower() in obj
            or (q and (q in d["page"].lower() or q in (d.get("dest_principal") or "").lower()))]
    if not hits:
        raise SystemExit("ninguno encontrado en el ranking")
    for d in hits:
        print("\n### %s  [%s]  nivel: %s" % (d["page"], d["market"], d["nivel"]))
        print("  total=%d  cohorte7+=%d  max_edad=%d  dup=%d  score=%.0f"
              % (d["n"], d["c7"], d["max"], d["dup"], d["score"]))
        print("  destino: %s (%s)" % (d["dest_principal"] or "-", d["tipo_destino"]))
        print("  keywords:", ", ".join(d["kw"][:6]))
        for c in d["copies"][:3]:
            print("   -", c[:130])
        print("  profundizar: python scripts/profundizar.py %s \"%s\"%s"
              % (d["market"], d["page"], " --dest " + d["dest_principal"] if d["dest_principal"] else ""))


if __name__ == "__main__":
    main()
