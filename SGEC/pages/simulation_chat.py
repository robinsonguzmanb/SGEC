import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import datetime
from db.database_manager import get_empleados_por_lider, get_empleado_by_id, get_reglas_grado, get_ceco_completo, crear_reserva, aprobar_reserva, guardar_carta_emitida
from utils.ia_manager import simular_chat, generar_borrador_correo
from utils.pdf_generator import generar_carta_oferta
from utils.navigation import render_sidebar

render_sidebar()

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Debes iniciar sesión primero para acceder a esta página.")
    st.stop()
rol = st.session_state.get('rol')
impersonating = st.session_state.get('impersonating', False)
if not (rol == "Líder" or impersonating):
    st.error("No tienes permisos para acceder a esta página. Solo para Líderes (o Admins en modo Impersonate).")
    st.stop()
st.title("🤖 Chat de Simulación (Challenge Engine)")
secret_key = st.session_state['secret_key']
email_activo = st.session_state.get('impersonate_email') if impersonating else st.session_state.get('email_usuario')
empleados_lista = get_empleados_por_lider(secret_key, email_activo)
reglas_grado = get_reglas_grado(secret_key)
if not empleados_lista:
    st.info("No hay empleados cargados en la base de datos.")
    st.stop()
st.markdown("### 🧑‍💼 Selector de Colaborador")
empleado_opciones = {f"{e['nombre_completo']} ({e['id_empleado']})": e['id_empleado'] for e in empleados_lista}

col_sel, col_opt = st.columns([2, 1])
with col_sel:
    seleccion = st.selectbox("Busca y selecciona un colaborador de tu equipo:", ["-- Seleccionar --"] + list(empleado_opciones.keys()))

if seleccion == "-- Seleccionar --":
    st.info("💡 Selecciona a alguien para comenzar la simulación y ver sus métricas comparativas.")
    st.stop()

empleado_id = empleado_opciones[seleccion]
contexto_empleado = get_empleado_by_id(secret_key, empleado_id)
ceco_info = get_ceco_completo(secret_key, contexto_empleado['id_ceco'])
if not ceco_info:
    st.error("Error: Centro de costos no encontrado para este empleado.")
    st.stop()
saldo_disponible = ceco_info['presupuesto_anual'] - ceco_info['presupuesto_consumido'] - ceco_info['presupuesto_reservado']

# Get statistics
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

prom_mismo, prom_otros, n_mismo, n_otros = get_estadisticas(secret_key, contexto_empleado['grado_actual'], contexto_empleado['id_ceco'])

with col_opt:
    with st.expander("⚙️ Campos Adicionales", expanded=False):
        campos_extra = st.multiselect(
            "Seleccionar para visualizar:",
            ['renta_anual', 'correo_electronico', 'fecha_ingreso', 'fecha_ultimo_ajuste', 'id_jefe_directo'],
            default=[]
        )

st.divider()

col_data, col_stats = st.columns([1.2, 1])
with col_data:
    st.markdown(f"#### 📄 Ficha de: {contexto_empleado['nombre_completo']}")
    c1, c2 = st.columns(2)
    c1.metric("Sueldo Base", f"${contexto_empleado.get('sueldo_base', 0):,.2f}")
    c1.metric("Grado Actual", contexto_empleado.get('grado_actual', 'N/A'))
    c2.metric("Centro de Costos", contexto_empleado.get('id_ceco', 'N/A'))
    c2.metric("Saldo CECO Disponible", f"${saldo_disponible:,.2f}")
    
    if campos_extra:
        st.markdown("**Datos Complementarios:**")
        for campo in campos_extra:
            # Re-fetch the full employee to get those fields since get_empleado_by_id doesn't return them all by default
            from db.database_manager import execute_query, get_fernet, decrypt_val
            f = get_fernet(secret_key)
            full_data = execute_query(f"SELECT {campo} FROM Empleados WHERE id_empleado = ?", (empleado_id,))
            if full_data:
                val = full_data[0][campo]
                if campo in ['renta_anual', 'fecha_ingreso', 'fecha_ultimo_ajuste', 'id_jefe_directo']:
                    val = decrypt_val(f, val) if val else "No Registrado"
                st.write(f"- **{campo.replace('_', ' ').title()}:** {val}")

with col_stats:
    st.markdown(f"#### 📊 Equidad Interna (Grado {contexto_empleado.get('grado_actual', 'N/A')})")
    
    sueldo_actual = contexto_empleado.get('sueldo_base', 0)
    delta_mismo = sueldo_actual - prom_mismo if prom_mismo > 0 else 0
    delta_otros = sueldo_actual - prom_otros if prom_otros > 0 else 0
    
    c3, c4 = st.columns(2)
    c3.metric(f"Promedio Mismo Equipo (n={n_mismo})", f"${prom_mismo:,.2f}", f"{delta_mismo:,.2f} vs Actual", delta_color="inverse")
    c4.metric(f"Promedio Otros Equipos (n={n_otros})", f"${prom_otros:,.2f}", f"{delta_otros:,.2f} vs Actual", delta_color="inverse")
    
    st.caption("Comparativa de sueldo base contra colaboradores en el mismo grado/GGS.")

st.divider()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "estado_flujo" not in st.session_state:
    st.session_state.estado_flujo = "SIMULACION" 
if "ia_explicacion" not in st.session_state:
    st.session_state.ia_explicacion = ""
if "reserva_actual_id" not in st.session_state:
    st.session_state.reserva_actual_id = None
if "nuevo_sueldo_propuesto" not in st.session_state:
    st.session_state.nuevo_sueldo_propuesto = 0.0
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
if st.session_state.estado_flujo == "SIMULACION":
    prompt = st.chat_input("Describe las tareas o cambios salariales propuestos...")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analizando con Auditor IA..."):
                response = simular_chat(contexto_empleado, reglas_grado, st.session_state.messages, ceco_info)
                
                if response.strip().startswith("[DISCREPANCIA_DETECTADA]"):
                    texto_limpio = response.replace("[DISCREPANCIA_DETECTADA]", "").strip()
                    st.error("🚨 Inconsistencia de Grado Detectada por el Auditor Experto")
                    st.markdown(texto_limpio)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.estado_flujo = "BLOQUEADO_GRADO"
                    st.session_state.ia_explicacion = texto_limpio
                    st.rerun()
                elif response.strip().startswith("[PRESUPUESTO_EXCEDIDO]"):
                    texto_limpio = response.replace("[PRESUPUESTO_EXCEDIDO]", "").strip()
                    st.error("🛑 Presupuesto Excedido (The Budget Lock)")
                    st.markdown(texto_limpio)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.estado_flujo = "BLOQUEADO_PRESUPUESTO"
                    st.session_state.ia_explicacion = texto_limpio
                    st.rerun()
                else:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
elif st.session_state.estado_flujo in ["BLOQUEADO_GRADO", "BLOQUEADO_PRESUPUESTO"]:
    st.warning("⚠️ La simulación ha sido interrumpida por reglas de gobernanza.")
    
    colA, colB = st.columns(2)
    with colA:
        if st.button("Elevar Caso al Analista Experto / Pedir Excepción", width='stretch', type="primary"):
            
            monto_reserva = contexto_empleado['sueldo_base'] * 0.20 
            st.session_state.nuevo_sueldo_propuesto = contexto_empleado['sueldo_base'] + monto_reserva
            
            fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            desc = f"Reserva por validación de caso - Empleado {contexto_empleado['id_empleado']}"
            
            justificacion_ia = st.session_state.ia_explicacion
            
            id_res = crear_reserva(secret_key, contexto_empleado['id_ceco'], monto_reserva, desc, fecha_str, "EN_VALIDACION", justificacion_ia)
            
            st.session_state.reserva_actual_id = id_res
            st.session_state.estado_flujo = "ESPERANDO_APROBACION_HUMANA"
            
            st.info("✉️ Simulación de envío: Correo de validación enviado a experto_rrhh@empresa.com con el reporte de discrepancia.")
            borrador = generar_borrador_correo(contexto_empleado, st.session_state.ia_explicacion, "[Determinar]")
            with st.expander("Ver Borrador de Correo Enviado", expanded=False):
                st.code(borrador, language="text")
            
            st.rerun()
            
    with colB:
        if st.button("Ajustar Propuesta", width='stretch'):
            st.session_state.estado_flujo = "SIMULACION"
            st.session_state.messages = st.session_state.messages[:-2]
            st.rerun()
elif st.session_state.estado_flujo == "ESPERANDO_APROBACION_HUMANA":
    st.info("⏳ Esperando revisión del Analista de RRHH en el Dashboard de Business Partner. Puedes simularlo si vas a esa vista, o forzarlo aquí para pruebas rápidas.")
    
    if st.button("[Bypass Simulación: Forzar Aprobación]", type="primary"):
        aprobar_reserva(secret_key, st.session_state.reserva_actual_id, comentario_bp="Aprobado por Bypass Local")
        st.session_state.estado_flujo = "APROBADO"
        st.success("Aprobación forzada registrada exitosamente.")
        st.rerun()
elif st.session_state.estado_flujo == "APROBADO":
    st.success("✅ Propuesta Aprobada. Ya puedes generar la Carta Oferta oficial.")
    
    if st.button("Generar Carta Oferta PDF", type="primary"):
        fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        ruta_pdf, hash_pdf = generar_carta_oferta(
            empleado_id=contexto_empleado['id_empleado'],
            nombre=contexto_empleado['nombre_completo'],
            cargo=contexto_empleado['grado_actual'],
            nuevo_sueldo=st.session_state.nuevo_sueldo_propuesto
        )
        
        guardar_carta_emitida(secret_key, contexto_empleado['id_empleado'], st.session_state.reserva_actual_id, hash_pdf, fecha_str)
        
        st.session_state.estado_flujo = "FINALIZADO"
        st.success(f"Carta generada y guardada en {ruta_pdf}")
        st.info(f"Hash de Seguridad Registrado: {hash_pdf}")
        
        with open(ruta_pdf, "rb") as file:
            st.download_button(
                label="Descargar PDF",
                data=file,
                file_name=ruta_pdf.split('/')[-1],
                mime="application/pdf"
            )
elif st.session_state.estado_flujo == "FINALIZADO":
    st.success("Flujo completado. La reserva ha sido efectuada y la carta ha sido emitida.")
    if st.button("Volver al Inicio / Simular Otro Empleado"):
        st.session_state.messages = []
        st.session_state.estado_flujo = "SIMULACION"
        st.rerun()