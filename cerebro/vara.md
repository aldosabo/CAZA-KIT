# La vara — criterios de caza, escritos

Sin esto, cada búsqueda empieza de cero y el criterio vive en mi cabeza (que es donde se pierde).

## 1. Qué cuenta como producto modelable

Un candidato solo pasa si cumple **las cinco**:

| # | Condición | Cómo se comprueba |
|---|---|---|
| 1 | Vende un **digital** (PDF, plantillas, imprimibles, curso descargable) | Abriendo la landing, no por el copy del anuncio |
| 2 | Página sin marca personal | Nombre de producto o genérico; sin cara de gurú ni «mi método» |
| 3 | Front-end autónomo | No es la puerta barata a una mentoría o a un back-end high-ticket |
| 4 | Entrega inmediata y precio visible | Precio en la landing y descarga tras pagar |
| 5 | El comprador es un **colectivo con nombre** | «logopedas», «maestras de primaria», «fisios», no «todo el mundo» |

Si falla una, se descarta y se anota el motivo en una línea.

> Esta vara está en código en `scripts/nucleo.py` (`VARA`, `nivel()`, `clasifica_landing()`).
> Si cambias un umbral aquí, cámbialo allí; las pruebas (`tests/`) fallan si se desalinean.

## 2. Umbrales numéricos

| Señal | Mirar | Profundizar | Ganador |
|---|---|---|---|
| Cohorte 7+ **de un mismo anunciante** | ≥ 3 | ≥ 8 | ≥ 20 |
| Antigüedad máxima de un anuncio vivo | ≥ 21 días | ≥ 45 días | ≥ 120 días |
| Creativos duplicados del mismo ángulo | 3 | 6 | 10+ |
| Competidores en el mercado destino | — | 0-3 | 0-1 |

**Cómo se combinan:** cada nivel exige cohorte **y** antigüedad de ese nivel (ganador = cohorte ≥ 20 y un anuncio vivo de ≥ 120 días). Con cohorte ≥ 3 nunca baja de «mirar». 10+ duplicados suben un escalón solo si la antigüedad ya lo respalda.

**La cohorte es lo que cuenta**, no el total de anuncios activos. Una página con 100 ads y 0 en cohorte es una fábrica de churn.

## 3. Qué se descarta de inmediato

- **Retail físico**: herbolarios, mercerías, tiendas de lanas, papelerías. Aunque tengan 180 ads.
- **Apps y SaaS**: Play Store, App Store, «descarga la app», plataformas.
- **Cursos corporativos y de compliance**: formación bonificada, seguridad laboral, certificaciones oficiales.
- **Marca personal consolidada**: nombre de persona + autoridad + escalera de valor.
- **Advertorial sin oferta**: página que no vende nada al final.
- **Nichos que ya tienen un whale**: 50+ ads de un solo jugador en el destino.

## 4. La regla que evita el sesgo principal

> **No se clasifica por el texto del anuncio. Se clasifica abriendo la landing.**

El copy dice «gratis», «ebook», «guía» en todas partes. Lo que distingue un infoproducto de una tienda es el checkout: precio, entrega inmediata y producto descargable. Clasificar por dominio o por palabras clave inventa falsos positivos (una mercería con un blog de «guías») y falsos negativos (un producto de oficio en dominio propio).

## 5. Cómo se mide la puntería

Dos números, al final de cada caza:

```
tasa de señal   = anunciantes que pasan cohorte / anunciantes leídos
tasa de modelo  = modelables verificados / anunciantes que pasan cohorte
```

Referencia actual (caza de croché + multi-nicho, 2.384 anuncios leídos, 1.267 anunciantes):
**15 con señal digital (1,2 %) · 3 verificados como modelables (0,24 %)**.

Si una caza nueva no mejora al menos uno de los dos números, el cambio de método no sirvió.

## 6. Lo que hay que registrar siempre

`caza_final.py` lo hace solo en `salidas/historico.csv`. Por cada producto cazado: nicho, mercado, `page_id`, cohorte 7+/total, antigüedad máxima, destino, precio, tipo de embudo y **motivo del descarte si no pasa**. Sin el motivo, el histórico no enseña nada.
