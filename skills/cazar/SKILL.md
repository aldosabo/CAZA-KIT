---
name: cazar
description: Busca productos winner en Facebook Ads Library en mercados de habla NO española y te trae los mejores anunciantes (30+ ads que llevan 7+ días corriendo en el país cazado). Usar cuando el usuario dice "cazar", "buscar winner", "buscar whales", "analizar nicho" o "espiar ads".
---

# Cazar winners en Ads Library

Skill autónoma. El argumento es el **nicho o keyword** a investigar (ej: "recetas keto", "IA para abogados"). No depende de ninguna otra skill ni de carpetas previas: corre sola y devuelve la shortlist en el chat (y guarda un `.md` si el usuario quiere).

## Qué hace por defecto

1. **Busca en mercados de habla NO española** (portugués, inglés, italiano, francés, alemán). Excluye explícitamente el mercado hispano: NO se generan keywords en español y se descarta cualquier creativo en español que se filtre.
2. Agrupa los resultados por anunciante y cuenta cuántos ads activos tiene cada uno.
3. Se queda con los **winners duros**: anunciantes con **~30+ ads que llevan 7+ días corriendo** sobre la misma oferta, contados **en el país cazado**. Los ads creados hoy no cuentan.
4. Los rankea por señales de escala y te devuelve la shortlist con link a la landing, cantidad de ads, antigüedad y el ángulo que están usando.

## Requisito ⚠️

Usa la herramienta **`ads_library_search` del conector oficial de Meta** (el de Facebook — NO un MCP de terceros). Tenés que tenerlo **instalado** y con al menos una cuenta de ads activa en la sesión. Si está diferida, cargarla con ToolSearch.
- Es **solo lectura**: no toca tu cuenta ni crea nada → cero riesgo de baneo.
- **Fallback sin conector**: si no lo tenés instalado, hacé la caza a mano en `facebook.com/ads/library` (Chrome MCP o captura de pantalla) con los mismos filtros y la misma lectura de señales. Más lento, pero funciona.

También se usa el **navegador (Browser MCP o Chrome MCP)** para el Paso 3 · Filtro B: entrar al embudo de cada candidato y verificar que sea una VSL/TSL/checkout real. Sin navegador no se puede cerrar la verificación de embudo → avisar y no dar candidatos por válidos.

## Paso 1 — Barrido en mercados NO hispanos

⚠️ La tool **solo permite INCLUIR países, no excluirlos** (no existe "todos menos español"). Por eso el mercado hispano se evita con dos palancas: (a) keywords SOLO en idiomas no españoles y (b) whitelist de países destino no hispanos.

Llamar a `ads_library_search` con:
- `search_terms`: **una** keyword o frase por llamada (es el texto del creativo). Para probar N variaciones → N llamadas. Correr 3-5 variaciones del nicho en idiomas NO españoles: **portugués + inglés + italiano/francés/alemán**. **Nunca generar keywords en español.**
- `countries`: apuntar a la **whitelist NO hispana** → `["BR", "US", "GB", "IT", "FR", "DE", "PT"]` (correr por país o en tandas). Omitir `countries` SOLO si querés barrido global, pero entonces **descartar en el análisis todo creativo en español**.
- `ad_active_status`: `ACTIVE` (default de caza; usar `ALL` si querés ver también los que pausaron).
- `limit`: hasta 50.
- `advertiser_request`: el pedido del usuario con sus palabras (ej: "cazá recetas keto").

Generar keywords por 4 ejes (**siempre en idioma NO español**): **formato** (ebook, guia, template, kit, método, protocolo...), **disparadores de compra impulsiva**, **footprints técnicos** (dominios de Hotmart/Gumroad/Payhip como `search_terms` — si el dominio aparece en el texto del creativo, cae) y **keywords del nicho traducidas al idioma destino**. Para Brasil funcionan: método, segredo, desafio, renda extra, secar barriga, reconquista, passo a passo. Para inglés: method, secret, challenge, blueprint, protocol, hack.

**Regla de exclusión de español:** si un creativo que cae está escrito en español, se descarta del análisis (no cuenta para el arsenal ni para el veredicto).

De cada ad la tool devuelve: texto del creativo, página, **fecha de creación** y `ad_snapshot_url` (vista visual del ad).

## Paso 2 — Contar el arsenal de cada anunciante

Del barrido salen páginas candidatas. Para cada anunciante prometedor, llamar de nuevo a `ads_library_search` con `page_ids: ["<id de la página>"]` **Y `countries: ["<ISO-2>"]`** → devuelve los ads de esa página en ESE mercado. Con eso se cuenta el arsenal real y la longevidad de cada ad.

> ⛔ **`page_ids` SIN `countries` es un error, no un atajo.** Sin filtro de país la tool devuelve el arsenal **global** de la página, que puede ser 3-4× el del mercado que estás cazando — y el link de Ads Library que después entregás SÍ va filtrado por país, así que el número y el link describen cosas distintas. Caso real (caza Colombia, 28-ago-2026): *Hijos con Carácter* dio **42 ads sin filtro y 13 con `countries:["CO"]`**. Se reportó 42, Franco abrió el link y vio otra realidad. **El conteo y el link se hacen sobre el mismo país, siempre.**

> 📌 **Anotar SIEMPRE dos datos por candidato: el `page_id` y el país donde está anunciando.** Los dos son obligatorios para armar el link de Ads Library que va en el output (ver §Output). El `page_id` viene en cada resultado de la tool; el país sale del `countries` de la búsqueda que lo trajo (y se confirma con la `currency` del ad: BRL→BR, EUR→IT/FR/DE/PT, GBP→GB, USD→US). Si un anunciante corre en más de un país, anotar el país principal y, si son relevantes, dar un link por país.

**El filtro madre (winner duro) — se mide sobre la COHORTE DE 7 DÍAS, no sobre el total:**

Para cada candidato, partir sus ads activos en dos grupos usando `ad_creation_time`:
- **Churn** — creados hace menos de 7 días. **No prueban nada**: son la tanda de hoy.
- **Cohorte 7+** — creados hace 7 días o más y **todavía activos**. Estos son los que sobrevivieron: nadie deja corriendo una semana lo que no vende.

**Pasa el filtro madre quien tiene ~30+ ads en la cohorte 7+, en el país cazado.** El total de activos es contexto, no evidencia.

> ⛔ **El error que este filtro existe para evitar** (caza Colombia, 28-ago-2026): se leyó el filtro como *"¿existe al menos un ad de 7+ días?"* en vez de *"¿cuántos ads llevan 7+ días?"*. Con esa lectura, una página que **recrea todo su arsenal cada mañana** pasa el filtro por un único sobreviviente. Los números reales de esa caza:
>
> | Anunciante | Activos en 🇨🇴 | Cohorte 7+ | Veredicto real |
> |---|---|---|---|
> | Megapack de Lectoescritura | 64 | **≥40** (cohortes a 10·14·16·29·38·54·63·65 d) | winner |
> | Hijos con Carácter | 13 | **7** | tester |
> | Paquete de Diseños | ~104 | **0** (ninguno pasa las 72 h) | fábrica de churn |
>
> Los tres "pasaban" con la lectura vieja. Solo el primero era real. **Un anunciante con 100 ads activos y 0 en la cohorte 7+ no es un whale: es una página que quema creativos.**

**Cómo se reporta (obligatorio):** siempre `cohorte 7+ / total activos` juntos, nunca el total solo. Y si la cohorte es chica, decirlo aunque el total impresione.

> La tool no filtra por fecha: trae `ad_creation_time` de cada ad → hacer la partición en el análisis. Ojo con el techo de `limit: 50`: si un candidato devuelve 50 resultados, hay más ads que no viste, así que la cohorte 7+ que contaste es un **piso**, no el número final — decirlo con "≥".

## Paso 3 — Filtros anti–falso positivo (OBLIGATORIO antes de rankear) ⛔

Volumen + longevidad NO alcanzan. Un anunciante puede tener 1.000 ads corriendo 3 meses y aun así ser un **falso positivo** para modelar. Antes de meter a cualquier candidato en la shortlist, tiene que pasar estos 3 filtros. Si falla uno, se descarta (o se marca como "no modelable" y se explica por qué).

### Filtro A — ¿Es una marca personal consolidada? → DESCARTAR
Las marcas personales fuertes (un coach/gurú con nombre propio, cara, autoridad y audiencia ya construida) **rompen la lógica de la caza**. Su infoproducto de entrada de $12-19 es un **tripwire / loss-leader**: no lo corren porque ese front-end sea rentable por sí solo, sino para **capturar comprador y escalarlo por su escalera de valor** (mentoría, high-ticket, comunidad) — ahí está el rédito real. Por lo tanto:
- Su volumen/longevidad valida **la marca y el back-end**, NO que el infoproducto de entrada sea rentable ni escalable de forma standalone.
- **Nosotros no tenemos esa marca ni esa escalera**, así que copiar su front-end nos deja sin el motor económico que lo sostiene → no es modelable.
- **Señales de marca personal a descartar**: nombre de persona como página, misma cara/voz en todos los creativos, autoridad ("como te enseñé", seguidores, prensa), webinar/evento en vivo, "mi método", venta de mentoría/coaching visible en el funnel.
- **Lo que SÍ queremos**: páginas **fantasma / sin marca personal** (nombre genérico o de producto, sin gurú detrás), que **viven o mueren por la economía del front-end**. Ahí el volumen sostenido SÍ prueba que el infoproducto de entrada es rentable solo → eso es lo modelable.

### Filtro B — Entrar al EMBUDO con el navegador (obligatorio, comprar con los ojos) 🔎
**Nunca asumir el funnel por el anuncio.** Para cada candidato que pasó el volumen/longevidad, **abrir la página del anuncio en el navegador** y recorrer el embudo hasta el checkout. No listar nada sin haber hecho este paso.

**Procedimiento (rápido, ~1-2 min por candidato):**
1. Abrir el `ad_snapshot_url` (Browser MCP `navigate`, o Chrome MCP si hace falta la sesión logueada). Ahí se ve el creativo y el **link de destino** (botón/CTA del anuncio).
2. **Seguir ese link de destino** hasta la landing real y avanzar el funnel un paso más (scrollear la página, buscar el botón de compra, llegar al checkout).
3. Leer la página con `get_page_text` / `read_page` y **clasificar el tipo de embudo**:
   - **VSL** (video sales letter — video largo + botón de compra),
   - **TSL / advertorial→VSL** (texto largo que **sí** empuja a una oferta con checkout),
   - **quiz/survey → oferta**,
   - **directo a checkout / página de producto con precio**.
4. Confirmar que la página **está diseñada para vender un infoproducto**. Puede ser de dos formas:
   - **Checkout visible directo**: precio + botón de compra a la vista.
   - **VSL/TSL con oferta diferida**: NO hace falta que el botón aparezca ya. Alcanza con que la página esté **construida alrededor de un video con una promesa clara** (hook/promesa arriba, video reproduciéndose, subtítulos/copy que venden, headline del tipo "descubrí cómo…"). El botón de compra suele aparecer **con retraso, recién al minuto 10-15** del video — es un patrón normal de las VSL, no un motivo para descartar.

> ⚠️ **No descartar por "no veo botón".** En VSL/TSL el CTA aparece tarde a propósito. La pregunta correcta no es "¿hay botón ahora?" sino **"¿esta página está diseñada para venderme algo?"**: ¿hay un video con una promesa, una oferta insinuada, un producto prometido adelante? Si sí → PASA (anotar "VSL con botón diferido"). Confirmar el precio/checkout es ideal, pero su ausencia en los primeros minutos **no** lo invalida.

**Qué es PASA vs FALSO POSITIVO:**
- ✅ **PASA**: el clic termina en una VSL/TSL/quiz/checkout **diseñada para vender un infoproducto** — hay promesa + video/oferta, aunque el botón esté diferido.
- ⛔ **FALSO POSITIVO típico**: el clic lleva a **una página de puro texto (advertorial/artículo) que NO empuja a ninguna oferta** — no hay video con promesa, no hay producto prometido, no hay CTA (ni diferido), es contenido que se agota en sí mismo. Si la página no está armada para vender nada, **no hay oferta que modelar → descartar** (por más ads que tenga). Igual de sospechoso: link roto, redirect a home genérica, o "solo junta leads/seguidores" sin ningún producto prometido.
- Anotar en el output: **tipo de embudo verificado** (VSL / TSL / quiz / directo), qué infoproducto vende y a qué precio. Si no se pudo verificar (link caído, requiere login, geobloqueo), decirlo explícito — no darlo por válido.

### Filtro C — ¿El front-end es el producto, o es carnada de un back-end? 
Aunque tenga BCL y venda algo, preguntarse **de dónde sale la plata**. Si el front-end barato es claramente la puerta a una escalera de valor cara (upsells agresivos a mentoría/coaching, marca detrás), el front-end **no está validado como producto rentable por sí solo**. Modelable = el infoproducto de entrada se sostiene solo.

> Regla de oro: **modelamos productos, no marcas.** Un winner válido es una oferta de front-end que un desconocido sin audiencia podría relanzar y que se banca sola. Si para funcionar necesita una marca personal o un back-end high-ticket que nosotros no tenemos, es un falso positivo.

## Señales de winner — escalera de certeza

Cuanto más arriba, menos apuesta:
> Todos los niveles se cuentan sobre la **cohorte 7+** (ads con 7 o más días corriendo, en el país cazado), nunca sobre el total de activos.

- **Nivel 1 — convierte**: 8+ ads en la cohorte, con antigüedad de 7-20 días.
- **Nivel 2 — escalando**: ~30 ads en la cohorte.
- **Nivel 3 — WHALE (la casi-segura)**: **50-100+ ads en la cohorte** sobre una misma oferta, y/o los mismos ads corriendo **45-90+ días** sin pausa. La señal más fuerte no es el tamaño de la cohorte sino su **escalonamiento**: cohortes sucesivas a 10, 20, 40, 60 días prueban que el anunciante fue dejando vivo lo que ganaba, tanda tras tanda. Nadie banca gasto perdedor 2-3 meses: la longevidad sostenida es la prueba de rentabilidad más dura que da la Library. Al detectar un whale, ir a profundidad: enumerar todo su arsenal con `page_ids`, mapear landings, precios y ángulos.
- **Duplicación de creativos**: el mismo creativo repetido 10-20 veces = ese ya ganó el test interno del anunciante. Anotar esos `ad_snapshot_url` aparte — son los ángulos a modelar primero.
- Todos los creativos apuntando a la MISMA landing (si apuntan a landings distintas, todavía está testeando).
- Sin "follow me ads" (perfiles que solo juntan seguidores no venden).
- Misma oferta corriendo en 5-10 fanpages distintas = se esconde de los cloners → convierte seguro.
- **Descartar marcas personales consolidadas** (ver Paso 3, Filtro A): su front-end es carnada de un back-end high-ticket que nosotros no tenemos → NO modelable, por más volumen/longevidad que tenga.
- **Descartar todo lo que no pase la verificación de embudo** (Paso 3, Filtro B): si al entrar no vende un infoproducto (advertorial sin checkout, página muerta), es falso positivo aunque tenga meses corriendo.
- Descartar fanpages con "fronts" duplicados que no gastan.

## Veredicto de competencia

Contar cuántos anunciantes distintos atacan la misma promesa:
- **ENTRAR**: 2-6 anunciantes activos con gasto sostenido y ninguno domina → demanda validada y espacio.
- **SUBNICHO**: 7+ anunciantes con creativos muy parecidos → validado pero saturado. Proponer 3 subnichos concretos (mismo dolor, avatar más específico).
- **DESCARTAR**: 0-1 anunciantes o ads que mueren a los pocos días → demanda no validada.
- **WHALE DOMINANTE**: un jugador domina con señales de Nivel 3 → no competirle de frente en su mercado. Modelar su oferta y lanzarla traducida en otro mercado con hueco (ver abajo).

## (Opcional) Arbitraje multi-mercado

Si encontrás un winner fuerte, chequeá si el mismo ángulo está libre en otro mercado. Repetir la búsqueda con `countries: ["<ISO-2>"]` traduciendo el término:
- 🇧🇷 Brasil (`["BR"]`) — suele ser la cuna de las olas low-ticket → mercado FUENTE
- 🇺🇸 EE.UU. (`["US"]`), 🇬🇧 Reino Unido (`["GB"]`), 🇮🇹 Italia (`["IT"]`), 🇫🇷 Francia (`["FR"]`), 🇩🇪 Alemania (`["DE"]`), 🇵🇹 Portugal (`["PT"]`)

**Orden de prioridad de destino** (mercados NO hispanos): 1) inglés (US/GB), 2) Europa (IT/FR/DE), 3) Brasil/Portugal. **El mercado hispano queda fuera del alcance de esta skill.** Se **modela** desde el mercado fuente (saturado, funnels maduros) y se **lanza** en un destino con 0-3 players débiles. Si en el destino ya aparecen testers con ads de pocos días, la ventana se está cerrando.

## Output

Devolver en el chat la **shortlist rankeada de 3-5 anunciantes** que pasaron TODOS los filtros (cohorte 7+ suficiente **en el país cazado**, **+ Paso 3: no es marca personal, embudo verificado que vende un infoproducto**), cada uno con:
- **Nombre de la página + link a su perfil de Ads Library filtrado por el país donde anuncia** (obligatorio, ver abajo) + link a la landing
- **`cohorte 7+ / total activos`** en ese país, y el escalonamiento de la cohorte (ej: "≥40 / 64 — cohortes a 10·16·29·54·65 d"). **Nunca el total solo.** Este par tiene que poder reproducirse abriendo el link que entregás: si no coincide, contaste mal.
- **Tipo de página**: fantasma/sin marca (✅ modelable) vs marca personal (⛔ descartar)
- **Embudo verificado**: a qué lleva el clic (advertorial→VSL→checkout / quiz / directo) + qué infoproducto vende y a qué precio. Si no vende nada verificable → no entra a la shortlist.
- Hook/ángulo principal (el dolor que atacan = lo validado)
- Los `ad_snapshot_url` de los creativos más duplicados (esos son los ángulos a modelar primero)

### 🔗 Link de Ads Library por anunciante — OBLIGATORIO

**Nunca presentar un anunciante sin el link a su perfil de Ads Library, y ese link SIEMPRE va filtrado por el país específico donde está anunciando.** Un link sin filtro de país mezcla mercados y hace inútil la lectura del arsenal.

Formato exacto (reemplazar `<PAIS>` por el ISO-2 y `<PAGE_ID>` por el id de la página):

```
https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=<PAIS>&view_all_page_id=<PAGE_ID>&search_type=page&media_type=all
```

Reglas:
- **Un link por anunciante, mínimo.** Si el anunciante corre la misma oferta en varias fanpages (patrón de esconderse de cloners), dar el link de **cada fanpage**, todas filtradas por país.
- Si corre en varios países, dar un link por país relevante en vez de uno global.
- `active_status=active` por defecto (es una caza de lo que está vivo). Cambiar a `all` solo si se está investigando el historial de una oferta.
- Este link es distinto del `ad_snapshot_url`: el snapshot muestra **un creativo**, este muestra **todo el arsenal de la página**. Se entregan los dos, no uno u otro.

⚠️ **Antes de presentar la shortlist, correr Paso 3 sobre cada candidato.** No listar nada sin haber (a) confirmado que no es marca personal consolidada y (b) entrado al embudo a verificar que vende un producto modelable. Es preferible una shortlist de 1-2 winners reales que 5 falsos positivos.

Cerrar con el veredicto (ENTRAR / SUBNICHO / DESCARTAR / WHALE) y, si aplica, el par mercado fuente→destino. Si el usuario quiere, guardar todo en un `01-caza.md`.

**GATE previo (Paso 3) — eliminatorio, no puntúa:** para siquiera entrar al scoring, el candidato debe (a) NO ser marca personal consolidada y (b) tener embudo verificado que vende un infoproducto modelable. Si falla el gate, queda afuera **por más score que sacaría** — un whale de 1.000 ads con marca personal, o un advertorial que no vende nada, NO son candidatos.

**Score de 4 señales** (solo para los que pasan el gate; 1 punto c/u): ① longevidad — la cohorte llega a 45+ días; ② volumen — 50+ ads **en la cohorte 7+** de un solo jugador sobre la misma oferta, en el país cazado; ③ duplicación — mismo creativo repetido 10+ veces **dentro de la cohorte** (repetirlo en el churn de hoy no cuenta); ④ hueco de arbitraje — sin equivalente fuerte en un mercado destino prioritario. **4/4 = candidata A** (examen aprobado, copiala); 3 = candidata B; ≤2 = observar, no entrar todavía.

Recordatorio: el whale valida la **OFERTA**, no te salva de un test sucio. Landing degradada, pixel ciego o un solo conjunto queman igual — cuando lances, armá el test en serio.
