# -*- coding: utf-8 -*-
"""Caza exhaustiva por oficios: varios mercados seguidos, un solo navegador.

Uso:  python scripts/caza_exhaustiva.py ES IT       (por defecto ES IT)
      python scripts/caza_exhaustiva.py BR --rondas 5

Guarda salidas/exhaustiva_<PAIS>.json tras cada keyword y reanuda si se relanza.
Las keywords siguen la regla 70 % oficio / 20 % formato / 10 % plataforma.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N  # noqa: E402

KEYWORDS = {
    "ES": ["logopedia", "terapia ocupacional", "fisioterapia ejercicios", "nutricionista plantillas",
           "manualidades patrones", "costura moldes", "profesores de música",
           "educación especial pictogramas", "wedding planner", "contadores plantillas",
           "oposiciones temario", "profesores de yoga",
           "fichas imprimibles", "cuadernillo actividades", "hotmart"],
    "IT": ["logopedia", "schede didattiche", "terapia occupazionale", "nutrizionista schede",
           "modelli cucito", "schemi cuoio", "maestri di musica", "autismo schede",
           "wedding planner", "commercialisti modelli", "preparazione concorsi", "yoga sequenze",
           "schede stampabili", "quaderno attività", "payhip"],
    "BR": ["fonoaudiologia", "terapia ocupacional", "nutrição planilhas", "moldes costura",
           "gráficos crochê", "atividades professoras", "planilhas casamento", "apostilas concurso",
           "caderno de atividades", "kiwify"],
    "MX": ["logopedia", "terapia ocupacional", "nutriólogos planillas", "manualidades moldes",
           "profesores material didáctico", "contadores plantillas", "wedding planner",
           "fichas imprimibles", "hotmart"],
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mercados", nargs="*", default=["ES", "IT"])
    ap.add_argument("--rondas", type=int, default=4)
    ap.add_argument("--ver", action="store_true")
    a = ap.parse_args(argv)
    mercados = [m.upper() for m in a.mercados]
    desconocidos = [m for m in mercados if m not in KEYWORDS]
    if desconocidos:
        ap.error("sin banco para %s (hay: %s). Usa barrido.py con tus keywords."
                 % (", ".join(desconocidos), ", ".join(KEYWORDS)))
    with N.playwright() as p:
        b, _, pg = N.abrir_navegador(p, headless=not a.ver)
        try:
            for mk in mercados:
                print("== %s (%d keywords)" % (mk, len(KEYWORDS[mk])))
                N.barrer(pg, mk, KEYWORDS[mk], a.rondas, os.path.join(N.SAL, "exhaustiva_%s.json" % mk))
        finally:
            b.close()
    print("== FIN. Siguiente: python scripts/caza_final.py")


if __name__ == "__main__":
    main()
