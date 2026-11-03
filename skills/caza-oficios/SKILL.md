---
name: caza-oficios
description: Cazar productos digitales ganadores en la Biblioteca de Anuncios de Meta buscando por OFICIO y colectivo (logopedia, costura, terapia ocupacional, wedding planner, docentes) en vez de por formato, verificando cada candidato abriendo su landing. Usar cuando pidan "cazar productos", "buscar winners", "encontrar un infoproducto para modelar" o "analizar un nicho" en mercados hispanos o italianos.
---

# Caza por oficios

Complementa a `cazar` (mercados no hispanos, conector oficial). Esta corre **sin conector**, con navegador, para mercados en español e italiano.

## La lección que justifica esta skill

Buscar por **formato** (`ebook`, `printables`, `planilha`, `planner`) devuelve *productos de sistema*: agendas, retos, planillas. Buscar por **oficio** (`logopedia`, `costura moldes`, `terapia ocupacional`, `wedding planner`) devuelve lo que de verdad se vende en este nicho: **imprimibles y plantillas gremiales**.

Medido en la misma máquina: con keywords de formato, **3 modelables en 2.384 anuncios**; con keywords de oficio, **4 modelables en 634**.

## Regla de reparto de keywords

- **70 % oficio y colectivo** — la que trae los productos
- **20 % formato** — `fichas`, `cuadernillo`, `plantillas`, `protocolo`
- **10 % plataforma** — `hotmart`, `kiwify`, `payhip` para detectar dominios de infoproducto

Banco de 27 colectivos en ES/PT/IT: `cerebro/banco-keywords.md`.

## Los mercados de oficio son micro (y eso cambia el método)

Inventario real de anuncios activos en un día cualquiera:

| Keyword | País | Anuncios activos en total |
|---|---|---|
| `logopedia` | ES | 173 |
| `terapia ocupacional` | ES | 63 |
| `nutricionista planillas` | ES | **1** |
| `schede didattiche` | IT | 89 |
| `terapia occupazionale` | IT | 17 |

Tres consecuencias:

1. **Se puede leer el mercado entero.** En `logopedia` se leyeron 80-99 de 173: no hay muestreo, hay censo. La exhaustividad por gremio es realista.
2. **El techo del producto es bajo, y la competencia también.** Es el intercambio: menos volumen, menos rivales, menos ruido.
3. **Una keyword con menos de ~20 anuncios no es un hueco, es una keyword mal escrita.** Se poda antes de gastar el barrido.

## Antes de barrer: poda de keywords

Corre una keyword suelta y mira el campo `library=` que imprime el barrido:

```bash
python scripts/barrido.py ES "logopedia" 2
# [ES] logopedia   ads=80   library=173
```

- `library` < 20 → podar (sinónimo más usado, plural, o el oficio real: `fonoaudiología`, `estimulación del lenguaje`).
- `library` entre 20 y 400 → mercado micro: barrer con 4-6 rondas basta.
- `library` > 5.000 → mercado ancho: aquí el oficio pierde señal y conviene volver al filtro por cohorte.

## La vara (qué se considera ganador)

Se cumplen las cinco o se descarta:

1. Vende un **digital** (PDF, plantilla, imprimible, curso descargable)
2. Página **sin marca personal** (sin gurú con nombre y cara)
3. **Front-end autónomo** (no es la puerta a una mentoría cara)
4. **Precio visible y entrega inmediata**
5. El comprador es un **colectivo con nombre**, no «todo el mundo»

Umbrales: cohorte 7+ ≥ 3 mirar, ≥ 8 profundizar, ≥ 20 ganador. Antigüedad ≥ 21 / ≥ 45 / ≥ 120 días. Duplicados 3 / 6 / 10+.

**Cohorte = anuncios creados hace 7+ días y aún activos**, no el total. Una página con 100 ads y 0 en cohorte es una fábrica de churn.

## Arquetipos que están funcionando (con números reales)

| Arquetipo | Ejemplo real | Cohorte | Días | Precio | Equivalente en el vídeo de referencia |
|---|---|---|---|---|---|
| **PDF de moldes de un oficio** | 50 bolsos de tela con moldes | **24/24** | 52 | R$ 97 | *Leathercraft Hub* (200 patrones, 24/27 ads) |
| **Pack de actividades para un colectivo** | +1001 actividades de terapia ocupacional pediátrica | 6/6 | 56 | **$17** | *Neurokids* (100 actividades) |
| **Plantilla premium de nicho** | Hoja de cálculo para planificar la boda | 9/9 | **192** | $67-77 | *Talleres Listos* |
| **Curso de oficio con descuento** | Negocio de lencería de autor | 10/11 | **186** | — | Los cursos de *Música sin vueltas* / *Logopedia* |

Los cuatro comparten la forma: **un problema de un gremio concreto, resuelto en un archivo, con precio de impulso**. Ese es el molde que hay que buscar; el nicho da igual.

## Rendimiento por gremio (para no perder el tiempo)

En la misma caza, los gremios no rinden igual:

- **Buenos**: costura y manualidades, bodas, docentes, logopedia, terapia ocupacional. Traen producto digital con precio.
- **Malos**: fisioterapia, nutrición, comercio, contabilidad. Devuelven clínicas, apps y SaaS; casi nunca un PDF.

Si un gremio no ha dado un solo digital en 100 anuncios, se abandona y se pasa al siguiente. No se insiste.

## La señal de arbitraje que más aparece

**Producto de un país, tráfico de otro, sin traducir.** Ejemplo real: un PDF brasileño de moldes (precios en **R$**) anunciando en **España**. Señal de que el hueco está en español y nadie lo ha tomado.

Cómo se detecta: en la landing, comparar la **moneda del precio** con el **país del anuncio**. Si no coinciden, hay cuña. Es más fiable que mirar «cuántos competidores hay», porque mide lo que nadie está haciendo.

## Cuándo NO cazar

- **Desierto, no hueco**: cero o un anunciante con cohorte ≥3 y sin historial. No hay demanda validada; esperar no lo arregla.
- **Whale dominante**: 50+ ads en cohorte de un solo jugador en el mercado destino. No se compite de frente.
- **Gremio sin producto digital** tras 100 anuncios leídos.

## El podio siempre lo ocupa el retail

Dos cazas distintas, misma trampa: el anunciante con más cohorte era un comercio físico.

| Caso | Cohorte | Días | Qué vendía |
|---|---|---|---|
| LacariaRicami (IT) | 179/187 | 44 | lanas y mercería |
| Luvain (IT) | **190/208** | 65 | astaxantina en cápsulas |

**Regla: producto físico = descartado, salvo que tengas fabricante detrás.** Un suplemento o una
tienda exige inventario, logística y asumir claims de salud. Y ojo: estas tiendas esconden el precio
tras el carrito, así que parecen un embudo digital sin precio. Se detectan por señales de producto
(`capsule`, `softgel`, `integratore`, `suplemento`, `mg`, `tallas`), no por el precio.

**Nunca decidas con el primer puesto de la lista.** Mira qué vende antes de emocionarte con la cohorte.

## Pipeline

Los scripts viven en `scripts/`. Ejecutar desde la raíz del kit.

```bash
# 0. calibración: una keyword donde ya sabes que hay ganador conocido
python scripts/cazar_lib.py ES "logopedia"          # esperado: ~173 de library, 80+ ads

# 1. barrido (secuencial, un navegador; relanzar = continuar donde se quedó)
python scripts/barrido.py ES "logopedia|costura moldes|wedding planner" 4
python scripts/barrido.py IT --banco

# 2. vara + verificación de embudos en una pasada
python scripts/caza_final.py --top 10

# 3. tasas de la caza y comparación con la anterior
python scripts/revisar/tasa_oficio.py

# 4. para cada ✅: arsenal en varios países y hueco de arbitraje
python scripts/profundizar.py ES "<anunciante>" --dest <dominio> --mercados ES MX CO AR
```

Salidas en `salidas/`: `barrido_<PAIS>.json`, `caza_final.json`, `caza_final.md` (informe para leer y presentar), `historico.csv` (cada candidato con su motivo) y `tasas.csv`.

Al terminar, **presenta `salidas/caza_final.md`**: los ✅ con precio y nivel, los ⚠️ que conviene abrir a mano y las dos tasas.

## Reglas de ejecución que cuestan caro

1. **Nunca dos navegadores a la vez.** Dos barridos en paralelo se cuelgan sin dar error. Secuencial: 12 keywords en ~4 min.
2. **Matar Chrome huérfanos antes de empezar.** Un `job_kill` mata el wrapper, no el navegador hijo; los viejos se comen la CPU y el barrido «se cuelga» en la primera keyword. En una sesión real fueron 24 procesos y tres barridos perdidos:
   ```powershell
   Get-Process chrome | Where-Object { $_.StartTime -lt (Get-Date).AddHours(-2) } | Stop-Process -Force
   ```
   ```bash
   pkill -f "chrome.*--headless"
   ```
3. **Clasificar abriendo la landing, no por el texto.** El copy dice «ebook» y «gratis» en todas partes. Clasificar por dominio inventa falsos positivos (una zapatería con blog de guías) y falsos negativos (un PDF de moldes con dominio propio). En una caza real marcó «formación» a una zapatería y «sin oferta» a un PDF de R$ 97.
4. **Verificar en contexto aislado.** Un fallo de DNS contamina el navegador y los siguientes `goto` fallan en cadena: un `new_context` por sitio.
5. **Guardar después de cada keyword**, no al final.

## Los embudos y cómo se leen

| Tipo | Señal en la landing | Veredicto |
|---|---|---|
| PDF / imprimible | precio + «acceso inmediato» / «descarga» | ✅ modelable |
| Plantilla premium | precio alto ($60-100), una sola página | ✅ modelable |
| Reto gratuito → oferta | cuenta atrás, «gratis», luego precio | ✅ mecanismo modelable |
| Academia con titulación | «título», «certificación», sin precio en la home | ⚠️ servicio, no impulso |
| Tienda física | catálogo, carrito, envío | ❌ retail |
| Dominio caído | 404 o DNS sin resolver | ⚠️ no verificable |

**Atajo:** si la home no muestra precio y ofrece «solicita información» o «reserva una llamada», no es un infoproducto de impulso. Se descarta sin abrir el resto.

## Métricas de la caza (obligatorias)

```
tasa de señal  = anunciantes con cohorte ≥3 / anunciantes leídos
tasa de modelo = modelables verificados / candidatos verificados
```

Referencia real: **13,4 % de señal** y **50 % de modelo** (307 anunciantes, 8 verificados, 4 modelables). Si una caza nueva no mejora alguna de las dos, el cambio de método no sirvió.

## Qué NO se copia del ganador

Nunca el copy, las imágenes ni los testimonios. Se copia **el dispositivo**: la comparativa «antes/después», el precio ancla, el tipo de producto. Traducir su gancho literal es plagio, no inspiración.

## Aviso sobre `cazar`

`skills/cazar/` viene de un repositorio público sin licencia declarada (ver `ORIGEN.md`). Úsala para ti; no la revendas ni la publiques como propia.
