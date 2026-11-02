# -*- coding: utf-8 -*-
"""Rankea los anunciantes de los barridos y separa infoproducto de retail."""
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAL = os.path.join(BASE, "salidas")

PLATAFORMAS = ("hotmart", "kiwify", "payhip", "gumroad", "braip", "cakto", "greenn",
               "eduzz", "perfectpay", "perfect pay", "learnworlds", "teachable", "kajabi",
               "cartpanda", "yampi", "systeme.io", "stan.store", "beacons.ai", "linktr.ee",
               "netlify", "vercel", "notion.site", "herospark", "leadlovers", "memberkit",
               "kiwify.app", "ticto", "pepper", "hubla", "paggrav", "zaper", "vindi")

RETAIL = ("amazon", "shein", "shopee", "mercadolivre", "aliexpress", "magazineluiza",
          "play.google", "apps.apple", "itunes.apple", "tiktok", "instagram", "facebook.com",
          "whatsapp", "tokstok", "hobbii", "ikea", "temu", "ebay", "walmart", "target",
          "leroy", "mercadolibre", "americanas", "casasbahia", "carrefour", "kabum",
          "etsy", "temu.com", "shopify.com", "shop.app")

DIGITAL_RE = re.compile(
    r"\b(pdf|e-?book|ebook|apostila|planilha|template|modelo|guia|m[eé]todo|metodo|curso|"
    r"treinamento|desafio|challenge|blueprint|printable|printables|planner|checklist|"
    r"protocol|protocolo|receita|receitas|programa|manual|kit|pack|pack de|curso online|"
    r"acesso|aula|aulas|workshop|masterclass|formazione|ricettario)\b", re.I)

MIN_C7 = 3


def clasifica(a):
    dest = (a.get("dest") or "").lower()
    copy = (a.get("copy") or "")
    if dest and any(r in dest for r in RETAIL):
        return "retail"
    if dest and any(p in dest for p in PLATAFORMAS):
        return "digital"
    if DIGITAL_RE.search(copy):
        return "digital"
    return "dudoso"


def main():
    files = sorted(glob.glob(os.path.join(SAL, "barrido_*.json")))
    if not files:
        print("sin barridos")
        return
    paginas = {}
    total_ads = 0
    for f in files:
        data = json.load(open(f, encoding="utf-8"))
        market = os.path.basename(f).replace("barrido_", "").replace(".json", "")
        for kw, blk in data.items():
            for a in blk.get("ads", []):
                total_ads += 1
                k = (market, a.get("page") or "?")
                d = paginas.setdefault(k, {"market": market, "page": k[1], "total": 0, "c7": 0,
                                           "ages": [], "dup": 0, "dest": {}, "copies": [],
                                           "kws": set(), "clases": {}})
                d["total"] += 1
                d["kws"].add(kw)
                e = a.get("edad")
                if e is not None and e >= 7:
                    d["c7"] += 1
                    d["ages"].append(e)
                if a.get("dup"):
                    d["dup"] += 1
                if a.get("dest"):
                    d["dest"][a["dest"]] = d["dest"].get(a["dest"], 0) + 1
                if a.get("copy"):
                    d["copies"].append(a["copy"])
                c = clasifica(a)
                d["clases"][c] = d["clases"].get(c, 0) + 1

    print("anuncios totales:", total_ads, "| paginas:", len(paginas))

    for d in paginas.values():
        dig = d["clases"].get("digital", 0)
        ret = d["clases"].get("retail", 0)
        d["digital"] = dig
        d["retail"] = ret
        d["max_age"] = max(d["ages"]) if d["ages"] else 0
        d["dest_principal"] = max(d["dest"].items(), key=lambda x: x[1])[0] if d["dest"] else ""
        # score: cohorte + longevidad + duplicacion + senal digital - penalizacion retail
        s = d["c7"] * 1.0
        s += 40 if d["max_age"] >= 45 else (15 if d["max_age"] >= 21 else 0)
        s += min(d["dup"], 12) * 2
        s += min(dig, 10) * 1.5
        s -= ret * 2
        if ret > dig:
            s -= 25
        d["score"] = s

    cand = [d for d in paginas.values() if d["c7"] >= MIN_C7 and d["digital"] >= 1 and d["digital"] >= d["retail"]]
    cand.sort(key=lambda d: -d["score"])

    print("\n%-4s %-30s %4s %5s %5s %5s %5s  %s" % ("MK", "ANUNCIANTE", "TOT", "C7+", "MAXd", "DUP", "SC", "DESTINO"))
    for d in cand[:30]:
        print("%-4s %-30s %4d %5d %5d %5d %5.0f  %s"
              % (d["market"], str(d["page"])[:30], d["total"], d["c7"], d["max_age"],
                 d["dup"], d["score"], d["dest_principal"][:30]))

    print("\n=== por mercado ===")
    for mk in sorted({d["market"] for d in cand}):
        top = [d for d in cand if d["market"] == mk][:6]
        print("\n[%s] %d paginas digitales" % (mk, len([d for d in cand if d["market"] == mk])))
        for d in top:
            ej = (d["copies"][0][:70] if d["copies"] else "")
            print("  %-28s c7=%-3d max=%-4d dup=%-2d %-26s | %s"
                  % (str(d["page"])[:28], d["c7"], d["max_age"], d["dup"],
                     d["dest_principal"][:26], ej))

    out = []
    for d in cand:
        out.append({k: (sorted(v) if isinstance(v, set) else v) for k, v in d.items()})
    json.dump(out, open(os.path.join(SAL, "ranking.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nguardado: salidas/ranking.json  (%d candidatos)" % len(cand))


if __name__ == "__main__":
    main()

