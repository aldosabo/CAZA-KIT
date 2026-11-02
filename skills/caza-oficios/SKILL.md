---
name: caza-oficios
description: Cazar productos digitales ganadores en la Biblioteca de Anuncios de Meta buscando por OFICIO y colectivo (logopedia, costura, terapia ocupacional, wedding planner, docentes) en vez de por formato, verificando cada candidato abriendo su landing. Usar cuando pidan "cazar productos", "buscar winners", "encontrar un infoproducto para modelar" o "analizar un nicho" en mercados hispanos o italianos.
---

# Caza por oficios

Complementa a `cazar` (que busca en mercados no hispanos con el conector oficial). Esta corre **sin conector**, con navegador, y está pensada para mercados en español e italiano.

## La lección que justifica esta skill

Buscar por **formato** (`ebook`, `printables`, `planilha`, `planner`) devuelve *productos de sistema*: agendas, retos, planillas. Buscar por **oficio** (`logopedia`, `costura moldes`, `terapia ocupacional`, `wedding planner`) devuelve lo que de verdad se vende en este nicho: **imprimibles y plantillas gremiales**.

Medido en la misma máquina: con keywords de formato, 3 modelables en 2.384 anuncios. Con keywords de oficio, **4 modelables en 634**.

## Regla de reparto de keywords

- **70 % oficio y colectivo** — la que trae los productos
- **20 % formato** — `fichas`, `cuadernillo`, `plantillas`, `protocolo`
- **10 % plataforma** — `hotmart`, `kiwify`, `payhip` para detectar dominios de infoproducto

Banco completo de 27 colectivos en ES/PT/IT: `cerebro/banco-keywords.md`.

## La vara (qué se considera ganador)

Se cumplen las cinco o se descarta:

1. Vende un **digital** (PDF, plantilla, imprimible, curso descargable)
2. Página **sin marca personal** (sin gurú con nombre y cara)
3. **Front-end autónomo** (no es la puerta a una mentoría caras)
4. **Precio visible y entrega inmediata**
5. El comprador es un **colectivo con nombre**, no «todo el mundo»

Umbrales: cohorte 7+ ≥ 3 para mirar, ≥ 8 para profundizar, ≥ 20 para ganador. Antigüedad ≥ 21 / ≥ 45 / ≥ 120 días. Duplicados 3 / 6 / 10+.

**Cohorte = anuncios creados hace 7+ días y aún activos**, no el total. Una página con 100 ads y 0 en cohorte es una fábrica de churn.

## Pipeline

Los scripts viven en el repositorio del kit (`scripts/`). Ejecutar desde la raíz del kit.

```bash
# 0. calibración: una keyword donde ya sabes que hay ganador conocido
python scripts/cazar_lib.py ES "logopedia"

# 1. barrido (secuencial, un navegador; relanzar = continuar donde se quedó)
python scripts/barrido.py ES "logopedia|costura moldes|wedding planner" 4
python scripts/barrido.py IT --banco            # keywords de oficio ya preparadas

# 2. vara + verificación de embudos en una pasada
python scripts/caza_final.py --top 10

# 3. tasas de la caza y comparación con la anterior
python scripts/revisar/tasa_oficio.py

# 4. para cada ✅: arsenal en varios países y hueco de arbitraje
python scripts/profundizar.py ES "<anunciante>" --dest <dominio> --mercados ES MX CO AR
```

Salidas en `salidas/`: `barrido_<PAIS>.json`, `caza_final.json`, `caza_final.md` (informe
para leer y presentar al usuario), `historico.csv` (cada candidato verificado con su motivo)
y `tasas.csv` (evolución de la puntería).

Al terminar una caza, **presenta al usuario el contenido de `salidas/caza_final.md`**: los ✅
con su precio y nivel, los ⚠️ que conviene abrir a mano y las dos tasas.

## Reglas de ejecución que cuestan caro si se ignoran

1. **Nunca dos navegadores a la vez.** Dos barridos en paralelo se cuelgan sin dar error. Secuencial: 12 keywords en ~4 min.
2. **Matar Chrome huérfanos antes de empezar.** Un `job_kill` mata el wrapper, no el navegador hijo. Los procesos viejos se comen la CPU y el barrido «se cuelga» en la primera keyword:
   ```powershell
   Get-Process chrome | Where-Object { $_.StartTime -lt (Get-Date).AddHours(-2) } | Stop-Process -Force
   ```
   ```bash
   pkill -f "chrome.*--headless"    # macOS / Linux
   ```
3. **Clasificar abriendo la landing, no por el texto.** El copy dice «ebook» y «gratis» en todas partes. Dominio y palabras clave inventan falsos positivos (una zapatería con blog de guías) y falsos negativos (un PDF de moldes con dominio propio).
4. **Verificar en contexto aislado.** Un fallo de DNS contamina el navegador y los siguientes `goto` fallan en cadena: un `new_context` por sitio.
5. **Guardar después de cada keyword**, no al final: si se cae, se pierde todo lo anterior.

## Los embudos que aparecen y cómo se leen

| Tipo | Señal en la landing | Veredicto |
|---|---|---|
| PDF / imprimible | precio + «acceso inmediato» / «descarga» | ✅ modelable |
| Plantilla premium | precio alto ($60-100), una sola página | ✅ modelable |
| Reto gratuito → oferta | cuenta atrás, «gratis», luego precio | ✅ mecanismo modelable |
| Academia con titulación | «título», «certificación», sin precio en la home | ⚠️ servicio, no impulso |
| Tienda física | catálogo, carrito, envío | ❌ retail |
| Dominio caído | 404 o DNS sin resolver | ⚠️ no verificable |

## Métricas de la caza (obligatorias)

```
tasa de señal  = anunciantes con cohorte ≥3 / anunciantes leídos
tasa de modelo = modelables verificados / candidatos verificados
```

Referencia real: 13,4 % de señal y 50 % de modelo en la caza por oficios (307 anunciantes, 8 verificados, 4 modelables).

## Qué NO se copia del ganador

Nunca el copy, las imágenes ni los testimonios. Se copia **el dispositivo**: la comparativa «antes/después», el precio ancla, el tipo de producto. Traducir su gancho literal es plagio, no inspiración.

## Aviso sobre `cazar`

`skills/cazar/` viene de un repositorio público sin licencia declarada (ver `ORIGEN.md`). Úsala para ti; no la revendas ni la publiques como propia.
