# -*- coding: utf-8 -*-
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data = json.load(open(os.path.join(BASE, "salidas", "ranking.json"), encoding="utf-8"))

objetivo = ["Mia Academy", "edu.sogno", "Mindfulness Educators Italia", "Jessa", "Shelby Sapp",
            "Aha Printables", "Gold City Ventures", "Planner Sem Caos TDAH", "Business Explained",
            "Unione Professionisti", "Everand"]

for d in data:
    if d["page"] not in objetivo:
        continue
    print("\n### %s  [%s]" % (d["page"], d["market"]))
    print("  total=%d  cohorte7+=%d  max_edad=%d  dup=%d  dest=%s"
          % (d["total"], d["c7"], d["max_age"], d["dup"], d["dest_principal"]))
    print("  keywords:", ", ".join(d["kws"][:6]))
    print("  clases:", d["clases"])
    for c in d["copies"][:3]:
        print("   -", c[:130])

