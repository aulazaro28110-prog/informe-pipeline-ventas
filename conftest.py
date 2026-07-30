"""Permite que los archivos de tests/ importen generar_informe.py.

pytest ejecuta este conftest.py al arrancar; aquí añadimos la carpeta del
proyecto al sys.path para que `import generar_informe` funcione desde tests/.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
