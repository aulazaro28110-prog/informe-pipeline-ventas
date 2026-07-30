# -*- coding: utf-8 -*-
"""
Generador de datos de ejemplo (deals.csv) para la demo.
=======================================================
Escribe un `deals.csv` REALISTA con fechas RELATIVAS A HOY. Así el informe de
ejemplo nunca sale "en llamas" (todo vencido/estancado) por culpa de fechas
viejas congeladas en el archivo.

Cada deal se define con OFFSETS en días respecto a hoy:
  - act_hace:   hace cuántos días fue la última actividad.
  - cierre_en:  dentro de cuántos días está previsto el cierre
                (un número negativo = fecha de cierre YA pasada).
Al ejecutar el script, esos offsets se convierten en fechas concretas usando
date.today(), y se guardan en deals.csv.

Uso:
  python generar_datos_demo.py
"""

import csv
from datetime import date, timedelta

HOY = date.today()

# (empresa, contacto, etapa, importe_eur, responsable, act_hace, cierre_en, prob)
# Mezcla pensada a propósito: la MAYORÍA sanos, unos pocos en riesgo, unos
# pocos estancados, y algunos cerrados (para la tasa de conversión).
DEALS = [
    # --- Sanos: actividad reciente y cierre en el futuro ---
    ("Logística Tajo",      "Pedro Nieto",   "Negociación",       42000, "Álvaro", 3, 15, 0.80),
    ("Consultora Norte",    "Marta Ruiz",    "Propuesta enviada", 64000, "Álvaro", 5, 25, 0.60),
    ("Innovatech",          "Luis Vera",     "Cualificación",     18000, "Carlos", 2, 30, 0.40),
    ("Grupo Salinas",       "Ana Gil",       "Negociación",       37000, "Álvaro", 6, 10, 0.75),
    ("Delta Foods",         "Sara Pons",     "Propuesta enviada", 28000, "Carlos", 4, 20, 0.55),
    ("Nube9",               "Iván Soto",     "Prospección",       12000, "Álvaro", 7, 40, 0.20),
    ("Vera & Co",           "Nadia Haddad",  "Cualificación",     22000, "Carlos", 8, 35, 0.35),
    ("Astra Bienes",        "Diego Ramos",   "Negociación",       51000, "Álvaro", 1, 18, 0.70),
    ("Ferrer Retail",       "Lucía Ferrer",  "Propuesta enviada", 33000, "Carlos", 9, 22, 0.50),
    ("OrbitMedia",          "Pablo Ortiz",   "Cualificación",     16000, "Álvaro", 3, 28, 0.30),
    # --- Sanos que cierran en los próximos días (alimentan la previsión del mes) ---
    ("Redes Cantábrico",    "Hugo Marín",    "Negociación",       35000, "Álvaro", 2,  2, 0.70),
    ("Aelia Software",      "Berta Lima",    "Propuesta enviada", 27000, "Carlos", 3,  4, 0.55),

    # --- En riesgo: cierre ya vencido ---
    ("Metalúrgica Ebro",    "Sergio Cruz",   "Negociación",       39000, "Álvaro", 4, -3, 0.65),
    ("Bodegas Ribera Nova", "Elena Sanz",    "Propuesta enviada", 26000, "Carlos", 6, -1, 0.50),
    # --- En riesgo: cierre inminente pero aún en fase temprana ---
    ("Domótica Sur",        "Clara Méndez",  "Prospección",       20000, "Álvaro", 2,  5, 0.20),

    # --- Estancados: sin actividad en más de 14 días (siguen activos) ---
    ("Casa Mateo",          "Tomás Ibáñez",  "Cualificación",     24000, "Carlos", 21, 30, 0.30),
    ("Grupo Vela",          "Sofía Romero",  "Propuesta enviada", 30000, "Álvaro", 18, 26, 0.45),
    ("Puerto Azul",         "Nuria Cano",    "Negociación",       45000, "Carlos", 25, 20, 0.60),

    # --- Cerrados ganados (2 en la última semana, 1 antiguo) ---
    ("Solaris SA",          "Ana García",    "Cerrado ganado",    40000, "Álvaro", 3,  -2, 1.0),
    ("Grupo Ledesma",       "Luis Pérez",    "Cerrado ganado",    22000, "Carlos", 5,  -5, 1.0),
    ("Marina Sur",          "Marta Ruiz",    "Cerrado ganado",    31000, "Álvaro", 20, -20, 1.0),

    # --- Cerrados perdidos (1 reciente, 1 antiguo) ---
    ("Vientos SL",          "Elena Sanz",    "Cerrado perdido",   15000, "Carlos", 6,  -3, 0.0),
    ("Ática Group",         "Pablo Ortiz",   "Cerrado perdido",   19000, "Álvaro", 25, -25, 0.0),
]

COLUMNAS = ["id", "empresa", "contacto", "etapa", "importe_eur",
            "responsable", "ultima_actividad", "cierre_previsto", "probabilidad"]


def construir_filas():
    """Convierte los offsets en fechas concretas relativas a HOY."""
    filas = []
    for i, (empresa, contacto, etapa, importe, resp, act_hace, cierre_en, prob) in enumerate(DEALS, start=1):
        filas.append({
            "id": i,
            "empresa": empresa,
            "contacto": contacto,
            "etapa": etapa,
            "importe_eur": importe,
            "responsable": resp,
            "ultima_actividad": (HOY - timedelta(days=act_hace)).isoformat(),
            "cierre_previsto": (HOY + timedelta(days=cierre_en)).isoformat(),
            "probabilidad": prob,
        })
    return filas


def main():
    filas = construir_filas()
    with open("deals.csv", "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"Escrito deals.csv con {len(filas)} deals, fechas relativas a {HOY.isoformat()}.")


if __name__ == "__main__":
    main()
