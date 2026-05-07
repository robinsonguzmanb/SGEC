import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database_manager import execute_query, get_fernet, decrypt_val
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Debes iniciar sesión primero para acceder a esta página.")
    st.stop()
rol = st.session_state.get('rol')
if rol != "Administrador":
    st.error("No tienes permisos para acceder a esta página. Solo Administradores.")
    st.stop()
st.title("🕵️ Entorno de Pruebas de Usuario (Impersonate)")
st.markdown("Suplanta la vista de un usuario habilitado para auditar el sistema en modo espejo.")
secret_key = st.session_state['secret_key']
def get_usuarios_habilitados(secret_key):
    # Intentar obtener el nombre_usuario, si falla usar query viejo
    query = "SELECT email, rol, estatus_acceso, nombre_usuario, id_empleado FROM Usuarios WHERE estatus_acceso = 'Habilitado' AND rol != 'Administrador'"
    results = execute_query(query)
    if not results:
        query_fallback = "SELECT email, rol, estatus_acceso, id_empleado FROM Usuarios WHERE estatus_acceso = 'Habilitado' AND rol != 'Administrador'"
        results = execute_query(query_fallback)
        for r in results:
            r['nombre_usuario'] = 'Desconocido'
            
    f = get_fernet(secret_key)
    empleados = execute_query("SELECT id_empleado, nombre_completo FROM Empleados")
    emp_nombres = {e['id_empleado']: decrypt_val(f, e['nombre_completo']) for e in empleados} if empleados else {}
    
    for r in results:
        if not r.get('nombre_usuario') or r.get('nombre_usuario') == "Desconocido":
            if r.get('id_empleado') in emp_nombres:
                r['nombre_usuario'] = emp_nombres[r['id_empleado']]
            else:
                r['nombre_usuario'] = "Desconocido"
                
    return results

usuarios_lista = get_usuarios_habilitados(secret_key)
if not usuarios_lista:
    st.info("No hay otros usuarios habilitados en la base de datos para suplantar.")
    st.stop()
user_opciones = {f"{u.get('nombre_usuario', 'Desconocido')} | {u['email']} ({u['rol']})": u['email'] for u in usuarios_lista}
seleccion = st.selectbox("Selecciona un Usuario a suplantar:", ["-- Seleccionar --"] + list(user_opciones.keys()))
if st.button("Activar Modo Impersonate", type="primary"):
    if seleccion != "-- Seleccionar --":
        email_sel = user_opciones[seleccion]
        rol_sel = next(u['rol'] for u in usuarios_lista if u['email'] == email_sel)
        
        st.session_state['impersonating'] = True
        st.session_state['impersonate_email'] = email_sel
        st.session_state['impersonate_rol'] = rol_sel
        
        st.success(f"Modo suplantación activado para {email_sel}. Redirigiendo...")
        st.rerun()
    else:
        st.warning("Por favor selecciona un usuario.")
if st.session_state.get('impersonating', False):
    st.info(f"Actualmente suplantando a: {st.session_state.get('impersonate_email')} ({st.session_state.get('impersonate_rol')})")
    if st.button("Terminar Suplantación"):
        st.session_state['impersonating'] = False
        st.session_state['impersonate_email'] = None
        st.session_state['impersonate_rol'] = None
        st.success("Suplantación terminada.")
        st.rerun()