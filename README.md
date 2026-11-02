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
    barrido.py              barrido por keywords y país (secuencial)
    caza_exhaustiva.py      varios mercados en una pasada, guardado incremental
    caza_final.py           une barridos, rankea y abre los embudos de los mejores
    profundizar.py          resuelve page_id, cuenta el arsenal y abre la landing
    revisar/                utilidades de análisis (rank, huecos, fichas)
  cerebro/
    vara.md                 criterios y umbrales de descarte
    banco-keywords.md       27 colectivos en ES/PT/IT con sus formatos
  ejemplo/
    caza_final.json         resultado real: 4 modelables en 634 anuncios
```

## Instalación

1. **Requisitos**: Python 3.10+, Google Chrome, y Playwright.
   ```bash
   pip install playwright
   playwright install chromium
   ```
2. **Skills**: copia las carpetas de `skills/` dentro de `~/.claude/skills/`.
   ```bash
   cp -r skills/cazar skills/caza-oficios ~/.claude/skills/
   ```
   Claude Code las detecta al reiniciar la sesión.
3. **Scripts**: déjalos en una carpeta de trabajo y ejecútalos desde ahí. Crean `salidas/` solos.
   ```bash
   python scripts/barrido.py ES "logopedia|costura moldes|wedding planner" 4
   python scripts/caza_final.py
   ```

## Cómo se usa en tres pasos

1. **Barrido** por oficio y país (10-12 keywords, 4-6 rondas):
   `python scripts/barrido.py ES "<kw1>|<kw2>|..." 4`
2. **Análisis y verificación**: `python scripts/caza_final.py` rankea por cohorte y abre las landings de los mejores, diciendo cuáles son infoproducto, formación o retail.
3. **Decidir** con la vara: `cerebro/vara.md`.

## Las cinco trampas que cuestan una tarde

1. **Dos navegadores a la vez = cuelgue silencioso.** Secuencial siempre.
2. **Chrome huérfanos**: si un barrido «se cuelga» en la primera keyword, no es Meta: son procesos viejos. Mátalos y reintenta.
3. **Clasificar por el copy falla.** Se clasifica abriendo la landing.
4. **Un DNS roto contamina el navegador**: un contexto aislado por sitio.
5. **Guardar por keyword**, no al final.

## Resultado de referencia

Con keywords de **formato** (`ebook`, `printables`, `planilha`): 3 modelables en 2.384 anuncios.
Con keywords de **oficio** (`logopedia`, `costura moldes`, `terapia ocupacional`): **4 modelables en 634**.

Ejemplos reales que salieron en esa caza: un PDF de 50 bolsos con moldes (cohorte 24/24), una plantilla de boda de $67 (192 días), un curso de lencería (186 días) y un pack de +1001 actividades de terapia ocupacional a $17.

## Licencia y atribución

- `skills/caza-oficios`, `cerebro/` y `scripts/`: de quien te pasa el kit. Úsalos y modifícalos.
- `skills/cazar`: proviene de un repositorio público **sin licencia declarada** (ver `ORIGEN.md`). Es contenido publicado públicamente, pero sin permiso explícito de redistribución: úsalo para ti y no lo revendas ni lo publiques como propio.

## Aviso de uso

Todo el kit lee datos **públicos** de la Biblioteca de Anuncios, en volumen moderado y con pausas. No descarga ni reutiliza creatividades ajenas: solo cuenta anuncios, fechas y destinos para decidir qué modelar.
