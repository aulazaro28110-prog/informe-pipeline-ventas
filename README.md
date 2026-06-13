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

(Informe completo en [`informe_semanal.md`](informe_semanal.md).)

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

Genera el archivo `informe_semanal.md` a partir del CSV de entrada.

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
| `informe_semanal.md` | El informe que produce el script (salida de ejemplo). |
| `.gitignore` | Qué no se sube al repositorio (caché, claves...). |
| `README.md` | Este archivo. |

## Stack

Python 3 · `csv` · `datetime` · (opcional) API de Anthropic

---

*Datos de ejemplo 100% ficticios. El proyecto no usa ni almacena datos reales de clientes.*
