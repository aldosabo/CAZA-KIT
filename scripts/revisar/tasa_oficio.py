# -*- coding: utf-8 -*-
"""Tasas de la caza (vara §5), calculadas de los datos, nada escrito a mano.

Uso:  python scripts/revisar/tasa_oficio.py [--mercados ES IT]

tasa de señal  = anunciantes con cohorte >= 3 / anunciantes leídos
tasa de modelo = modelables verificados / candidatos verificados
Compara con la caza anterior registrada en salidas/tasas.csv y dice si el método mejoró.
"""
import argparse
import csv
import datetime as dt
import os

from _comun import N


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mercados", nargs="*")
    ap.add_argument("--no-guardar", action="store_true")
    a = ap.parse_args(argv)
    mercados = {m.upper() for m in a.mercados} if a.mercados else None
    ads = N.cargar_barridos(mercados=mercados)
    if not ads:
        raise SystemExit("sin barridos en %s" % N.SAL)
    pag = N.agrega(ads)
    niveles = {n: sum(1 for d in pag.values() if d["nivel"] == n) for n in N.NIVELES}
    c3 = sum(1 for d in pag.values() if d["c7"] >= N.VARA["c7"][0])
    fin = N.cargar_json(os.path.join(N.SAL, "caza_final.json"), {}) or {}
    ver = [v for v in fin.get("verificados", []) if not mercados or v["market"] in mercados]
    mod = sum(1 for v in ver if v.get("veredicto") == "modelable")
    t = N.tasas(len(pag), c3, len(ver), mod)
    kws = sorted({x.get("kw") for x in ads if x.get("kw")})

    print("CAZA · %s" % ", ".join(sorted({d["market"] for d in pag.values()})))
    print("  keywords......................... %d" % len(kws))
    print("  anuncios leídos.................. %d" % len(ads))
    print("  anunciantes distintos............ %d" % len(pag))
    for n in N.NIVELES[1:]:
        print("  nivel %-12s................ %d" % (n, niveles[n]))
    print("  verificados abriendo landing..... %d  ·  modelables: %d" % (len(ver), mod))
    print("  TASA DE SEÑAL.................... %.2f %%" % t["tasa_senal"])
    print("  TASA DE MODELO................... %.1f %%" % t["tasa_modelo"])

    # rendimiento por keyword: qué keywords traen señal (para podar el banco)
    por_kw = {}
    for d in pag.values():
        for k in d["kw"]:
            s = por_kw.setdefault(k, [0, 0])
            s[0] += 1
            s[1] += d["c7"] >= N.VARA["c7"][0]
    print("\nkeywords por señal (anunciantes con cohorte / anunciantes):")
    for k, (n, c) in sorted(por_kw.items(), key=lambda x: (-x[1][1], -x[1][0]))[:20]:
        print("  %-30s %3d/%-3d %s" % (k[:30], c, n, "← podar" if n >= 10 and c == 0 else ""))

    f = os.path.join(N.SAL, "tasas.csv")
    previa = None
    if os.path.exists(f):
        with open(f, encoding="utf-8") as fh:
            filas = list(csv.DictReader(fh))
            previa = filas[-1] if filas else None
    if previa:
        ms = t["tasa_senal"] > float(previa["tasa_senal"])
        mm = t["tasa_modelo"] > float(previa["tasa_modelo"])
        print("\nvs caza anterior (%s): señal %s %s · modelo %s %s → %s"
              % (previa["fecha"], previa["tasa_senal"], "↑" if ms else "=/↓",
                 previa["tasa_modelo"], "↑" if mm else "=/↓",
                 "el cambio de método SIRVIÓ" if ms or mm else "el cambio de método NO sirvió"))
    if not a.no_guardar:
        nuevo = not os.path.exists(f)
        with open(f, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if nuevo:
                w.writerow(["fecha", "mercados", "anuncios", "anunciantes", "cohorte", "verificados",
                            "modelables", "tasa_senal", "tasa_modelo"])
            w.writerow([dt.date.today().isoformat(), " ".join(sorted({d["market"] for d in pag.values()})),
                        len(ads), len(pag), c3, len(ver), mod, t["tasa_senal"], t["tasa_modelo"]])


if __name__ == "__main__":
    main()
