# 📊 Generador de Informe Semanal de Pipeline

> Convierte una exportación CSV del CRM en un informe de ventas claro y accionable **en 2 segundos** — el mismo que un responsable comercial tarda entre 45 y 60 minutos en redactar a mano cada semana.

---

## El problema

Cada lunes, alguien del equipo de ventas dedica casi una hora a mirar el CRM y escribir a mano el "estado del pipeline": cuánto hay en juego, qué deals están parados, cuáles se están escapando y qué hay que hacer. Es repetitivo, aburrido y propenso a que se cuele un olvido.

## La solución

Un script que:

1. **Lee** la exportación CSV del CRM (deals, etapas, importes, fechas).
2. **Calcula** las métricas clave en Python: pipeline total y ponderado, dinero en riesgo, ticket medio, tasa de conversión, previsión del mes, reparto por etapa, deals estancados y deals en riesgo.
3. **Redacta** el informe automáticamente, con un resumen, las mayores oportunidades, las alertas y las 3 acciones recomendadas de la semana.

## El impacto

| | Antes | Después |
|---|---|---|
| Tiempo por informe | ~45–60 min | ~2 segundos |
| Riesgo de olvidar un deal | Alto | Cero (revisa el 100%) |

---

## Ejemplo de salida

```markdown
## Resumen
- Deals activos: 22
- Pipeline total: 439.900 €
- Pipeline ponderado (por probabilidad): 271.500 €
- Dinero en riesgo: 122.700 € (28 % del pipeline)
- Ticket medio del deal activo: 19.995 €
- Tasa de conversión (histórica, todos los cierres): 50 %
- Previsión ponderada de cierre este mes: 129.120 € (11 deals)

## ✅ Acciones recomendadas para esta semana
1. Rescatar Metalúrgica Ebro: fecha de cierre ya superada.
2. Rescatar Bodegas Ribera Nova: fecha de cierre ya superada.
3. Empujar el mayor deal abierto: Consultora Norte (64.000 €).
```

El script genera el informe en **dos formatos a la vez**: texto en [`informe_semanal.md`](informe_semanal.md) y una **versión web** en [`informe_semanal.html`](informe_semanal.html) (tema oscuro, gráfico de barras en CSS puro, sin librerías externas).

---

## ✨ Emails de seguimiento con IA (la función estrella)

Además del informe, el script **redacta el email de seguimiento de cada deal en riesgo** y los guarda en [`emails_seguimiento.md`](emails_seguimiento.md). Aquí es donde la IA aporta algo que una regla `if/else` no puede: **escribir texto nuevo y distinto** para cada caso.

La gracia está en el contraste. El mismo deal, redactado de dos formas:

**🤖 Modo plantilla (gratis, sin IA)** — correcto, pero todos los emails salen calcados:
```
Asunto: Seguimiento — Metalúrgica Ebro

Hola Sergio Cruz,
Te escribo para retomar nuestra propuesta de Metalúrgica Ebro (39.000 €).
Lo marco como prioritario porque: fecha de cierre ya superada.
¿Tienes un hueco esta semana para hablarlo?
Un saludo, Alvaro
```

**🧠 Modo IA (con `ANTHROPIC_API_KEY`)** — personalizado y con tacto comercial:
```
Asunto: Retomamos lo de Metalúrgica Ebro antes de que se enfríe

Hola Sergio,
revisando la cuenta vi que la fecha que habíamos fijado para cerrar
ya quedó atrás, y no quiero que la propuesta (39.000 €) se nos enfríe
por una cuestión de calendario. ¿Sigue encajando por vuestra parte o
ha cambiado algo? Si te viene bien, te reservo 15 minutos esta semana
para ajustar lo que haga falta y darle salida.
Un abrazo, Álvaro
```

**Una regla nunca escribiría el segundo.** El script intenta el modo IA si hay clave; si no, usa la plantilla, así que **siempre produce algo** (con o sin coste).

> Sigue valiendo el principio del proyecto: Python decide *qué* deals están en riesgo (el cálculo); la IA solo *redacta* (el texto). Nunca se le pide a la IA que haga las cuentas.

---

## Decisión técnica que sostiene el proyecto

**Las cuentas las hace Python; el texto solo da forma a esos números.** Nunca se le pasa el CSV crudo a la IA para que sume: los modelos de lenguaje se inventan cifras. Por eso el programa primero calcula los números de forma fiable y solo después los convierte en prosa. Esta separación (cálculo ↔ redacción) es lo que hace que el informe sea de fiar.

## Robustez (aguanta datos reales)

Una exportación real del CRM viene sucia. El script lo tiene en cuenta:

- Si **el archivo no existe**, avisa con un mensaje claro en vez de romperse.
- Si una **fila trae un dato no válido** (importe vacío, fecha mal escrita, probabilidad fuera de 0–1, importe negativo), la **descarta avisando** y sigue con las demás.
- Si **no hay deals válidos**, lo dice y termina limpio.

## Dos modos de redacción

- **Modo plantilla (gratis):** genera el informe con Python puro. Funciona siempre, sin coste, sin conexión. **No necesita instalar nada** (solo librería estándar).
- **Modo API (opcional, de pago):** si defines la variable de entorno `ANTHROPIC_API_KEY`, el informe lo redacta la API de Claude con un tono más natural. El programa lo detecta solo; si no hay clave, usa la plantilla.

```bash
# Activar el modo API (opcional):
pip install anthropic
set ANTHROPIC_API_KEY=tu_clave   # en Windows
python generar_informe.py
```

## Cómo se usa

```bash
# Usa deals.csv por defecto:
python generar_informe.py

# O pásale cualquier otro CSV con el mismo formato:
python generar_informe.py otros_deals.csv
```

A partir del CSV de entrada genera **tres archivos**: `informe_semanal.md` (texto, ideal para pegar en un email o en Slack), `informe_semanal.html` (versión web que se abre en el navegador) y `emails_seguimiento.md` (los emails de seguimiento de los deals en riesgo). Todos se generan siempre, da igual el modo de redacción.

## Formato del CSV de entrada

```
id,empresa,contacto,etapa,importe_eur,responsable,ultima_actividad,cierre_previsto,probabilidad
2,Logística Tajo,Pedro Nieto,Negociación,42000,Alvaro,2026-06-10,2026-06-18,0.8
```

- `etapa`: Prospección, Cualificación, Propuesta enviada, Negociación, Cerrado ganado, Cerrado perdido.
- `importe_eur`: número. `probabilidad`: de 0 a 1. Fechas en formato `AAAA-MM-DD`.

## Reglas de negocio (configurables)

Definidas como constantes al inicio de `generar_informe.py`, para ajustarlas a cada equipo:

- `DIAS_PARA_ESTANCADO = 14` → un deal sin actividad en 14 días se marca como estancado.
- `DIAS_CIERRE_INMINENTE = 7` → cierre en 7 días o menos = urgente.
- `DIAS_VENTANA_RECIENTE = 7` → ventana que cuenta como "esta semana" para los cierres.
- `ETAPAS_TEMPRANAS` → fases en las que un cierre inminente es señal de riesgo.
- `ETAPAS_CERRADAS` → fases que ya no cuentan como pipeline activo.

## Estructura de archivos

| Archivo | Qué es |
|---|---|
| `generar_informe.py` | El script principal. |
| `deals.csv` | Datos de ejemplo (24 deals ficticios, sin datos reales). |
| `informe_semanal.md` | El informe en texto que produce el script (salida de ejemplo). |
| `informe_semanal.html` | El mismo informe en versión web (tema oscuro + gráfico de barras). |
| `emails_seguimiento.md` | Emails de seguimiento de los deals en riesgo (IA o plantilla). |
| `.gitignore` | Qué no se sube al repositorio (caché, claves...). |
| `README.md` | Este archivo. |
| `RESUMEN.md` | Resumen breve del proyecto y de los conceptos de Python aplicados. |

## Stack

Python 3 · `csv` · `datetime` · `html` · (opcional) API de Anthropic

---

## Conceptos de Python aplicados

Proyecto pensado también como práctica de programación. Conceptos que pone en juego:

- **Funciones** (`def`) con una responsabilidad cada una: leer datos, calcular métricas, redactar texto, generar HTML, guardar archivos.
- **Módulo `csv`** para leer datos reales desde un archivo, sin librerías externas.
- **Módulo `datetime`** para trabajar con fechas (días sin actividad, días hasta el cierre, fecha de hoy automática).
- **Diccionarios** para mover las métricas de un sitio a otro de forma ordenada.
- **Condicionales y bucles** (`if/elif/else`, `for`) para clasificar cada deal.
- **Manejo de errores** (`try/except`, `raise ValueError`) para aguantar datos sucios sin romperse.
- **Argumentos de línea de comandos** (`sys.argv`) para pasarle cualquier CSV.
- **Variables de entorno** (`os.environ`) para activar la API sin escribir nunca la clave en el código.
- **Generación de archivos** (`open`, `write`) en dos formatos: Markdown y HTML.
- **Escapado de texto** (`html.escape`) para que el HTML sea seguro y no se rompa con caracteres raros.

---

## Casos de uso reales

- **Responsable comercial**: prepara en segundos el informe de pipeline del lunes en vez de redactarlo a mano.
- **Dirección de ventas**: recibe siempre el mismo formato de informe, comparable semana a semana.
- **Equipo de ventas**: detecta automáticamente los deals estancados o en riesgo antes de que se enfríen.
- **Reporte a cliente/dirección**: la versión `.html` se abre en el navegador o se adjunta tal cual.

---

## Limitaciones conocidas

- Trabaja sobre una **exportación CSV**; no se conecta todavía en directo al CRM (eso sería el siguiente paso vía API).
- Las métricas son tan buenas como los datos del CSV: si una etapa está mal escrita, ese deal puede contarse de forma distinta a la esperada.
- El modo API es **de pago** y requiere una clave propia (`ANTHROPIC_API_KEY`); sin clave, el informe se redacta igual con la plantilla gratuita.

---

## Próximos pasos (escalabilidad)

- Conectar directamente con el CRM (HubSpot, Pipedrive, Salesforce) vía API en lugar de exportar a CSV.
- Enviar el informe automáticamente por email o a un canal de Slack cada lunes.
- Guardar el histórico semanal para ver la evolución del pipeline en el tiempo.
- Añadir gráficos adicionales (evolución mensual, embudo por etapa).

---

## Autor

**Álvaro Utazu Lázaro** · En formación como AI Engineer
Proyecto desarrollado con [Claude Code](https://claude.ai) (Anthropic) como parte del programa de aprendizaje práctico de IA.

---

*Datos de ejemplo 100% ficticios. El proyecto no usa ni almacena datos reales de clientes.*
