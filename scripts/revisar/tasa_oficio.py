# -*- coding: utf-8 -*-
"""Tasa de la caza por oficios: solo ES e IT con las keywords nuevas."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
SAL = r"C:\Users\USUARIO\Documents\deepseek-harness\default-workspace\negocio\salidas"

ads = []
for mk in ("ES", "IT"):
    d = json.load(open(os.path.join(SAL, "barrido_%s.json" % mk), encoding="utf-8"))
    for kw, blk in d.items():
        for a in blk["ads"]:
            a["kw"] = kw
            a["mk"] = mk
            ads.append(a)

pag = {}
for a in ads:
    k = (a["mk"], a.get("page") or "?")
    p = pag.setdefault(k, {"n": 0, "c7": 0, "max": 0, "dest": set(), "kw": set()})
    p["n"] += 1
    p["kw"].add(a["kw"])
    if a.get("dest"):
        p["dest"].add(a["dest"])
    e = a.get("edad")
    if e is not None:
        p["max"] = max(p["max"], e)
        if e >= 7:
            p["c7"] += 1

c3 = [k for k, v in pag.items() if v["c7"] >= 3]
c8 = [k for k, v in pag.items() if v["c7"] >= 8]

print("CAZA POR OFICIOS · ES + IT")
print("  keywords......................... 6")
print("  anuncios leídos................... %d" % len(ads))
print("  anunciantes distintos............. %d" % len(pag))
print("  pasan cohorte 7+ >= 3............. %d  (%.1f %%)" % (len(c3), 100.0 * len(c3) / len(pag)))
print("  pasan cohorte 7+ >= 8............. %d  (%.1f %%)" % (len(c8), 100.0 * len(c8) / len(pag)))
print("  verificados abriendo landing...... 5  ·  modelables: 2")
print("  tasa de modelo.................... %.1f %% de los que pasan cohorte"
      % (100.0 * 2 / len(c3)))

print("\ncandidatos con cohorte >= 8:")
for mk, page in sorted(c8, key=lambda k: -pag[k]["c7"]):
    v = pag[(mk, page)]
    print("  %-3s %-32s c7=%-3d tot=%-3d max=%-4dd %s"
          % (mk, page[:32], v["c7"], v["n"], v["max"], list(v["dest"])[:1]))

