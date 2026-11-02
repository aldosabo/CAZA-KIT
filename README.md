# Kit de caza — dos skills y las herramientas

Todo lo necesario para cazar productos digitales ganadores en la Biblioteca de Anuncios de Meta, sin conector oficial, con navegador.

## Qué hay dentro

```
caza-kit/
  skills/
    cazar/SKILL.md          búsqueda de winners con el conector oficial de Meta
    cazar/ORIGEN.md         de dónde salió y su licencia
    caza-oficios/SKILL.md   método propio: buscar por oficio, verificar el embudo, medir la puntería
  scripts/                  el motor, en Python
    nucleo.py               lo común: parseo, paginación, la vara en código, landings, guardado
    cazar_lib.py            tanteo rápido de UNA keyword (calibración)
    barrido.py              barrido por keywords y país, reanudable
    caza_exhaustiva.py      varios mercados con el banco de oficios, reanudable
    caza_final.py           une barridos, aplica la vara, abre landings, informe + histórico
    profundizar.py          page_id, arsenal en varios países y hueco de arbitraje
    revisar/                rankear, ficha, otros (sin revisar), hueco, tasa_oficio
  cerebro/
    vara.md                 criterios y umbrales de descarte (los mismos que usa el código)
    banco-keywords.md       27 colectivos en ES/PT/IT con sus formatos
  tests/                    pruebas sin red: python -m unittest discover -s tests
  ejemplo/
    caza_final.json         resultado real: 4 modelables en 634 anuncios
```

## Instalación

1. **Requisitos**: Python 3.10+ y Playwright.
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
   ¿Prefieres tu Chrome instalado? `export CAZA_CHROME="/ruta/a/chrome"` (Windows: `set CAZA_CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe`).
2. **Skills**: copia las carpetas de `skills/` dentro de `~/.claude/skills/`.
   ```bash
   cp -r skills/cazar skills/caza-oficios ~/.claude/skills/
   ```
   Claude Code las detecta al reiniciar la sesión.
3. **Comprobar** que todo está bien (no usa red):
   ```bash
   python -m unittest discover -s tests
   ```
4. Ejecuta los scripts desde la raíz del kit. Crean `salidas/` solos (o la carpeta de `CAZA_SALIDAS`).

## Cómo se usa

```bash
# 0. calibrar: una keyword donde ya sabes que hay ganador
python scripts/cazar_lib.py ES "logopedia"

# 1. barrer (10-12 keywords, 4-6 rondas). Si se corta, relanza: sigue donde iba.
python scripts/barrido.py ES "logopedia|costura moldes|wedding planner" 4
python scripts/barrido.py IT --banco

# 2. decidir: vara + apertura de las 10 mejores landings
python scripts/caza_final.py --top 10
#    → salidas/caza_final.md  (informe legible: ✅ modelables, ⚠️ dudosos, ❌ con motivo)

# 3. medir la puntería y comparar con la caza anterior
python scripts/revisar/tasa_oficio.py

# 4. profundizar en cada ✅ y buscar el país donde aún no está
python scripts/profundizar.py ES "Mundo de La Costura" --dest mundodelacostura.com --mercados ES MX CO AR
```

### Qué decide el kit por ti

| Paso | Regla (de `cerebro/vara.md`) |
|---|---|
| Nivel del anunciante | `ruido` / `mirar` / `profundizar` / `ganador`: cohorte 7+ **y** antigüedad |
| Descarte sin abrir | destino app/SaaS, retail (Amazon, Etsy…), red social o sin destino |
| Veredicto de la landing | ✅ digital + checkout + precio · ❌ retail, academia con título, marca personal · ⚠️ sin precio, captación gratuita, caído |
| Whale | 50+ anuncios de un jugador → nicho con dueño |
| Registro | cada verificado va a `salidas/historico.csv` con su motivo; `otros.py` ya no te los vuelve a enseñar |
| Puntería | `tasa_oficio.py` guarda `tasas.csv` y dice si el cambio de método sirvió; marca keywords a podar |

El veredicto automático es un **filtro**, no la decisión final: abre a mano los ✅ y los ⚠️ antes de modelar.

## Las cinco trampas que cuestan una tarde

1. **Dos navegadores a la vez = cuelgue silencioso.** Secuencial siempre.
2. **Chrome huérfanos**: si un barrido «se cuelga» en la primera keyword, no es Meta: son procesos viejos. Mátalos (`pkill -f "chrome.*--headless"` en macOS/Linux) y reintenta.
3. **Clasificar por el copy falla.** Se clasifica abriendo la landing.
4. **Un DNS roto contamina el navegador**: un contexto aislado por sitio.
5. **Guardar por keyword**, no al final. (El kit ya lo hace y reanuda solo.)

## Resultado de referencia

Con keywords de **formato** (`ebook`, `printables`, `planilha`): 3 modelables en 2.384 anuncios.
Con keywords de **oficio** (`logopedia`, `costura moldes`, `terapia ocupacional`): **4 modelables en 634**.

Ejemplos reales que salieron en esa caza: un PDF de 50 bolsos con moldes (cohorte 24/24), una plantilla de boda de $67 (192 días), un curso de lencería (186 días) y un pack de +1001 actividades de terapia ocupacional a $17.

## Licencia y atribución

- `skills/caza-oficios`, `cerebro/` y `scripts/`: de quien te pasa el kit. Úsalos y modifícalos.
- `skills/cazar`: proviene de un repositorio público **sin licencia declarada** (ver `ORIGEN.md`). Es contenido publicado públicamente, pero sin permiso explícito de redistribución: úsalo para ti y no lo revendas ni lo publiques como propio.

## Aviso de uso

Todo el kit lee datos **públicos** de la Biblioteca de Anuncios, en volumen moderado y con pausas (el barrido espera entre keywords y para de paginar cuando ya no llegan anuncios nuevos). La interfaz de la Biblioteca cambia: si un día no lee nada, ejecuta `cazar_lib.py` con `--rondas 2` y revisa `CARD_JS` en `nucleo.py`. No descarga ni reutiliza creatividades ajenas: solo cuenta anuncios, fechas y destinos para decidir qué modelar.
