import sys

def patch_file():
    with open('SGEC/pages/simulation_chat.py', 'r') as f:
        content = f.read()

    search_block = """    renta_actual = contexto_empleado.get('renta_anual', 0)
    delta_mismo = renta_actual - prom_mismo if prom_mismo > 0 else 0
    delta_otros = renta_actual - prom_otros if prom_otros > 0 else 0"""

    replace_block = """    renta_actual = float(contexto_empleado.get('renta_anual', 0)) if contexto_empleado.get('renta_anual') is not None else 0.0
    delta_mismo = renta_actual - prom_mismo if prom_mismo > 0 else 0.0
    delta_otros = renta_actual - prom_otros if prom_otros > 0 else 0.0"""

    content = content.replace(search_block, replace_block)

    with open('SGEC/pages/simulation_chat.py', 'w') as f:
        f.write(content)

patch_file()
