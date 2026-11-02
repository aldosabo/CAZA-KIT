# -*- coding: utf-8 -*-
"""Lista los candidatos del ranking que no salieron en el informe, ordenados por señal."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data = json.load(open(os.path.join(BASE, "salidas", "ranking.json"), encoding="utf-8"))

YA_VISTOS = {
    "Planner Sem Caos TDAH", "Crocheteca", "Avelune Crochet Patterns", "edu.sogno",
    "Mindfulness Educators Italia", "LacariaRicami.Store", "Gold City Ventures", "Jessa",
    "Shelby Sapp", "Victor Pareto", "felipetitto con Meu Assessor",
}

MIN_C7 = 5
rows = []
for d in data:
    if d["page"] in YA_VISTOS:
        continue
    if d["c7"] < MIN_C7:
        continue
    if d["digital"] < d["retail"]:
        continue
    rows.append(d)

rows.sort(key=lambda d: (-d["score"], -d["c7"]))

print("%-3s %-3s %-30s %5s %5s %5s %-28s %s" % ("#", "MK", "ANUNCIANTE", "C7+", "TOT", "MAXd", "DESTINO", "COPY"))
print("-" * 132)
for i, d in enumerate(rows[:32], 1):
    copy = (d["copies"][0][:58] if d["copies"] else "")
    print("%-3d %-3s %-30s %5d %5d %5d %-28s %s"
          % (i, d["market"], str(d["page"])[:30], d["c7"], d["total"], d["max_age"],
             (d["dest_principal"] or "-")[:28], copy))

print("\ntotal con señal digital y cohorte >= %d: %d" % (MIN_C7, len(rows)))

# longevos: la señal más dura
viejos = [d for d in rows if d["max_age"] >= 180]
print("\nLONGEVOS (>= 180 días corriendo):", len(viejos))
for d in sorted(viejos, key=lambda x: -x["max_age"])[:14]:
    print("  %-30s %s  c7=%-3d max=%-5d %-26s %s"
          % (str(d["page"])[:30], d["market"], d["c7"], d["max_age"],
             (d["dest_principal"] or "-")[:26], (d["copies"][0][:50] if d["copies"] else "")))

