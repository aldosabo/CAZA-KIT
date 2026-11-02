# -*- coding: utf-8 -*-
"""Caza final: une todos los barridos, aplica la vara, abre las landings y decide.

Uso:
  python scripts/caza_final.py                 # todos los mercados, verifica el top 10
  python scripts/caza_final.py --top 15 --mercados ES IT
  python scripts/caza_final.py --sin-verificar # solo ranking, sin navegador

Lee salidas/barrido_*.json y salidas/exhaustiva_*.json.
Escribe salidas/caza_final.json, salidas/caza_final.md (informe) y añade al
salidas/historico.csv una línea por candidato verificado con su motivo.
"""
import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as N  # noqa: E402

ICONO = {"modelable": "✅", "dudoso": "⚠️", "descartado": "❌"}


def candidatos(pag, min_nivel="mirar"):
    umbral = N.NIVELES.index(min_nivel)
    out, descartes = [], {}
    for d in pag.values():
        if N.NIVELES.index(d["nivel"]) < umbral:
            continue
        if d["tipo_destino"] in N.DESCARTE_DESTINO:
            m = N.DESCARTE_DESTINO[d["tipo_destino"]]
            descartes[m] = descartes.get(m, 0) + 1
            continue
        out.append(d)
    out.sort(key=lambda d: (-d["score"], -d["c7"]))
    return out, descartes


def whales(pag):
    """Anunciante con 50+ anuncios en un mercado: nicho con dueño (vara §3)."""
    return sorted((d for d in pag.values() if d["n"] >= N.WHALE), key=lambda d: -d["n"])


def informe_md(res):
    t, L = res["tasas"], []
    L.append("# Caza final — %s\n" % res["fecha"])
    L.append("- Anuncios únicos: **%d** · anunciantes: **%d** · mercados: %s"
             % (res["anuncios"], res["anunciantes"], ", ".join(res["mercados"])))
    L.append("- Con cohorte ≥ 3: **%d** · candidatos tras descartes de destino: **%d**"
             % (res["con_cohorte"], len(res["candidatos"])))
    L.append("- Verificados: **%d** · modelables: **%d**" % (len(res["verificados"]), res["modelables"]))
    L.append("- **Tasa de señal %.2f %% · tasa de modelo %.1f %%**\n" % (t["tasa_senal"], t["tasa_modelo"]))
    if res["verificados"]:
        L.append("## Verificados\n")
        L.append("| | Mk | Anunciante | Nivel | C7+ | Máx días | Destino | Precio | Motivo |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for v in res["verificados"]:
            L.append("| %s | %s | %s | %s | %d | %d | %s | %s | %s |"
                     % (ICONO.get(v["veredicto"], ""), v["market"], v["page"].replace("|", "/"),
                        v["nivel"], v["c7"], v["max"], v["dest"], v.get("precio", ""), v["motivo"]))
    L.append("\n## Top candidatos\n")
    L.append("| Mk | Anunciante | Nivel | C7+ | Total | Máx días | Dup | Destino | Score |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for c in res["candidatos"][:25]:
        L.append("| %s | %s | %s | %d | %d | %d | %d | %s | %.0f |"
                 % (c["market"], c["page"].replace("|", "/"), c["nivel"], c["c7"], c["n"], c["max"],
                    c["dup"], c["dest_principal"], c["score"]))
    if res["descartes_destino"]:
        L.append("\n## Descartados por destino (sin abrir)\n")
        for m, n in sorted(res["descartes_destino"].items(), key=lambda x: -x[1]):
            L.append("- %s: %d" % (m, n))
    if res["whales"]:
        L.append("\n## Whales (50+ anuncios: nicho con dueño)\n")
        for w in res["whales"][:10]:
            L.append("- [%s] %s — %d anuncios, %d en cohorte" % (w["market"], w["page"], w["n"], w["c7"]))
    L.append("\nSiguiente paso para cada ✅: `python scripts/profundizar.py <PAIS> \"<anunciante>\" --dest <dominio>`")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=10, help="cuántas landings abrir")
    ap.add_argument("--mercados", nargs="*", help="filtrar mercados (ES IT ...)")
    ap.add_argument("--min-nivel", default="mirar", choices=N.NIVELES[1:])
    ap.add_argument("--sin-verificar", action="store_true", help="no abrir navegador")
    ap.add_argument("--no-historico", action="store_true", help="no añadir al historico.csv")
    a = ap.parse_args(argv)

    mercados = {m.upper() for m in a.mercados} if a.mercados else None
    ads = N.cargar_barridos(mercados=mercados)
    if not ads:
        sys.exit("No hay barridos en %s. Primero: python scripts/barrido.py ES \"kw1|kw2\" 4" % N.SAL)
    pag = N.agrega(ads)
    con_cohorte = sum(1 for d in pag.values() if d["c7"] >= N.VARA["c7"][0])
    cands, descartes = candidatos(pag, a.min_nivel)
    print("anuncios únicos: %d | anunciantes: %d | con cohorte>=%d: %d | candidatos: %d"
          % (len(ads), len(pag), N.VARA["c7"][0], con_cohorte, len(cands)))

    print("\n%-3s %-28s %-11s %4s %4s %5s %3s %-28s %5s" %
          ("MK", "ANUNCIANTE", "NIVEL", "C7+", "TOT", "MAXd", "DUP", "DESTINO", "SCORE"))
    print("-" * 104)
    for c in cands[:24]:
        print("%-3s %-28s %-11s %4d %4d %5d %3d %-28s %5.0f"
              % (c["market"], c["page"][:28], c["nivel"], c["c7"], c["n"], c["max"], c["dup"],
                 c["dest_principal"][:28], c["score"]))

    verif = []
    if not a.sin_verificar and cands:
        print("\nverificando %d landings (contexto aislado por sitio)..." % min(a.top, len(cands)))
        with N.playwright() as p:
            b = N.lanzar(p)
            try:
                for c in cands[:a.top]:
                    dest = c["dest_principal"]
                    url = dest if dest.startswith("http") else "https://" + dest
                    d = N.abrir_landing(b, url)
                    v = {"fecha": dt.date.today().isoformat(), "market": c["market"], "page": c["page"],
                         "nicho": ", ".join(c["kw"][:2]), "c7": c["c7"], "n": c["n"], "max": c["max"],
                         "dup": c["dup"], "nivel": c["nivel"], "dest": dest,
                         "precio": " / ".join(d.get("precios") or [])[:40],
                         "tipo": d.get("tipo"), "veredicto": d.get("veredicto"), "motivo": d.get("motivo"),
                         "title": d.get("title", ""), "plataforma": d.get("plataforma"),
                         "muestra": d.get("muestra", ""), "copy": (c["copies"] or [""])[0][:90]}
                    verif.append(v)
                    print("\n%s %-26s [%s] %s c7=%d max=%dd → %s (%s)"
                          % (ICONO.get(v["veredicto"], "?"), c["page"][:26], c["market"], c["nivel"],
                             c["c7"], c["max"], v["tipo"], v["motivo"]))
                    if v["title"] or v["precio"]:
                        print("    %s | precios: %s" % (v["title"][:60], v["precio"] or "-"))
            finally:
                b.close()

    modelables = sum(1 for v in verif if v["veredicto"] == "modelable")
    t = N.tasas(len(pag), con_cohorte, len(verif), modelables)
    res = {"fecha": dt.date.today().isoformat(), "anuncios": len(ads), "anunciantes": len(pag),
           "mercados": sorted({d["market"] for d in pag.values()}), "con_cohorte": con_cohorte,
           "modelables": modelables, "tasas": t, "descartes_destino": descartes,
           "whales": [{k: w[k] for k in ("market", "page", "n", "c7")} for w in whales(pag)],
           "candidatos": [{k: c[k] for k in ("market", "page", "nivel", "score", "c7", "n", "max", "dup",
                                              "dest_principal", "tipo_destino", "kw", "copies")}
                          for c in cands],
           "verificados": verif}

    N.guardar_json(os.path.join(N.SAL, "caza_final.json"), res)
    with open(os.path.join(N.SAL, "caza_final.md"), "w", encoding="utf-8") as fh:
        fh.write(informe_md(res))
    if verif and not a.no_historico:
        N.registrar(verif)

    print("\nTASA DE SEÑAL %.2f %% (%d/%d) · TASA DE MODELO %.1f %% (%d/%d verificados)"
          % (t["tasa_senal"], con_cohorte, len(pag), t["tasa_modelo"], modelables, len(verif)))
    print("guardado: salidas/caza_final.json · salidas/caza_final.md%s"
          % (" · salidas/historico.csv" if verif and not a.no_historico else ""))


if __name__ == "__main__":
    main()
