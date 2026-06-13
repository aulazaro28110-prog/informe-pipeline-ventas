# 📊 Generador de Informe Semanal de Pipeline
### Script Python que convierte una exportación CSV del CRM en un informe de ventas accionable

> **Reduce de 45–60 minutos a 2 segundos** la redacción manual del informe semanal de pipeline.

---

## ¿Qué es este proyecto?
Un script en Python que lee los deals de un CRM desde un archivo CSV, calcula en
Python todas las métricas de ventas clave (pipeline total y ponderado, dinero en
riesgo, ticket medio, tasa de conversión, previsión del mes, reparto por etapa,
deals estancados y en riesgo) y redacta el informe automáticamente en dos
formatos: texto (`.md`) y web (`.html`).

## Archivos del proyecto
| Archivo | Descripción |
|---------|-------------|
| `deals.csv` | Datos de entrada (24 deals ficticios de ejemplo) |
| `generar_informe.py` | Script principal con toda la lógica |
| `informe_semanal.md` | Salida: informe en texto |
| `informe_semanal.html` | Salida: informe en web (tema oscuro + gráfico de barras) |
| `README.md` | Documentación completa del proyecto |
| `RESUMEN.md` | Este documento |

## Conceptos Python aplicados
- **Funciones** (`def`) separadas por responsabilidad: leer datos, calcular métricas, redactar texto, generar HTML, guardar archivos.
- **Módulo `csv`** para leer datos reales sin librerías externas.
- **Módulo `datetime`** para calcular días sin actividad, días hasta el cierre y la fecha de hoy automática.
- **Diccionarios** para transportar las métricas de forma ordenada.
- **Condicionales y bucles** (`if/elif/else`, `for`) para clasificar cada deal.
- **Manejo de errores** (`try/except`, `raise ValueError`) para descartar filas sucias sin romper el programa.
- **`sys.argv`** para pasarle cualquier CSV por línea de comandos.
- **Variables de entorno** (`os.environ`) para activar la API sin escribir la clave en el código.
- **`html.escape`** para generar un HTML seguro.

## Decisión técnica que sostiene el proyecto
> **Las cuentas las hace Python; la IA o la plantilla solo dan forma al texto.**
> Nunca se le pasa el CSV crudo a un modelo de lenguaje para que sume, porque los
> modelos se inventan cifras. Primero se calculan los números de forma fiable y
> solo después se convierten en prosa. Esa separación (cálculo ↔ redacción) es lo
> que hace que el informe sea de fiar.

## Reglas de negocio (configurables al inicio del script)
- **Estancado:** un deal sin actividad en más de `14` días (`DIAS_PARA_ESTANCADO`).
- **Cierre inminente:** cierre en `7` días o menos (`DIAS_CIERRE_INMINENTE`).
- **"Esta semana":** cierres en los últimos `7` días (`DIAS_VENTANA_RECIENTE`).
- **Etapas tempranas / cerradas:** listas editables para ajustar el cálculo a cada equipo.

## Resultados de la última ejecución (13/06/2026)
- 📥 Deals activos: **22**
- 💰 Pipeline total: **439.900 €** · ponderado: **271.500 €**
- ⚠️ Dinero en riesgo: **122.700 €** (28 % del pipeline)
- 🎟️ Ticket medio del deal activo: **19.995 €**
- 📈 Tasa de conversión histórica: **50 %**
- 🔮 Previsión ponderada de cierre este mes: **126.620 €** (10 deals)
- 💤 Deals estancados: **7** · 🚨 en riesgo: **6**

### Top 3 mayores oportunidades
| Empresa | Importe | Probabilidad |
|---------|---------|--------------|
| Consultora Norte | 64.000 € | 85 % |
| Hotel Mirasierra | 58.000 € | 70 % |
| Seguros Atlante | 46.000 € | 80 % |

## Dos modos de redacción
- **Modo plantilla (gratis):** Python puro, sin coste ni conexión. Funciona siempre.
- **Modo API (opcional, de pago):** si existe `ANTHROPIC_API_KEY`, la API de Claude redacta con un tono más natural. El programa lo detecta solo; si no hay clave, usa la plantilla.

## Para qué sirve
Útil para cualquier equipo comercial que cada semana tiene que mirar el CRM y
redactar el estado del pipeline a mano: cuánto hay en juego, qué deals están
parados y qué acciones priorizar. Lo que antes era casi una hora de trabajo
repetitivo (con riesgo de olvidar un deal) pasa a hacerse en segundos y revisando
el 100 % de los deals.

## Cómo ejecutarlo
```bash
python generar_informe.py                 # usa deals.csv por defecto
python generar_informe.py otros_deals.csv # o cualquier otro CSV con el mismo formato
```

---
*Datos de ejemplo 100 % ficticios. Creado con Claude Code (Anthropic) · Proyecto AI Engineer — Álvaro 2026*
