# -*- coding: utf-8 -*-
"""
Pruebas del generador de informe de pipeline.
=============================================
Cubren las funciones de CÁLCULO (la parte de valor: los números). No probamos
la redacción con IA porque depende de una clave externa; sí probamos que las
métricas salen bien y que la lectura del CSV aguanta datos sucios.

Idea de cada prueba en una frase, para poder defenderla:
  - Construimos deals "a mano" con fechas relativas a HOY.
  - Llamamos a la función y comprobamos que el número que sale es el esperado.
"""

from datetime import timedelta

import generar_informe as gi


def hacer_deal(importe=1000, prob=0.5, etapa="Negociación", act_hace=1, cierre_en=10,
               empresa="X", contacto="Y", responsable="Z"):
    """Fabrica un deal ya "parseado" (con fechas date), como el que produce leer_deals."""
    return {
        "empresa": empresa, "contacto": contacto, "responsable": responsable,
        "etapa": etapa,
        "importe_eur": float(importe),
        "probabilidad": float(prob),
        "ultima_actividad": gi.FECHA_REFERENCIA - timedelta(days=act_hace),
        "cierre_previsto": gi.FECHA_REFERENCIA + timedelta(days=cierre_en),
    }


# ---------- Formato ----------

def test_eur_formatea_miles_con_punto():
    assert gi.eur(42000) == "42.000 €"
    assert gi.eur(0) == "0 €"


# ---------- Fechas ----------

def test_dias_sin_actividad_y_hasta_cierre():
    d = hacer_deal(act_hace=5, cierre_en=8)
    assert gi.dias_sin_actividad(d) == 5
    assert gi.dias_hasta_cierre(d) == 8


# ---------- Métricas de pipeline ----------

def test_pipeline_total_y_ponderado():
    deals = [hacer_deal(importe=1000, prob=0.5), hacer_deal(importe=3000, prob=1.0)]
    m = gi.calcular_metricas(deals)
    assert m["pipeline_total"] == 4000          # 1000 + 3000
    assert m["pipeline_ponderado"] == 3500      # 1000*0.5 + 3000*1.0


def test_cerrados_no_cuentan_como_activos():
    deals = [hacer_deal(etapa="Negociación", importe=1000),
             hacer_deal(etapa="Cerrado ganado", importe=9999)]
    m = gi.calcular_metricas(deals)
    assert len(m["activos"]) == 1               # el cerrado no está en el pipeline activo
    assert m["pipeline_total"] == 1000


def test_estancado_solo_si_pasa_de_14_dias():
    deals = [hacer_deal(act_hace=20, empresa="Vieja"),   # estancado
             hacer_deal(act_hace=3, empresa="Fresca")]   # no estancado
    m = gi.calcular_metricas(deals)
    empresas_estancadas = [d["empresa"] for d in m["estancados"]]
    assert empresas_estancadas == ["Vieja"]


def test_en_riesgo_por_cierre_vencido():
    deals = [hacer_deal(cierre_en=-3, empresa="Vencida"),   # cierre ya pasado
             hacer_deal(cierre_en=20, empresa="AunNo")]     # cierre futuro
    m = gi.calcular_metricas(deals)
    empresas_riesgo = [d["empresa"] for d, motivo in m["en_riesgo"]]
    assert empresas_riesgo == ["Vencida"]


def test_tasa_conversion():
    deals = [hacer_deal(etapa="Cerrado ganado"),
             hacer_deal(etapa="Cerrado ganado"),
             hacer_deal(etapa="Cerrado ganado"),
             hacer_deal(etapa="Cerrado perdido")]
    m = gi.calcular_metricas(deals)
    assert m["tasa_conversion"] == 0.75         # 3 ganados de 4 cerrados


def test_ticket_medio():
    deals = [hacer_deal(importe=1000), hacer_deal(importe=2000), hacer_deal(importe=3000)]
    m = gi.calcular_metricas(deals)
    assert m["ticket_medio"] == 2000            # media de 1000, 2000, 3000


# ---------- Lectura robusta del CSV ----------

def test_leer_deals_descarta_filas_invalidas(tmp_path):
    csv_texto = (
        "id,empresa,contacto,etapa,importe_eur,responsable,ultima_actividad,cierre_previsto,probabilidad\n"
        "1,Buena,Ana,Negociación,1000,Alvaro,2026-06-10,2026-06-18,0.8\n"        # válida
        "2,MalaProb,Leo,Negociación,1000,Alvaro,2026-06-10,2026-06-18,5\n"       # prob fuera de 0-1
        "3,MalImporte,Sara,Negociación,-50,Alvaro,2026-06-10,2026-06-18,0.5\n"   # importe negativo
    )
    ruta = tmp_path / "deals_test.csv"
    ruta.write_text(csv_texto, encoding="utf-8")
    deals = gi.leer_deals(str(ruta))
    assert len(deals) == 1                       # solo la fila válida sobrevive
    assert deals[0]["empresa"] == "Buena"


def test_leer_deals_archivo_inexistente_no_rompe():
    assert gi.leer_deals("no_existe_este_archivo.csv") == []
