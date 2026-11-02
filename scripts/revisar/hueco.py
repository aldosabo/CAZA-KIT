# -*- coding: utf-8 -*-
"""Hueco de arbitraje: quién compite ya en un mercado destino para una keyword.

Uso:  python scripts/revisar/hueco.py ES MX --kw "planner tdah"
      python scripts/revisar/hueco.py MX                    # todas las keywords del barrido

Lee los barridos del mercado. Vara: 0-3 competidores con cohorte = hueco; 50+ ads de
uno solo = whale, no entrar.
"""
import argparse

from _comun import N


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mercados", nargs="+")
    ap.add_argument("--kw", help="filtra anuncios cuya keyword o copy contenga este texto")
    a = ap.parse_args(argv)
    for mk in (m.upper() for m in a.mercados):
        ads = N.cargar_barridos(mercados={mk})
        if a.kw:
            q = a.kw.lower()
            ads = [x for x in ads if q in (x.get("kw") or "").lower() or q in (x.get("copy") or "").lower()]
        if not ads:
            print("\n=== %s: sin anuncios%s" % (mk, " para '%s'" % a.kw if a.kw else ""))
            continue
        pag = N.agrega(ads)
        comp = [d for d in pag.values() if d["c7"] >= N.VARA["c7"][0]]
        whale = [d for d in pag.values() if d["n"] >= N.WHALE]
        veredicto = ("WHALE: nicho con dueño" if whale else
                     "HUECO: 0-1 competidores con cohorte" if len(comp) <= 1 else
                     "entrable: 2-3 competidores" if len(comp) <= 3 else
                     "saturado: %d competidores con cohorte" % len(comp))
        print("\n=== %s: %d anuncios, %d anunciantes, %d con cohorte → %s"
              % (mk, len(ads), len(pag), len(comp), veredicto))
        for d in sorted(pag.values(), key=lambda x: -x["c7"])[:10]:
            print("  %-30s tot=%-3d c7+=%-3d max=%-4s %-26s | %s"
                  % (d["page"][:30], d["n"], d["c7"], d["max"] or "-", (d["dest_principal"] or "-")[:26],
                     (d["copies"] or [""])[0][:60]))


if __name__ == "__main__":
    main()
