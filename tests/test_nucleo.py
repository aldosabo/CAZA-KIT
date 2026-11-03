# -*- coding: utf-8 -*-
"""Pruebas sin red: parseo, vara, clasificación de landings y pipeline de análisis.

python -m unittest discover -s tests -v
"""
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

TMP = tempfile.mkdtemp(prefix="caza_test_")
os.environ["CAZA_SALIDAS"] = TMP
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "scripts", "revisar"))

import nucleo as N  # noqa: E402

HOY = dt.date(2026, 11, 2)

TARJETA = """Activo
Identificador de la biblioteca: 1234567890
En circulación desde el 12 de mar. de 2026
Plataformas
Ver detalles del anuncio
Mundo de La Costura
Publicidad
🧵 ¡Transforma tus telas favoritas en neceseres hermosos!
MUNDODELACOSTURA.COM
Moldes en PDF
Más información
Este anuncio tiene varias versiones"""


class Parseo(unittest.TestCase):
    def test_fechas(self):
        self.assertEqual(N.parse_date("12 de mar. de 2026"), dt.date(2026, 3, 12))
        self.assertEqual(N.parse_date("1 sept 2025"), dt.date(2025, 9, 1))
        self.assertEqual(N.parse_date("3 dic 2025"), dt.date(2025, 12, 3))
        self.assertEqual(N.parse_date("Mar 12, 2026"), dt.date(2026, 3, 12))
        self.assertIsNone(N.parse_date("ayer"))
        self.assertIsNone(N.parse_date("31 feb 2026"))

    def test_tarjeta(self):
        a = N.parse_card(TARJETA, HOY)
        self.assertEqual(a["id"], "1234567890")
        self.assertEqual(a["fecha"], "2026-03-12")
        self.assertEqual(a["edad"], 235)
        self.assertEqual(a["page"], "Mundo de La Costura")
        self.assertEqual(a["dest"], "mundodelacostura.com")
        self.assertTrue(a["copy"].startswith("🧵"))
        self.assertTrue(a["dup"])
        json.dumps(a)  # serializable sin default=str

    def test_tarjeta_invalida(self):
        self.assertIsNone(N.parse_card("nada que ver"))

    def test_tipo_destino(self):
        self.assertEqual(N.tipo_destino("play.google.com"), "app")
        self.assertEqual(N.tipo_destino("www.amazon.es"), "retail")
        self.assertEqual(N.tipo_destino("pay.hotmart.com"), "plataforma")
        self.assertEqual(N.tipo_destino("wa.me"), "red_social")
        self.assertEqual(N.tipo_destino("fonoaprende.com"), "propio")
        self.assertEqual(N.tipo_destino(""), "sin_destino")


class Vara(unittest.TestCase):
    def test_niveles(self):
        self.assertEqual(N.nivel(2, 300), "ruido")          # sin cohorte no hay nada
        self.assertEqual(N.nivel(3, 5), "mirar")            # cohorte mínima, joven
        self.assertEqual(N.nivel(24, 52), "profundizar")    # mucha cohorte pero < 120 días
        self.assertEqual(N.nivel(24, 150), "ganador")
        self.assertEqual(N.nivel(9, 192), "profundizar")
        self.assertEqual(N.nivel(9, 192, dup=10), "ganador")  # duplicación respaldada por edad
        self.assertEqual(N.nivel(9, 30, dup=10), "mirar")     # duplicación sin edad no sube

    def test_vara_md_alineada(self):
        """Los umbrales de cerebro/vara.md y los de nucleo.VARA deben ser los mismos."""
        import re
        with open(os.path.join(RAIZ, "cerebro", "vara.md"), encoding="utf-8") as fh:
            md = fh.read()

        def fila(nombre):
            linea = next(l for l in md.splitlines() if l.startswith("| " + nombre))
            return tuple(int(x) for x in re.findall(r"(\d+)", linea.split("|", 2)[2])[:3])
        self.assertEqual(fila("Cohorte 7+"), N.VARA["c7"])
        self.assertEqual(fila("Antigüedad"), N.VARA["edad"])
        self.assertEqual(fila("Creativos duplicados"), N.VARA["dup"])

    def test_tasas(self):
        self.assertEqual(N.tasas(200, 20, 8, 4), {"tasa_senal": 10.0, "tasa_modelo": 50.0})
        self.assertEqual(N.tasas(0, 0, 0, 0), {"tasa_senal": 0.0, "tasa_modelo": 0.0})


RELLENO = " Lorem ipsum dolor sit amet consectetur. " * 8


class Landing(unittest.TestCase):
    def v(self, txt, url="https://ejemplo.com"):
        return N.clasifica_landing(txt + RELLENO, url)[0:2]

    def test_infoproducto(self):
        self.assertEqual(self.v("Pack de +1001 fichas imprimibles en PDF. Acceso inmediato. "
                                "Precio 17 € Comprar ahora"), ("modelable", "infoproducto"))

    def test_retail(self):
        self.assertEqual(self.v("Bolso de piel. Envío gratis. Elige talla. Devoluciones 30 días. "
                                "Añadir al carrito 49,90 €"), ("descartado", "retail"))

    def test_academia(self):
        self.assertEqual(self.v("Máster con título oficial. Matrícula abierta. Formación bonificada FUNDAE"),
                         ("descartado", "academia"))

    def test_marca_personal(self):
        self.assertEqual(self.v("Soy Laura, coach. Con mi método y mi mentoría. Agenda una llamada"),
                         ("descartado", "marca_personal"))

    def test_app_por_url(self):
        self.assertEqual(N.clasifica_landing("x" * 500, "https://play.google.com/store/apps/x")[0],
                         "descartado")

    def test_sin_contenido(self):
        self.assertEqual(N.clasifica_landing("", "https://x.com")[1], "vacía")

    def test_sin_precio(self):
        self.assertEqual(self.v("Plantillas para wedding planners"), ("dudoso", "sin_precio"))


def ad(i, page, edad, dest, kw="costura moldes", dup=False):
    return {"id": str(i), "page": page, "edad": edad, "dest": dest, "copy": "copy %s" % page,
            "dup": dup, "kw": kw, "fecha": None}


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ads, i = [], 0
        for e in range(30):  # ganador: 25 en cohorte, el más viejo 150 días
            i += 1
            ads.append(ad(i, "Moldes PDF", 150 - e * 5 if e < 25 else 2, "moldespdf.com"))
        for e in range(12):  # app con mucha cohorte: debe caer por destino
            i += 1
            ads.append(ad(i, "Una App", 60, "play.google.com"))
        for e in range(2):
            i += 1
            ads.append(ad(i, "Ruido", 40, "ruido.com"))
        ads.append(dict(ads[0]))  # duplicado exacto: se ignora
        N.guardar_json(os.path.join(TMP, "barrido_ES.json"),
                       {"costura moldes": {"total_library": 100, "ads": ads}})
        N.guardar_json(os.path.join(TMP, "barrido_IT.json"), {"modelli cucito": {"ads": [
            ad(900, "Moldes PDF", 30, "moldespdf.com", "modelli cucito")]}})

    def test_carga_y_agrega(self):
        ads = N.cargar_barridos()
        self.assertEqual(len(ads), 45)  # 44 ES únicos + 1 IT (mismo nombre, otro mercado)
        pag = N.agrega(ads)
        g = pag[("ES", "Moldes PDF")]
        self.assertEqual((g["c7"], g["n"], g["max"], g["nivel"]), (25, 30, 150, "ganador"))
        self.assertEqual(pag[("ES", "Una App")]["tipo_destino"], "app")
        self.assertEqual(pag[("ES", "Ruido")]["nivel"], "ruido")

    def test_caza_final_sin_verificar(self):
        import caza_final
        with redirect_stdout(io.StringIO()) as out:
            caza_final.main(["--sin-verificar"])
        res = N.cargar_json(os.path.join(TMP, "caza_final.json"))
        pages = [c["page"] for c in res["candidatos"]]
        self.assertEqual(pages[0], "Moldes PDF")
        self.assertNotIn("Una App", pages)
        self.assertEqual(res["descartes_destino"], {"app/SaaS": 1})
        self.assertIn("TASA DE SEÑAL", out.getvalue())
        self.assertTrue(os.path.exists(os.path.join(TMP, "caza_final.md")))

    def test_revisar(self):
        import rankear
        import tasa_oficio
        import hueco
        with redirect_stdout(io.StringIO()):
            rankear.main([])
            tasa_oficio.main(["--no-guardar"])
            hueco.main(["ES", "IT"])
        self.assertTrue(N.cargar_json(os.path.join(TMP, "ranking.json")))

    def test_historico(self):
        f = os.path.join(TMP, "h.csv")
        N.registrar([{"page": "X", "motivo": "retail físico"}], f)
        N.registrar([{"page": "Y", "motivo": "ok"}], f)
        with open(f, encoding="utf-8") as fh:
            lineas = fh.read().strip().splitlines()
        self.assertEqual(len(lineas), 3)
        self.assertTrue(lineas[0].startswith("fecha,market,page"))


class ClasificacionLanding(unittest.TestCase):
    """Regresión: los tres falsos positivos que costaron una caza entera."""

    RELLENO = (" Aprende paso a paso con material descargable y acceso desde cualquier "
               "dispositivo, actualizado cada temporada y explicado con ejemplos reales.")

    def test_suplemento_es_fisico(self):
        # Luvain: 190 anuncios en cohorte vendiendo astaxantina en cápsulas.
        txt = ("SPEDIZIONE GRATIS IN 24/48H APRI CARRELLO Astaxantina dosaggio 12 mg en una "
               "softgel quotidiana. ACQUISTA ORA 70% DI SCONTO Garanzia 90 giorni "
               "integratore alimentare 30 capsule molli." + self.RELLENO)
        v, tipo, motivo = N.clasifica_landing(txt, "https://luvain.it")
        self.assertEqual(v, "descartado")
        self.assertEqual(tipo, "fisico")
        self.assertIn("fabricante", motivo)

    def test_pdf_con_precio_es_modelable(self):
        # Mundo de La Costura: «50 bolsas de tela en PDF», R$ 97. Antes salía sin_oferta.
        txt = ("50 Bolsas de Tecido em PDF com moldes cotados. Acesso imediato apos o pagamento. "
               "R$ 97,00. Comprar agora e baixar o PDF na hora com os 50 moldes prontos."
               + self.RELLENO)
        v, tipo, _ = N.clasifica_landing(txt, "https://mundodelacostura.com")
        self.assertEqual(v, "modelable")
        self.assertEqual(tipo, "infoproducto")

    def test_tienda_fisica_es_retail(self):
        # Mercería con 179 anuncios en cohorte: el podio siempre lo ocupa el retail.
        txt = ("Nuestra tienda de lanas. Envio gratis a partir de 30 EUR. Tallas y colores "
               "disponibles. Anade al carrito y recibe en 48 horas. Devoluciones sin coste."
               + self.RELLENO)
        v, tipo, _ = N.clasifica_landing(txt, "https://lacariaricami.store")
        self.assertEqual(v, "descartado")
        self.assertEqual(tipo, "retail")

    def test_academia_no_es_impulso(self):
        txt = ("Titulo oficial de logopeda con titulacion homologada. Matricula abierta todo el "
               "ano. Formacion bonificada para profesionales sanitarios." + self.RELLENO)
        v, tipo, _ = N.clasifica_landing(txt, "https://fonoaprende.com")
        self.assertEqual(v, "descartado")
        self.assertEqual(tipo, "academia")


if __name__ == "__main__":
    unittest.main()
