# -*- coding: utf-8 -*-
"""Hueco de arbitraje: quien compite en el mercado destino y con que antiguedad."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for mk in ("ES", "MX"):
    f = os.path.join(BASE, "salidas", "barrido_%s.json" % mk)
    if not os.path.exists(f):
        print("falta", f)
        continue
    data = json.load(open(f, encoding="utf-8"))
    pages = {}
    n = 0
    for kw, blk in data.items():
        for a in blk["ads"]:
            n += 1
            k = a.get("page") or "?"
            d = pages.setdefault(k, {"tot": 0, "c7": 0, "ages": [], "dest": {}, "copy": []})
            d["tot"] += 1
            e = a.get("edad")
            if e is not None and e >= 7:
                d["c7"] += 1
                d["ages"].append(e)
            if a.get("dest"):
                d["dest"][a["dest"]] = d["dest"].get(a["dest"], 0) + 1
            if a.get("copy"):
                d["copy"].append(a["copy"][:80])
    print("\n=== %s: %d anuncios, %d anunciantes con anuncios en 'planner/agenda tdah'" % (mk, n, len(pages)))
    for k, d in sorted(pages.items(), key=lambda x: -x[1]["c7"])[:10]:
        dest = max(d["dest"].items(), key=lambda x: x[1])[0] if d["dest"] else "-"
        print("  %-30s tot=%-3d c7+=%-3d max=%-4s %-26s | %s"
              % (str(k)[:30], d["tot"], d["c7"], max(d["ages"]) if d["ages"] else "-",
                 dest[:26], (d["copy"][0] if d["copy"] else "")[:60]))

