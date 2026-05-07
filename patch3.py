import sys

def patch_file():
    with open('SGEC/pages/simulation_chat.py', 'r') as f:
        content = f.read()

    search_block = """# Get statistics
def get_estadisticas(secret_key, grado, ceco_emp):
    from db.database_manager import execute_query, get_fernet, decrypt_val
    f = get_fernet(secret_key)
    res = execute_query("SELECT id_ceco, sueldo_base FROM Empleados WHERE grado_actual = ?", (grado,))
    s_mismo, s_otros = [], []
    for r in res:
        try:
            s = float(decrypt_val(f, r['sueldo_base']))
            if r['id_ceco'] == ceco_emp:
                s_mismo.append(s)
            else:
                s_otros.append(s)
        except: pass
    p_mismo = sum(s_mismo)/len(s_mismo) if s_mismo else 0
    p_otros = sum(s_otros)/len(s_otros) if s_otros else 0
    return p_mismo, p_otros, len(s_mismo), len(s_otros)

prom_mismo, prom_otros, n_mismo, n_otros = get_estadisticas(secret_key, contexto_empleado['grado_actual'], contexto_empleado['id_ceco'])"""

    replace_block = """# Get statistics
def get_estadisticas(secret_key, grado, ceco_emp):
    from db.database_manager import execute_query, get_fernet, decrypt_val
    f = get_fernet(secret_key)

    # Hay que desencriptar el grado en la base para comparar, o encriptar el grado buscado (si el grado está encriptado)
    # Sin embargo, en _decrypt_empleado_row, grado_actual es desencriptado.
    # Así que para buscar en DB tenemos que hacer un fetchall y buscar a nivel aplicación,
    # o bien encriptar el grado (pero en AES/Fernet no es determinista a menos que se fije el IV).
    # Como la BD es local y pequeña (SQLite), extraemos todos y filtramos en python:

    res = execute_query("SELECT id_ceco, grado_actual, renta_anual FROM Empleados")
    s_mismo, s_otros = [], []
    for r in res:
        try:
            r_grado = decrypt_val(f, r['grado_actual'])
            if str(r_grado).strip() == str(grado).strip():
                # En lugar de sueldo_base, ahora utilizamos renta_anual
                s = float(decrypt_val(f, r['renta_anual']))
                if r['id_ceco'] == ceco_emp:
                    s_mismo.append(s)
                else:
                    s_otros.append(s)
        except Exception as e:
            pass

    p_mismo = sum(s_mismo)/len(s_mismo) if s_mismo else 0
    p_otros = sum(s_otros)/len(s_otros) if s_otros else 0
    return p_mismo, p_otros, len(s_mismo), len(s_otros)

prom_mismo, prom_otros, n_mismo, n_otros = get_estadisticas(secret_key, contexto_empleado['grado_actual'], contexto_empleado['id_ceco'])"""

    content = content.replace(search_block, replace_block)

    search_block2 = """with col_stats:
    st.markdown(f"#### 📊 Equidad Interna (Grado {contexto_empleado.get('grado_actual', 'N/A')})")

    sueldo_actual = contexto_empleado.get('sueldo_base', 0)
    delta_mismo = sueldo_actual - prom_mismo if prom_mismo > 0 else 0
    delta_otros = sueldo_actual - prom_otros if prom_otros > 0 else 0

    c3, c4 = st.columns(2)
    c3.metric(f"Promedio Mismo Equipo (n={n_mismo})", f"${prom_mismo:,.2f}", f"{delta_mismo:,.2f} vs Actual", delta_color="inverse")
    c4.metric(f"Promedio Otros Equipos (n={n_otros})", f"${prom_otros:,.2f}", f"{delta_otros:,.2f} vs Actual", delta_color="inverse")

    st.caption("Comparativa de sueldo base contra colaboradores en el mismo grado/GGS.")"""

    replace_block2 = """with col_stats:
    st.markdown(f"#### 📊 Equidad Interna (Grado {contexto_empleado.get('grado_actual', 'N/A')})")

    renta_actual = contexto_empleado.get('renta_anual', 0)
    delta_mismo = renta_actual - prom_mismo if prom_mismo > 0 else 0
    delta_otros = renta_actual - prom_otros if prom_otros > 0 else 0

    c3, c4 = st.columns(2)
    c3.metric(f"Renta Promedio Equipo (n={n_mismo})", f"${prom_mismo:,.2f}", f"{delta_mismo:,.2f} vs Actual", delta_color="inverse")
    c4.metric(f"Renta Promedio Externa (n={n_otros})", f"${prom_otros:,.2f}", f"{delta_otros:,.2f} vs Actual", delta_color="inverse")

    st.caption("Comparativa de Renta Anual contra colaboradores en el mismo grado/GGS.")"""

    content = content.replace(search_block2, replace_block2)

    with open('SGEC/pages/simulation_chat.py', 'w') as f:
        f.write(content)

patch_file()
