# -*- coding: utf-8 -*-
"""Núcleo común del kit de caza.

Todo lo que antes estaba copiado en cada script vive aquí:
- lectura de tarjetas de la Biblioteca de Anuncios (DOM en español)
- paginación con parada temprana cuando ya no llegan anuncios nuevos
- agregación por anunciante (cohorte 7+, antigüedad, duplicados, destino)
- la vara de `cerebro/vara.md` convertida en código (niveles y descartes)
- clasificación de landings con motivo de descarte
- guardado atómico y registro histórico

Playwright solo se importa al abrir el navegador, así que el análisis
(caza_final sin verificar, revisar/*, tests) funciona sin él.
"""
import csv
import datetime as dt
import json
import os
import re
import sys
import tempfile
import time
from urllib.parse import quote_plus, urlparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAL = os.environ.get("CAZA_SALIDAS") or os.path.join(BASE, "salidas")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

LIBRARY = ("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
           "&country={country}&q={q}&search_type=keyword_unordered&media_type=all")
LIBRARY_PAGE = ("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                "&country={country}&view_all_page_id={pid}&search_type=page&media_type=all")

# ---------------------------------------------------------------- la vara
# Umbrales de cerebro/vara.md §2. Cambiar aquí = cambiar la vara.
VARA = {
    "c7": (3, 8, 20),          # mirar, profundizar, ganador
    "edad": (21, 45, 120),     # días del anuncio vivo más antiguo
    "dup": (3, 6, 10),         # creativos duplicados
}
NIVELES = ("ruido", "mirar", "profundizar", "ganador")
WHALE = 50  # anuncios de un solo jugador que bloquean un nicho

RETAIL = ("amazon", "shein", "shopee", "mercadolivre", "aliexpress", "mercadolibre", "temu",
          "ebay", "walmart", "target.com", "etsy", "ikea", "leroy", "carrefour", "americanas",
          "magazineluiza", "casasbahia", "kabum", "tokstok", "hobbii", "zalando", "elcorteingles",
          "decathlon", "fnac", "mediamarkt", "shop.app")
APPS = ("play.google", "apps.apple", "itunes.apple", "onelink.me", "app.link", "adj.st")
REDES = ("tiktok.com", "instagram.com", "facebook.com", "fb.me", "whatsapp", "wa.me",
         "m.me", "messenger.com", "youtube.com", "t.me", "linkedin.com")
SAAS = ("adobe", "canva", "notion.so", "hubspot", "shopify.com", "wix.com", "squarespace")
PLATAFORMAS = ("hotmart", "kiwify", "payhip", "gumroad", "braip", "cakto", "greenn", "eduzz",
               "perfectpay", "perfect pay", "learnworlds", "teachable", "kajabi", "thinkific",
               "podia", "systeme.io", "stan.store", "beacons.ai", "ticto", "hubla", "memberkit",
               "herospark", "monetizze", "lemonsqueezy", "sellfy", "sendowl", "ko-fi",
               "stripe", "paypal", "mercadopago", "pay.hotmart", "lastlink")

MES = {"ene": 1, "jan": 1, "gen": 1, "feb": 2, "fev": 2, "mar": 3, "abr": 4, "apr": 4,
       "may": 5, "mai": 5, "mag": 5, "jun": 6, "giu": 6, "jul": 7, "lug": 7, "ago": 8,
       "aug": 8, "sep": 9, "set": 9, "oct": 10, "out": 10, "ott": 10, "nov": 11,
       "dic": 12, "dez": 12, "dec": 12}

CARD_JS = """() => {
  const spans = [...document.querySelectorAll('span')]
    .filter(s => /^(Identificador de la biblioteca|Library ID)/.test(s.textContent || ''));
  const out = [];
  for (const s of spans) {
    let n = s, card = null;
    for (let i = 0; i < 14 && n; i++) {
      n = n.parentElement; if (!n) break;
      const t = n.innerText || '';
      if (/(Ver detalles|See ad details|See summary details)/.test(t) && t.length > 120) {
        card = n; break;
      }
    }
    if (card) out.push(card.innerText);
  }
  return out;
}"""

RE_ID = re.compile(r"(?:Identificador de la biblioteca|Library ID):\s*(\d+)")
RE_FECHA = re.compile(r"(?:En circulaci[oó]n desde el|Started running on)\s+([^\n]+)")
RE_PAGE = re.compile(r"(?:Ver detalles|See ad details|See summary details)[^\n]*\n([^\n]+)\n"
                     r"(?:Publicidad|Sponsored)")
RE_DOM = re.compile(r"\n([A-Z0-9][A-Z0-9.\-]{2,}\.[A-Z]{2,})\n")
RE_COPY = re.compile(r"\n(?:Publicidad|Sponsored)\n([^\n]+)")
RE_TOTAL = re.compile(r'"search_results_connection":\{"count":(\d+)')
RE_PRECIO = re.compile(r"(?:R\$|US\$|€|\$|£|MX\$|COP|ARS)\s?\d{1,4}(?:[.,]\d{2,3})*"
                       r"|\d{1,4}(?:[.,]\d{2})?\s?(?:€|EUR|USD)")


# ---------------------------------------------------------------- parseo
def parse_date(s):
    """'12 de mar. de 2025', '12 mar 2025', 'Mar 12, 2025' -> date."""
    if not s:
        return None
    s = s.strip().lower().replace(" de ", " ").replace(",", " ")
    m = re.match(r"(\d{1,2})\s+([a-záéíóúç]+)\.?\s+(\d{4})", s)
    if m:
        d, mes, y = m.group(1), m.group(2), m.group(3)
    else:
        m = re.match(r"([a-z]+)\.?\s+(\d{1,2})\s+(\d{4})", s)
        if not m:
            return None
        mes, d, y = m.group(1), m.group(2), m.group(3)
    mes = mes[:3]
    if mes not in MES:
        return None
    try:
        return dt.date(int(y), MES[mes], int(d))
    except ValueError:
        return None


def parse_card(txt, hoy=None):
    i = RE_ID.search(txt or "")
    if not i:
        return None
    f, p, dom, cp = RE_FECHA.search(txt), RE_PAGE.search(txt), RE_DOM.search(txt), RE_COPY.search(txt)
    fecha = parse_date(f.group(1)) if f else None
    hoy = hoy or dt.date.today()
    low = txt.lower()
    return {"id": i.group(1),
            "fecha": fecha.isoformat() if fecha else None,
            "edad": (hoy - fecha).days if fecha else None,
            "page": p.group(1).strip() if p else None,
            "dest": dom.group(1).lower() if dom else None,
            "copy": cp.group(1).strip()[:170] if cp else None,
            "dup": any(k in low for k in ("varias versiones", "varios anuncios",
                                          "multiple versions", "ads use this creative"))}


def dominio(d):
    if not d:
        return ""
    d = d.lower().strip()
    if "//" not in d:
        d = "https://" + d
    h = urlparse(d).netloc or ""
    return h[4:] if h.startswith("www.") else h


def tipo_destino(dest):
    """Clasificación barata del destino del anuncio (antes de abrir la landing)."""
    h = dominio(dest)
    if not h:
        return "sin_destino"
    if any(x in h for x in APPS):
        return "app"
    if any(x in h for x in REDES):
        return "red_social"
    if any(x in h for x in RETAIL):
        return "retail"
    if any(x in h for x in SAAS):
        return "saas"
    if any(x in h for x in PLATAFORMAS):
        return "plataforma"
    return "propio"


DESCARTE_DESTINO = {"app": "app/SaaS", "saas": "app/SaaS", "retail": "retail físico",
                    "red_social": "destino es una red social, no un checkout",
                    "sin_destino": "sin destino legible"}


# ---------------------------------------------------------------- navegador
def lanzar(p, headless=True):
    """Chromium de Playwright, o el Chrome que indiques en CAZA_CHROME (ruta al ejecutable)."""
    kw = {"headless": headless, "args": ["--no-sandbox"]}
    if os.environ.get("CAZA_CHROME"):
        kw["executable_path"] = os.environ["CAZA_CHROME"]
    return p.chromium.launch(**kw)


def abrir_navegador(p, headless=True):
    b = lanzar(p, headless)
    ctx = b.new_context(locale="es-ES", viewport={"width": 1400, "height": 1000}, user_agent=UA)
    return b, ctx, ctx.new_page()


def playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Falta Playwright:  pip install -r requirements.txt && playwright install chromium")
    return sync_playwright()


def buscar(pg, country, kw, rounds=6, espera=2000, url=None, hoy=None):
    """Abre una búsqueda y pagina. Para antes si dos rondas seguidas no traen nada."""
    seen, total, vacias = {}, None, 0
    pg.goto(url or LIBRARY.format(country=country, q=quote_plus(kw)),
            wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(5000)
    for _ in range(rounds + 1):
        antes = len(seen)
        for t in pg.evaluate(CARD_JS):
            a = parse_card(t, hoy)
            if a and a["id"] not in seen:
                seen[a["id"]] = a
        if total is None:
            m = RE_TOTAL.search(pg.content())
            if m:
                total = int(m.group(1))
        vacias = vacias + 1 if len(seen) == antes else 0
        if vacias >= 2 or (total is not None and len(seen) >= total):
            break
        pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(espera)
    return list(seen.values()), total


def barrer(pg, country, kws, rounds, archivo, espera=2000, pausa=1.5):
    """Barrido secuencial con guardado incremental y reanudación.

    Si `archivo` ya tiene una keyword con anuncios, se salta (relanzar = continuar).
    """
    out = cargar_json(archivo, {})
    for kw in kws:
        if out.get(kw, {}).get("ads"):
            print("  [%s] %-26s ya estaba (%d ads), se salta" % (country, kw[:26], len(out[kw]["ads"])))
            continue
        t0 = time.time()
        ads, total, err = [], None, None
        for intento in (1, 2):
            try:
                ads, total = buscar(pg, country, kw, rounds, espera)
                err = None
                break
            except Exception as e:  # noqa: BLE001
                err = repr(e)[:120]
                print("  ! %s intento %d: %s" % (kw, intento, err))
                time.sleep(3 * intento)
        for a in ads:
            a["kw"], a["country"] = kw, country
        out[kw] = {"total_library": total, "ads": ads, "fecha": dt.date.today().isoformat()}
        if err:
            out[kw]["error"] = err
        guardar_json(archivo, out)
        print("  [%s] %-26s ads=%-4d library=%-7s %.0fs"
              % (country, kw[:26], len(ads), total, time.time() - t0))
        time.sleep(pausa)  # volumen moderado y con pausas
    return out


# ---------------------------------------------------------------- agregación
def cargar_barridos(rutas=None, mercados=None):
    """Lee barrido_*.json y exhaustiva_*.json. Devuelve lista de anuncios únicos por mercado."""
    import glob
    rutas = rutas or sorted(glob.glob(os.path.join(SAL, "barrido_*.json")) +
                            glob.glob(os.path.join(SAL, "exhaustiva_*.json")))
    ads, vistos = [], set()
    for f in rutas:
        mk = os.path.basename(f).split("_", 1)[1].rsplit(".", 1)[0].upper()
        if mercados and mk not in mercados:
            continue
        for kw, blk in cargar_json(f, {}).items():
            if not isinstance(blk, dict):
                continue
            for a in blk.get("ads", []):
                clave = (mk, a.get("id"))
                if not a.get("id") or clave in vistos:
                    continue
                vistos.add(clave)
                a = dict(a, mk=mk, kw=a.get("kw") or kw)
                ads.append(a)
    return ads


def agrega(ads):
    """Agrupa por (mercado, anunciante)."""
    pag = {}
    for a in ads:
        k = (a.get("mk") or a.get("country") or "?", a.get("page") or "?")
        d = pag.setdefault(k, {"market": k[0], "page": k[1], "n": 0, "c7": 0, "edades": [],
                               "dup": 0, "dest": {}, "copies": [], "kw": set()})
        d["n"] += 1
        d["kw"].add(a.get("kw") or "")
        e = a.get("edad")
        if e is not None and e >= 7:
            d["c7"] += 1
            d["edades"].append(e)
        if a.get("dup"):
            d["dup"] += 1
        if a.get("dest"):
            d["dest"][a["dest"]] = d["dest"].get(a["dest"], 0) + 1
        if a.get("copy") and len(d["copies"]) < 5:
            d["copies"].append(a["copy"])
    for d in pag.values():
        d["max"] = max(d["edades"]) if d["edades"] else 0
        d["dest_principal"] = max(d["dest"].items(), key=lambda x: x[1])[0] if d["dest"] else ""
        d["tipo_destino"] = tipo_destino(d["dest_principal"])
        d["kw"] = sorted(x for x in d["kw"] if x)
        d["nivel"] = nivel(d["c7"], d["max"], d["dup"])
        d["score"] = score(d)
    return pag


def _escalon(valor, umbrales):
    return sum(1 for u in umbrales if valor >= u)


def nivel(c7, max_edad, dup=0):
    """Nivel de la vara. La cohorte manda: sin cohorte >= 3 es ruido.

    Cada nivel exige cohorte Y antigüedad de ese nivel (ganador = c7 >= 20 y >= 120 días).
    Con cohorte suficiente siempre queda al menos en 'mirar'. Muchos duplicados (10+)
    suben un escalón si la antigüedad ya lo respalda.
    """
    n = _escalon(c7, VARA["c7"])
    if n == 0:
        return NIVELES[0]
    e = _escalon(max_edad, VARA["edad"])
    final = max(1, min(n, e))
    if _escalon(dup, VARA["dup"]) == 3 and final < e:
        final += 1
    return NIVELES[min(final, 3)]


def score(d):
    """Orden de revisión: cohorte, longevidad, duplicación; penaliza destinos descartables."""
    s = d["c7"] * 2.0 + min(d["max"], 240) / 6.0 + min(d["dup"], 12) * 1.5
    if d["tipo_destino"] == "plataforma":
        s += 10
    if d["tipo_destino"] in DESCARTE_DESTINO:
        s -= 60
    if d["n"] >= WHALE:
        s -= 15  # whale: probablemente nicho bloqueado o fábrica de churn
    if d["n"] and d["c7"] / d["n"] < 0.3:
        s -= 10  # mucho anuncio nuevo y poco superviviente
    return round(s, 1)


# ---------------------------------------------------------------- landing
RE_CHECKOUT = re.compile(r"(comprar|compra ahora|adquirir|acquista|buy now|add to cart|checkout|"
                         r"carrito|añadir al carrito|pagar|finalizar compra|quiero (?:el|mi|acceso)|"
                         r"get instant access|scarica ora|obtener acceso|"
                         r"inscr[ií]b|inscri[cç][aã]o|iscriv|matricul|matr[ií]cula|enroll|"
                         r"ap[uú]ntate|contratar|suscribirme)", re.I)
RE_DESCARGA = re.compile(r"(descarga|descargable|acceso inmediato|entrega inmediata|al instante|"
                         r"download|instant access|immediat|acesso imediato|scaricabil)", re.I)
RE_DIGITAL = re.compile(r"\b(pdf|imprimibles?|stampabil\w*|printables?|plantillas?|templates?|"
                        r"fichas|schede|cuadernillos?|e-?book|moldes?\s+(?:en\s+)?pdf|"
                        r"patr[oó]n(?:es)?\s+pdf|canva)\b", re.I)
RE_CURSO = re.compile(r"(curso|videolez|lezioni|lecciones|m[oó]dulos|moduli|clases|"
                      r"masterclass|formaci[oó]n|formazione)", re.I)
RE_ACADEMIA = re.compile(r"(t[ií]tulo oficial|titulaci[oó]n|certificado de profesionalidad|"
                         r"formaci[oó]n bonificada|fundae|m[aá]ster universitario|"
                         r"prevenci[oó]n de riesgos|compliance|matr[ií]cula)", re.I)
RE_TIENDA = re.compile(r"(env[ií]o gratis|gastos de env[ií]o|spedizione|frete|talla|taglia|"
                       r"devoluciones|reso gratuito|en stock|agotado|esaurito|nuestra tienda|"
                       r"carrello|carrito|añadir al carrito|add to cart|acquista ora|compra ahora|"
                       r"checkout|ordine|pedido|env[ií]o en \d+|entrega en \d+)", re.I)

# Producto físico: si aparecen dos o más señales, no es un infoproducto modelable
# (haría falta fabricante, inventario y logística). Aprendido con Luvain: 190 anuncios
# en cohorte vendiendo astaxantina en cápsulas, clasificado como «captación».
RE_FISICO = re.compile(r"(integratore|integratori|suplemento|suplementos|c[aá]psulas?|capsule|"
                       r"softgel|compresse|comprimidos|col[aá]geno|crema facial|s[eé]rum|"
                       r"perfume|champ[uú]|jab[oó]n|vitamina|omega ?3|colágeno|\b\d+\s?mg\b|"
                       r"dosis diaria|dosaggio|contenido neto|peso neto|tallas?|taglie)", re.I)
RE_MARCA = re.compile(r"(mi m[eé]todo|il mio metodo|soy (?:\w+ )?(?:coach|mentor)|"
                      r"mentor[ií]a|mentoring|sesi[oó]n estrat[eé]gica|llamada de descubrimiento|"
                      r"agenda (?:tu|una) llamada|aplica(?:r)? (?:ahora|aqu[ií])|plazas limitadas)", re.I)
RE_GRATIS = re.compile(r"(gratis|gratuito|free|webinar|reto de \d+ d[ií]as|sfida)", re.I)


def clasifica_landing(txt, url=""):
    """Devuelve (veredicto, tipo, motivo) según la tabla de embudos de caza-oficios.

    veredicto: 'modelable' | 'dudoso' | 'descartado'
    """
    t = re.sub(r"\s+", " ", txt or "")
    td = tipo_destino(url)
    if td in DESCARTE_DESTINO:
        return "descartado", td, DESCARTE_DESTINO[td]
    if len(t) < 200:
        return "dudoso", "vacía", "landing sin contenido legible (JS, login o bloqueo)"
    precios = RE_PRECIO.findall(t)
    checkout = bool(RE_CHECKOUT.search(t)) or td == "plataforma"
    descarga = bool(RE_DESCARGA.search(t))
    digital = len(RE_DIGITAL.findall(t))
    tienda = len(RE_TIENDA.findall(t))
    if RE_ACADEMIA.search(t):
        return "descartado", "academia", "academia/curso con titulación: servicio, no impulso"
    fisico = len(RE_FISICO.findall(t))
    if fisico >= 2:
        return "descartado", "fisico", ("producto físico (%d señales): cápsulas, suplemento o "
                                        "cosmética. No modelable sin fabricante" % fisico)
    if tienda >= 3 or (tienda >= 2 and digital == 0):
        return "descartado", "retail", "tienda física: carrito, envío o stock"
    if RE_MARCA.search(t) and not precios:
        return "descartado", "marca_personal", "puerta a mentoría o marca personal, sin precio"
    if (digital or descarga) and checkout and precios:
        return "modelable", "infoproducto", "digital + checkout + precio visible"
    if RE_CURSO.search(t) and checkout and precios:
        return "modelable", "curso", "curso con precio y checkout (revisar que sea autónomo)"
    if RE_GRATIS.search(t) and (digital or RE_CURSO.search(t)):
        return "dudoso", "captación", "gratis/reto: mirar la oferta que viene después"
    if not precios:
        return "dudoso", "sin_precio", "no se ve precio en la landing"
    return "dudoso", "sin_oferta", "hay precio pero no se ve producto digital claro"


def abrir_landing(browser, url, espera=3000):
    """Abre la landing en un contexto aislado (un DNS roto no contamina al resto)."""
    d = {"url": url}
    ctx = browser.new_context(locale="es-ES", viewport={"width": 1280, "height": 900}, user_agent=UA)
    pg = ctx.new_page()
    try:
        ok = False
        variantes = [url]
        if "://www." in url:
            variantes.append(url.replace("://www.", "://"))
        else:
            variantes.append(url.replace("://", "://www.", 1))
        for u in variantes:
            try:
                r = pg.goto(u, wait_until="domcontentloaded", timeout=25000)
                d["status"] = r.status if r else None
                ok = True
                break
            except Exception as e:  # noqa: BLE001
                d["error"] = repr(e)[:100]
        if not ok:
            raise RuntimeError(d.get("error", "no resuelve"))
        d.pop("error", None)
        pg.wait_for_timeout(espera)
        txt = pg.inner_text("body")
        d["final_url"] = pg.url
        d["title"] = (pg.title() or "")[:90]
        d["precios"] = RE_PRECIO.findall(txt)[:4]
        d["plataforma"] = next((x for x in PLATAFORMAS if x in (txt[:20000] + pg.url).lower()), None)
        d["muestra"] = re.sub(r"\s+", " ", txt)[:200]
        d["veredicto"], d["tipo"], d["motivo"] = clasifica_landing(txt, pg.url)
    except Exception as e:  # noqa: BLE001
        d.setdefault("error", repr(e)[:100])
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass
    if "error" in d:
        d.update(veredicto="dudoso", tipo="no_verificable", motivo="dominio caído o no resuelve")
    return d


# ---------------------------------------------------------------- E/S
def cargar_json(f, defecto=None):
    try:
        with open(f, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return defecto


def guardar_json(f, data):
    """Escritura atómica: si se corta a mitad, el archivo anterior queda intacto."""
    os.makedirs(os.path.dirname(os.path.abspath(f)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(f)), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, default=str)
    os.replace(tmp, f)


CAMPOS_HISTORICO = ("fecha", "market", "page", "nicho", "page_id", "c7", "n", "max", "dup",
                    "nivel", "dest", "precio", "tipo", "veredicto", "motivo")


def registrar(filas, f=None):
    """Añade filas a salidas/historico.csv (vara §6: sin el motivo, el histórico no enseña)."""
    f = f or os.path.join(SAL, "historico.csv")
    os.makedirs(os.path.dirname(f), exist_ok=True)
    nuevo = not os.path.exists(f)
    with open(f, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS_HISTORICO, extrasaction="ignore")
        if nuevo:
            w.writeheader()
        for r in filas:
            w.writerow({k: r.get(k, "") for k in CAMPOS_HISTORICO})
    return f


def tasas(n_anunciantes, n_cohorte, n_verificados, n_modelables):
    return {"tasa_senal": round(100.0 * n_cohorte / n_anunciantes, 2) if n_anunciantes else 0.0,
            "tasa_modelo": round(100.0 * n_modelables / n_verificados, 2) if n_verificados else 0.0}


def slug(s, n=24):
    return re.sub(r"\W+", "_", s or "").strip("_")[:n]
