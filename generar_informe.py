# -*- coding: utf-8 -*-
"""
Generador de Informe Semanal de Pipeline
=========================================
Lee una exportación CSV del CRM y genera un informe de ventas legible.

IDEA CLAVE (y decisión técnica que debes saber defender):
  - Python CALCULA los números (sumas, días, conteos).
  - La IA (o una plantilla) solo REDACTA el texto a partir de esos números.
  Nunca le pidas a la IA que haga las cuentas: se las inventaría.

Tiene dos modos para escribir el informe:
  - MODO PLANTILLA  -> gratis, en Python puro. Funciona siempre.
  - MODO API        -> usa la API de Claude (de pago). Se activa solo si
                       existe la variable de entorno ANTHROPIC_API_KEY.

Uso:
  python generar_informe.py [ruta_csv]    (por defecto: deals.csv)
"""

import csv
import html
import os
import sys
from datetime import date, datetime

# En Windows, esto evita errores con tildes y emojis en la consola.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# 1) REGLAS DE NEGOCIO  (esta es TU parte de valor: tócalas a tu criterio)
# ============================================================
# "hoy" es la fecha real del sistema, así el informe siempre va al día.
# (Si quisieras congelar una fecha para una demo, pon: date(2026, 6, 11).)
FECHA_REFERENCIA = date.today()        # "hoy" del informe
DIAS_PARA_ESTANCADO = 14               # sin actividad => estancado
DIAS_CIERRE_INMINENTE = 7              # cierre en <= 7 días => urgente
DIAS_VENTANA_RECIENTE = 7             # "esta semana" = cerrados en los últimos 7 días
ETAPAS_TEMPRANAS = ["Prospección", "Cualificación"]
ETAPAS_CERRADAS = ["Cerrado ganado", "Cerrado perdido"]
ARCHIVO_ENTRADA = "deals.csv"
ARCHIVO_SALIDA = "informe_semanal.md"
ARCHIVO_SALIDA_HTML = "informe_semanal.html"
ARCHIVO_EMAILS = "emails_seguimiento.md"   # emails de seguimiento de deals en riesgo


# ============================================================
# 2) LEER LOS DATOS
# ============================================================
def leer_deals(ruta):
    """Lee el CSV y devuelve una lista de diccionarios, ya con tipos correctos.

    Es tolerante a fallos: si el archivo no existe, o si una fila trae un dato
    mal escrito (un importe vacío, una fecha rara...), avisa y sigue, en lugar
    de romper el programa entero. Así aguanta una exportación real del CRM.
    """
    if not os.path.exists(ruta):
        print(f"❌ No encuentro el archivo '{ruta}'. ¿Está en esta carpeta?")
        return []

    deals = []
    descartadas = 0
    with open(ruta, encoding="utf-8") as f:
        # start=2 porque la fila 1 es la cabecera; los datos empiezan en la 2.
        for numero, fila in enumerate(csv.DictReader(f), start=2):
            try:
                fila["importe_eur"] = float(fila["importe_eur"])
                fila["probabilidad"] = float(fila["probabilidad"])
                fila["ultima_actividad"] = datetime.strptime(fila["ultima_actividad"], "%Y-%m-%d").date()
                fila["cierre_previsto"] = datetime.strptime(fila["cierre_previsto"], "%Y-%m-%d").date()
                # Validación de rangos: la probabilidad va de 0 a 1 y el importe
                # no puede ser negativo. Si no, lanzamos el mismo tipo de error
                # y la fila se descarta abajo como cualquier otro dato no válido.
                if not 0 <= fila["probabilidad"] <= 1:
                    raise ValueError(f"probabilidad fuera de 0-1: {fila['probabilidad']}")
                if fila["importe_eur"] < 0:
                    raise ValueError(f"importe negativo: {fila['importe_eur']}")
            except (ValueError, KeyError) as error:
                empresa = fila.get("empresa", "¿?")
                print(f"⚠️  Fila {numero} ({empresa}) descartada: dato no válido ({error}).")
                descartadas += 1
                continue
            deals.append(fila)

    if descartadas:
        print(f"   Se descartaron {descartadas} fila(s) con datos no válidos.")
    return deals


def dias_sin_actividad(deal):
    return (FECHA_REFERENCIA - deal["ultima_actividad"]).days


def dias_hasta_cierre(deal):
    return (deal["cierre_previsto"] - FECHA_REFERENCIA).days


# ============================================================
# 3) CALCULAR LAS MÉTRICAS  (Python hace las cuentas)
# ============================================================
def calcular_metricas(deals):
    activos = [d for d in deals if d["etapa"] not in ETAPAS_CERRADAS]
    ganados = [d for d in deals if d["etapa"] == "Cerrado ganado"]
    perdidos = [d for d in deals if d["etapa"] == "Cerrado perdido"]

    # Pipeline por etapa: cuántos deals y cuánto dinero en cada fase.
    por_etapa = {}
    for d in activos:
        etapa = d["etapa"]
        if etapa not in por_etapa:
            por_etapa[etapa] = {"num": 0, "importe": 0.0}
        por_etapa[etapa]["num"] += 1
        por_etapa[etapa]["importe"] += d["importe_eur"]

    # Estancados: activos sin actividad en X días.
    estancados = [d for d in activos if dias_sin_actividad(d) > DIAS_PARA_ESTANCADO]

    # En riesgo: cierre ya pasado, o muy cercano pero todavía en fase temprana.
    en_riesgo = []
    for d in activos:
        dc = dias_hasta_cierre(d)
        if dc < 0:
            en_riesgo.append((d, "fecha de cierre ya superada"))
        elif dc <= DIAS_CIERRE_INMINENTE and d["etapa"] in ETAPAS_TEMPRANAS:
            en_riesgo.append((d, "cierre inminente pero aún en fase temprana"))
    # Priorizamos por dinero en juego: el deal en riesgo más caro va primero.
    # par[0] es el deal de la tupla (deal, motivo).
    en_riesgo.sort(key=lambda par: par[0]["importe_eur"], reverse=True)

    pipeline_total = sum(d["importe_eur"] for d in activos)
    pipeline_ponderado = sum(d["importe_eur"] * d["probabilidad"] for d in activos)

    # Dinero en riesgo: importe de los deals marcados en riesgo y su peso sobre
    # el pipeline. Un % alto significa que mucho dinero pende de un hilo.
    importe_en_riesgo = sum(d["importe_eur"] for d, motivo in en_riesgo)
    pct_en_riesgo = importe_en_riesgo / pipeline_total if pipeline_total else 0.0

    top = sorted(activos, key=lambda d: d["importe_eur"], reverse=True)[:3]

    # --- Métricas de venta (Mejora 2) ---
    # Tasa de conversión: de los deals ya cerrados, ¿qué proporción se ganó?
    # El "if cerrados else 0" evita dividir entre cero si no hubo cierres.
    cerrados = len(ganados) + len(perdidos)
    tasa_conversion = len(ganados) / cerrados if cerrados else 0.0

    # Ticket medio: importe medio de un deal activo.
    ticket_medio = pipeline_total / len(activos) if activos else 0.0

    # Previsión del mes: deals activos cuyo cierre cae en el mes en curso,
    # ponderado por su probabilidad (lo que "de verdad" esperamos ingresar).
    cierres_mes = [
        d for d in activos
        if d["cierre_previsto"].year == FECHA_REFERENCIA.year
        and d["cierre_previsto"].month == FECHA_REFERENCIA.month
        and d["cierre_previsto"] >= FECHA_REFERENCIA   # solo lo que aún no ha vencido
    ]
    prevision_mes = sum(d["importe_eur"] * d["probabilidad"] for d in cierres_mes)

    # Cerrados "esta semana": solo los cerrados en los últimos 7 días (antes la
    # etiqueta decía "esta semana" pero en realidad contaba TODOS los cerrados).
    ganados_semana = [d for d in ganados
                      if 0 <= (FECHA_REFERENCIA - d["cierre_previsto"]).days <= DIAS_VENTANA_RECIENTE]
    perdidos_semana = [d for d in perdidos
                       if 0 <= (FECHA_REFERENCIA - d["cierre_previsto"]).days <= DIAS_VENTANA_RECIENTE]

    return {
        "activos": activos,
        "ganados": ganados,
        "perdidos": perdidos,
        "por_etapa": por_etapa,
        "estancados": estancados,
        "en_riesgo": en_riesgo,
        "pipeline_total": pipeline_total,
        "pipeline_ponderado": pipeline_ponderado,
        "importe_en_riesgo": importe_en_riesgo,
        "pct_en_riesgo": pct_en_riesgo,
        "top": top,
        "tasa_conversion": tasa_conversion,
        "ticket_medio": ticket_medio,
        "cierres_mes": cierres_mes,
        "prevision_mes": prevision_mes,
        "ganados_semana": ganados_semana,
        "perdidos_semana": perdidos_semana,
    }


def eur(n):
    """Formatea un número como euros: 42000 -> '42.000 €'."""
    return f"{n:,.0f} €".replace(",", ".")


def guardar(texto, ruta):
    """Escribe 'texto' en 'ruta' con codificación UTF-8 (sirve para .md y .html)."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


# ============================================================
# 4A) REDACTAR EL INFORME  ·  MODO PLANTILLA (gratis)
# ============================================================
def redactar_plantilla(m):
    L = []
    L.append(f"# Informe semanal de pipeline · {FECHA_REFERENCIA.strftime('%d/%m/%Y')}\n")

    L.append("## Resumen")
    L.append(f"- Deals activos: **{len(m['activos'])}**")
    L.append(f"- Pipeline total: **{eur(m['pipeline_total'])}**")
    L.append(f"- Pipeline ponderado (por probabilidad): **{eur(m['pipeline_ponderado'])}**")
    L.append(f"- Dinero en riesgo: **{eur(m['importe_en_riesgo'])}** "
             f"({m['pct_en_riesgo'] * 100:.0f} % del pipeline)")
    L.append(f"- Ticket medio del deal activo: **{eur(m['ticket_medio'])}**")
    L.append(f"- Tasa de conversión (histórica, todos los cierres): **{m['tasa_conversion'] * 100:.0f} %**")
    L.append(f"- Previsión ponderada de cierre este mes: **{eur(m['prevision_mes'])}** "
             f"({len(m['cierres_mes'])} deals)")
    L.append(f"- Cerrados esta semana (últimos {DIAS_VENTANA_RECIENTE} días): "
             f"{len(m['ganados_semana'])} ganados, {len(m['perdidos_semana'])} perdidos\n")

    L.append("## Pipeline por etapa")
    # Ordenadas de más dinero a menos, para ver de un vistazo dónde está el peso.
    for etapa, datos in sorted(m["por_etapa"].items(),
                               key=lambda par: par[1]["importe"], reverse=True):
        L.append(f"- {etapa}: {datos['num']} deals · {eur(datos['importe'])}")
    L.append("")

    L.append("## 🏆 Mayores oportunidades (top 3 por importe)")
    for d in m["top"]:
        L.append(f"- **{d['empresa']}** ({eur(d['importe_eur'])}) — "
                 f"{d['etapa']}, probabilidad {d['probabilidad'] * 100:.0f} %.")
    L.append("")

    L.append("## ⚠️ Deals en riesgo")
    if m["en_riesgo"]:
        for d, motivo in m["en_riesgo"]:
            L.append(f"- **{d['empresa']}** ({eur(d['importe_eur'])}) — {motivo}.")
    else:
        L.append("- Ninguno. Buen control de fechas.")
    L.append("")

    L.append("## 💤 Deals estancados (sin actividad > "
             f"{DIAS_PARA_ESTANCADO} días)")
    if m["estancados"]:
        for d in sorted(m["estancados"], key=dias_sin_actividad, reverse=True):
            L.append(f"- **{d['empresa']}** ({eur(d['importe_eur'])}) — "
                     f"{dias_sin_actividad(d)} días sin contacto, en {d['etapa']}.")
    else:
        L.append("- Ninguno.")
    L.append("")

    L.append("## ✅ Acciones recomendadas para esta semana")
    # La prioridad y el quitar repetidos viven en acciones_recomendadas().
    # Aquí solo resaltamos el nombre de la empresa en negrita Markdown.
    for i, (empresa, texto) in enumerate(acciones_recomendadas(m), 1):
        texto_md = texto.replace(empresa, f"**{empresa}**")
        L.append(f"{i}. {texto_md}")
    L.append("")

    return "\n".join(L)


# ============================================================
# 4B) REDACTAR EL INFORME  ·  MODO API (de pago, listo para activar)
# ============================================================
def redactar_api(m):
    """
    Convierte las métricas en un informe narrado con la API de Claude.
    Solo se ejecuta si existe ANTHROPIC_API_KEY. Si no, devuelve None y
    el programa usa la plantilla.
    """
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic   # pip install anthropic
    except ImportError:
        print("Aviso: falta la librería 'anthropic'. Usando modo plantilla.")
        return None

    # Pasamos a la IA los NÚMEROS YA CALCULADOS, no el CSV crudo.
    datos = redactar_plantilla(m)
    cliente = anthropic.Anthropic()
    respuesta = cliente.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=("Eres un analista de ventas. Reescribe estos datos como un "
                "informe semanal claro y profesional para un director comercial. "
                "No inventes cifras: usa solo las que te doy."),
        messages=[{"role": "user", "content": datos}],
    )
    return respuesta.content[0].text


# ============================================================
# 4B-bis) EMAILS DE SEGUIMIENTO  ·  lo que una regla NO puede hacer
# ============================================================
# Esta es la diferencia real frente al validador de leads: aquí la IA no
# "reordena" datos, GENERA texto nuevo (un email distinto para cada deal).
# Igual que siempre: Python decide QUÉ deals están en riesgo; la IA solo
# pone las palabras. Si no hay clave, una plantilla hace un email decente.

def redactar_email_plantilla(deal, motivo):
    """Email de seguimiento BÁSICO (plantilla, gratis).
    Sirve de respaldo si no hay clave de API y como punto de
    comparación con la versión que escribe la IA."""
    return (
        f"Asunto: Seguimiento — {deal['empresa']}\n\n"
        f"Hola {deal['contacto']},\n\n"
        f"Te escribo para retomar nuestra propuesta de {deal['empresa']} "
        f"({eur(deal['importe_eur'])}). Lo marco como prioritario porque: "
        f"{motivo}.\n\n"
        f"¿Tienes un hueco esta semana para hablarlo?\n\n"
        f"Un saludo,\n{deal['responsable']}"
    )


def _email_con_ia(cliente, deal, motivo):
    """Pide a Claude que escriba UN email de seguimiento para este deal.
    Le pasamos una FICHA con los datos ya calculados (nunca el CSV crudo).
    Si la llamada falla por lo que sea, cae a la plantilla: nunca rompe."""
    ficha = (
        f"Empresa: {deal['empresa']}\n"
        f"Persona de contacto: {deal['contacto']}\n"
        f"Comercial que firma el email: {deal['responsable']}\n"
        f"Importe del deal: {eur(deal['importe_eur'])}\n"
        f"Etapa actual: {deal['etapa']}\n"
        f"Motivo por el que urge: {motivo}"
    )
    try:
        respuesta = cliente.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=350,
            system=(
                "Eres un comercial B2B con tablas. Escribe un email de "
                "seguimiento breve (4-6 líneas), cercano y profesional, para "
                "reactivar este deal sin sonar agresivo. Empieza por una línea "
                "'Asunto: ...'. Usa SOLO los datos de la ficha, no inventes "
                "nada. Firma con el nombre del comercial."
            ),
            messages=[{"role": "user", "content": ficha}],
        )
        return respuesta.content[0].text
    except Exception as error:
        print(f"⚠️  La IA falló con {deal['empresa']} ({error}). Uso plantilla.")
        return redactar_email_plantilla(deal, motivo)


def redactar_emails_seguimiento(m):
    """Genera un email de seguimiento por cada deal en riesgo y los junta
    en un documento Markdown. Usa la IA si hay ANTHROPIC_API_KEY (tono
    natural, distinto en cada email); si no, la plantilla gratuita."""
    en_riesgo = m["en_riesgo"]
    if not en_riesgo:
        return "# 📧 Emails de seguimiento\n\n¡Ningún deal en riesgo esta semana! 🎉\n"

    # Preparamos el cliente de IA UNA sola vez (no en cada vuelta del bucle).
    cliente = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            cliente = anthropic.Anthropic()
        except ImportError:
            print("Aviso: falta la librería 'anthropic'. Emails en modo plantilla.")

    bloques = []
    for deal, motivo in en_riesgo:
        if cliente is not None:
            email = _email_con_ia(cliente, deal, motivo)
        else:
            email = redactar_email_plantilla(deal, motivo)
        bloques.append(f"## {deal['empresa']} — {motivo}\n\n{email}")

    modo = "IA (Claude)" if cliente else "plantilla (gratis)"
    cabecera = (
        f"# 📧 Emails de seguimiento de deals en riesgo\n"
        f"*Generados automáticamente · modo: {modo} · {len(en_riesgo)} email(s)*\n\n"
    )
    return cabecera + "\n\n---\n\n".join(bloques)


# ============================================================
# 4C) REDACTAR EL INFORME  ·  MODO HTML (web, tema oscuro, gráfico en CSS)
# ============================================================
def barra_css(valor, maximo):
    """Devuelve el ancho de una barra en %, proporcional al máximo (regla de tres).

    Si 'maximo' es el importe de la etapa más grande, esa etapa da 100 %, y una
    que valga la mitad da 50 %. Es pura presentación: no calcula nada de negocio.
    """
    if maximo <= 0:
        return 0.0
    return valor / maximo * 100


def acciones_recomendadas(m):
    """Hasta 3 acciones priorizadas, sin empresas repetidas.

    Devuelve una lista de tuplas (empresa, texto_plano). Separar la empresa del
    texto permite que cada salida resalte el nombre a su manera: negrita Markdown
    (**...**) en el .md, o <b>...</b> en el HTML. Lógica COMPARTIDA por ambos.
    """
    candidatas = []
    for d, motivo in m["en_riesgo"][:2]:
        candidatas.append((d["empresa"], f'Rescatar {d["empresa"]}: {motivo}.'))
    for d in sorted(m["estancados"], key=lambda x: x["importe_eur"], reverse=True)[:2]:
        candidatas.append((d["empresa"], f'Retomar contacto con {d["empresa"]} ({eur(d["importe_eur"])}).'))
    if m["top"]:
        d = m["top"][0]
        candidatas.append((d["empresa"], f'Empujar el mayor deal abierto: {d["empresa"]} ({eur(d["importe_eur"])}).'))

    acciones = []
    vistas = set()
    for empresa, texto in candidatas:
        if empresa not in vistas:
            vistas.add(empresa)
            acciones.append((empresa, texto))
    return acciones[:3]


def redactar_html(m):
    """Devuelve el informe como una página HTML completa y autocontenida.

    Tema oscuro, CSS incrustado (nada externo) y un gráfico de barras hecho solo
    con CSS. Reutiliza los números de calcular_metricas; aquí solo se da forma.
    """
    fecha = FECHA_REFERENCIA.strftime("%d/%m/%Y")

    estilo = """
    :root { --bg:#0d1117; --panel:#161b22; --texto:#e6edf3; --suave:#8b949e;
            --acento:#22d3ee; --borde:#30363d; }
    * { box-sizing:border-box; }
    body { margin:0; padding:2rem; background:var(--bg); color:var(--texto);
           font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif; line-height:1.5; }
    .contenedor { max-width:880px; margin:0 auto; }
    h1 { color:var(--acento); border-bottom:1px solid var(--borde); padding-bottom:.5rem; }
    h2 { margin-top:2rem; font-size:1.1rem; }
    .panel { background:var(--panel); border:1px solid var(--borde);
             border-radius:10px; padding:1rem 1.25rem; margin:1rem 0; }
    .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:.75rem; }
    .kpi { background:var(--bg); border:1px solid var(--borde); border-radius:8px; padding:.7rem 1rem; }
    .kpi .label { color:var(--suave); font-size:.8rem; }
    .kpi .valor { font-size:1.25rem; font-weight:700; }
    .fila { display:flex; align-items:center; gap:.75rem; margin:.45rem 0; }
    .fila .nombre { width:150px; color:var(--suave); font-size:.9rem; }
    .pista { flex:1; background:var(--bg); border-radius:6px; overflow:hidden; }
    .barra { height:22px; border-radius:6px; }
    .fila .importe { width:110px; text-align:right; font-variant-numeric:tabular-nums; }
    ul,ol { padding-left:1.2rem; margin:.3rem 0; }
    li { margin:.25rem 0; }
    .pie { color:var(--suave); font-size:.8rem; margin-top:2rem; text-align:center; }
    """

    colores = ["#22d3ee", "#34d399", "#a78bfa", "#f472b6", "#fbbf24", "#60a5fa"]

    L = []
    L.append("<!DOCTYPE html>")
    L.append('<html lang="es"><head>')
    L.append('<meta charset="utf-8">')
    L.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    L.append(f"<title>Informe de pipeline · {fecha}</title>")
    L.append(f"<style>{estilo}</style>")
    L.append("</head><body><div class='contenedor'>")

    L.append(f"<h1>📊 Informe semanal de pipeline · {fecha}</h1>")

    # Resumen (tarjetas KPI) — los mismos números que el .md.
    kpis = [
        ("Pipeline total", eur(m["pipeline_total"])),
        ("Pipeline ponderado", eur(m["pipeline_ponderado"])),
        ("Dinero en riesgo", f'{eur(m["importe_en_riesgo"])} · {m["pct_en_riesgo"] * 100:.0f} %'),
        ("Ticket medio", eur(m["ticket_medio"])),
        ("Conversión", f'{m["tasa_conversion"] * 100:.0f} %'),
        ("Previsión del mes", eur(m["prevision_mes"])),
    ]
    L.append('<div class="panel kpis">')
    for label, valor in kpis:
        L.append(f'<div class="kpi"><div class="label">{label}</div>'
                 f'<div class="valor">{valor}</div></div>')
    L.append("</div>")

    # Gráfico de barras por etapa (CSS puro: el ancho sale de barra_css).
    L.append("<h2>Pipeline por etapa</h2><div class='panel'>")
    etapas = sorted(m["por_etapa"].items(), key=lambda par: par[1]["importe"], reverse=True)
    maximo = max((datos["importe"] for _, datos in etapas), default=0)
    for i, (etapa, datos) in enumerate(etapas):
        ancho = barra_css(datos["importe"], maximo)
        color = colores[i % len(colores)]
        L.append('<div class="fila">'
                 f'<span class="nombre">{html.escape(etapa)}</span>'
                 f'<span class="pista"><span class="barra" style="width:{ancho:.0f}%;background:{color}"></span></span>'
                 f'<span class="importe">{eur(datos["importe"])}</span>'
                 "</div>")
    L.append("</div>")

    # Deals en riesgo.
    L.append("<h2>⚠️ Deals en riesgo</h2><div class='panel'><ul>")
    if m["en_riesgo"]:
        for d, motivo in m["en_riesgo"]:
            L.append(f'<li><b>{html.escape(d["empresa"])}</b> '
                     f'({eur(d["importe_eur"])}) — {html.escape(motivo)}.</li>')
    else:
        L.append("<li>Ninguno. Buen control de fechas.</li>")
    L.append("</ul></div>")

    # Deals estancados.
    L.append(f"<h2>💤 Deals estancados (&gt; {DIAS_PARA_ESTANCADO} días)</h2><div class='panel'><ul>")
    if m["estancados"]:
        for d in sorted(m["estancados"], key=dias_sin_actividad, reverse=True):
            L.append(f'<li><b>{html.escape(d["empresa"])}</b> ({eur(d["importe_eur"])}) — '
                     f'{dias_sin_actividad(d)} días sin contacto, en {html.escape(d["etapa"])}.</li>')
    else:
        L.append("<li>Ninguno.</li>")
    L.append("</ul></div>")

    # Acciones recomendadas (reutiliza la lógica priorizada y sin repetir).
    L.append("<h2>✅ Acciones recomendadas</h2><div class='panel'><ol>")
    for empresa, texto in acciones_recomendadas(m):
        seguro = html.escape(texto).replace(html.escape(empresa), f"<b>{html.escape(empresa)}</b>")
        L.append(f"<li>{seguro}</li>")
    L.append("</ol></div>")

    L.append('<p class="pie">Generado automáticamente · datos de ejemplo ficticios.</p>')
    L.append("</div></body></html>")
    return "\n".join(L)


# ============================================================
# 5) PROGRAMA PRINCIPAL
# ============================================================
def main():
    # El archivo CSV se puede pasar por línea de comandos. Ejemplos:
    #   python generar_informe.py                 -> usa deals.csv (por defecto)
    #   python generar_informe.py otros_deals.csv -> usa ese archivo
    ruta_csv = sys.argv[1] if len(sys.argv) > 1 else ARCHIVO_ENTRADA

    deals = leer_deals(ruta_csv)
    if not deals:
        print("No hay deals válidos que procesar. Revisa el archivo de entrada.")
        return

    metricas = calcular_metricas(deals)

    informe = redactar_api(metricas)        # intenta el modo de pago
    modo = "API (Claude)"
    if informe is None:                     # si no hay clave, gratis
        informe = redactar_plantilla(metricas)
        modo = "plantilla (gratis)"

    guardar(informe, ARCHIVO_SALIDA)                         # informe de texto (.md)
    guardar(redactar_html(metricas), ARCHIVO_SALIDA_HTML)    # informe web (.html)
    guardar(redactar_emails_seguimiento(metricas), ARCHIVO_EMAILS)  # emails (IA/plantilla)

    print(f"Informe generado con modo: {modo}")
    print(f"Fecha de referencia (hoy): {FECHA_REFERENCIA.strftime('%d/%m/%Y')}")
    print(f"Leídos {len(deals)} deals de '{ruta_csv}'.")
    print(f"Generados: {ARCHIVO_SALIDA} (texto), {ARCHIVO_SALIDA_HTML} (web) "
          f"y {ARCHIVO_EMAILS} (emails).")
    print(f"Pipeline activo: {eur(metricas['pipeline_total'])} | "
          f"En riesgo: {len(metricas['en_riesgo'])} | "
          f"Estancados: {len(metricas['estancados'])}")


if __name__ == "__main__":
    main()
