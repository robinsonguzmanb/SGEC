import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import hashlib
import string
import random
from db.database_manager import execute_query, get_connection, get_fernet, encrypt_val, decrypt_val
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Debes iniciar sesión primero para acceder a esta página.")
    st.stop()
rol = st.session_state.get('rol')
if rol != "Administrador":
    st.error("No tienes permisos para acceder a esta página. Solo Administradores.")
    st.stop()
st.title("🔐 Gestión de Accesos y Llaves Únicas")
st.markdown("Habilita usuarios, crea accesos manuales y genera llaves únicas.")
secret_key = st.session_state['secret_key']
def get_all_usuarios(secret_key):
    query = "SELECT email, id_empleado, nombre_usuario, rol, estatus_acceso, fecha_ultimo_acceso, llave_enc FROM Usuarios ORDER BY email"
    results = execute_query(query)
    
    # Si devuelve vacío, puede ser porque execute_query silencia el error de que la columna no existe aún
    if not results:
        query_fallback = "SELECT email, id_empleado, rol, estatus_acceso, fecha_ultimo_acceso FROM Usuarios ORDER BY email"
        results = execute_query(query_fallback)
        for r in results:
            r['nombre_usuario'] = "Desconocido"
            r['llave_enc'] = None
            
    f = get_fernet(secret_key)
    
    empleados = execute_query("SELECT id_empleado, nombre_completo FROM Empleados")
    emp_nombres = {e['id_empleado']: decrypt_val(f, e['nombre_completo']) for e in empleados} if empleados else {}
    
    for r in results:
        if not r.get('nombre_usuario') or r.get('nombre_usuario') == "Desconocido":
            if r.get('id_empleado') in emp_nombres:
                r['nombre_usuario'] = emp_nombres[r['id_empleado']]
            else:
                r['nombre_usuario'] = "Desconocido"
                
        if r.get('llave_enc'):
            r['Llave de Acceso'] = decrypt_val(f, r['llave_enc'])
        else:
            r['Llave de Acceso'] = "No generada (Vacía)"
        
        if 'llave_enc' in r:
            del r['llave_enc']
            
    return results
def generar_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
def actualizar_usuario(secret_key, email, rol, estatus, nombre_usuario=None, id_empleado=None, hashed_key=None, plain_key=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        f = get_fernet(secret_key)
        
        updates = ["rol = ?", "estatus_acceso = ?"]
        params = [rol, estatus]
        
        if nombre_usuario is not None:
            updates.append("nombre_usuario = ?")
            params.append(nombre_usuario)
            
        if id_empleado is not None:
            updates.append("id_empleado = ?")
            params.append(id_empleado)
            
        if hashed_key:
            updates.append("hashed_key = ?")
            params.append(hashed_key)
            llave_enc = encrypt_val(f, plain_key) if plain_key else None
            try:
                cursor.execute(f"UPDATE Usuarios SET {', '.join(updates)}, llave_enc = ? WHERE email = ?", tuple(params) + (llave_enc, email))
                conn.commit()
                return
            except Exception:
                pass
                
        query = f"UPDATE Usuarios SET {', '.join(updates)} WHERE email = ?"
        cursor.execute(query, tuple(params) + (email,))
        conn.commit()
    finally:
        conn.close()
def crear_usuario(secret_key, email, id_empleado, nombre_usuario, rol, estatus, hashed_key, plain_key=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        f = get_fernet(secret_key)
        llave_enc = encrypt_val(f, plain_key) if plain_key else None
        try:
            cursor.execute("""
                INSERT INTO Usuarios (email, id_empleado, nombre_usuario, hashed_key, rol, estatus_acceso, llave_enc)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (email, id_empleado, nombre_usuario, hashed_key, rol, estatus, llave_enc))
        except Exception:
            cursor.execute("""
                INSERT INTO Usuarios (email, id_empleado, hashed_key, rol, estatus_acceso)
                VALUES (?, ?, ?, ?, ?)
            """, (email, id_empleado, hashed_key, rol, estatus))
        conn.commit()
    finally:
        conn.close()
# Gestión de estado para mensajes post-rerun
if 'success_msg' in st.session_state:
    st.success(st.session_state['success_msg'])
    del st.session_state['success_msg']
if 'new_token_msg' in st.session_state:
    st.success(st.session_state['new_token_msg'])
    st.code(st.session_state['new_token_code'])
    st.warning("⚠️ Copia esta llave ahora, no se podrá visualizar de nuevo.")
    if st.button("OK, Llave Copiada"):
        del st.session_state['new_token_msg']
        del st.session_state['new_token_code']
        st.rerun()
usuarios = get_all_usuarios(secret_key)
st.subheader("Usuarios en el Sistema")
if not usuarios:
    st.info("No hay usuarios en la base de datos.")
else:
    df_usuarios = pd.DataFrame(usuarios)
    
    # Buscador interactivo
    search_term = st.text_input("🔍 Buscar usuario (por correo, rol, ID...)", placeholder="Escribe para filtrar...")
    if search_term:
        df_usuarios = df_usuarios[df_usuarios.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
        
    st.dataframe(df_usuarios, hide_index=True, width='stretch')
st.divider()
tab_buscar, tab_crear, tab_editar = st.tabs(["🔎 Búsqueda y Activación Rápida", "➕ Añadir Usuario Manualmente", "✏️ Modificar Accesos (Avanzado)"])

with tab_crear:
    st.subheader("➕ Añadir Nuevo Usuario")
    with st.form("form_nuevo_usuario"):
        nuevo_email = st.text_input("Correo Electrónico *")
        nuevo_nombre = st.text_input("Nombre Completo (Opcional)")
        nuevo_id_empleado = st.text_input("ID Empleado (Opcional, dejar vacío si es BP/Admin)")
        nuevo_rol = st.selectbox("Rol", ["Líder", "Business Partner", "Administrador"])
        nuevo_estatus = st.selectbox("Estatus", ["Habilitado", "Deshabilitado"])
        
        submit_nuevo = st.form_submit_button("Crear Usuario")
        
        if submit_nuevo:
            if nuevo_email:
                try:
                    nuevo_token = generar_token()
                    hashed_token = hashlib.sha256(nuevo_token.encode()).hexdigest()
                    
                    # Limpiar ID si está vacío
                    emp_id_val = nuevo_id_empleado.strip() if nuevo_id_empleado.strip() != "" else None
                    nombre_val = nuevo_nombre.strip() if nuevo_nombre.strip() != "" else None
                    
                    crear_usuario(secret_key, nuevo_email.strip(), emp_id_val, nombre_val, nuevo_rol, nuevo_estatus, hashed_token, plain_key=nuevo_token)
                    
                    st.session_state['new_token_msg'] = f"Usuario {nuevo_email.strip()} creado correctamente. La llave única es:"
                    st.session_state['new_token_code'] = nuevo_token
                    st.rerun()
                except Exception as e:
                    if "UNIQUE constraint failed" in str(e):
                        st.error("Error: Este correo electrónico ya existe en el sistema.")
                    else:
                        st.error(f"Error al añadir usuario: {e}")
            else:
                st.warning("El correo electrónico es obligatorio.")

with tab_buscar:
    st.subheader("🔎 Búsqueda y Activación Rápida")
    st.markdown("Busca un líder en la nómina cargada y actívalo al instante.")
    busqueda_nomina = st.text_input("Buscar por nombre, ID o correo...")
    
    if busqueda_nomina:
        from db.database_manager import get_empleados
        todos_emp = get_empleados(secret_key)
        
        resultados = []
        for e in todos_emp:
            texto = f"{e.get('nombre_completo', '')} {e.get('id_empleado', '')} {e.get('correo_electronico', '')}".lower()
            if busqueda_nomina.lower() in texto:
                resultados.append(e)
                
        if resultados:
            for res in resultados[:5]:
                with st.container(border=True):
                    # Check if already in Usuarios
                    user_existente = next((u for u in usuarios if str(u.get('id_empleado', '')) == str(res['id_empleado'])), None)
                    
                    st.markdown(f"**{res.get('nombre_completo', 'Sin Nombre')}** | ID: {res['id_empleado']}")
                    
                    if user_existente:
                        st.info(f"✅ Usuario registrado con correo: {user_existente['email']} ({user_existente['estatus_acceso']})")
                        if user_existente['estatus_acceso'] == 'Deshabilitado':
                            if st.button("Habilitar Acceso", key=f"btn_hab_{res['id_empleado']}"):
                                nuevo_token = generar_token()
                                hashed_token = hashlib.sha256(nuevo_token.encode()).hexdigest()
                                actualizar_usuario(secret_key, user_existente['email'], 'Líder', 'Habilitado', hashed_token, plain_key=nuevo_token)
                                st.session_state['new_token_msg'] = f"Usuario {user_existente['email']} habilitado. La llave única es:"
                                st.session_state['new_token_code'] = nuevo_token
                                st.rerun()
                    else:
                        st.warning("⚠️ Este empleado no tiene cuenta de acceso creada.")
                        with st.form(key=f"form_crear_{res['id_empleado']}"):
                            nuevo_correo = st.text_input("Asignar Correo Electrónico para acceso:", value=res.get('correo_electronico') if res.get('correo_electronico') and str(res.get('correo_electronico')) != 'nan' else "")
                            btn_crear = st.form_submit_button("Crear Acceso")
                            
                            if btn_crear:
                                if nuevo_correo and str(nuevo_correo).strip():
                                    nuevo_token = generar_token()
                                    hashed_token = hashlib.sha256(nuevo_token.encode()).hexdigest()
                                    try:
                                        crear_usuario(secret_key, str(nuevo_correo).strip(), res['id_empleado'], res['nombre_completo'], "Líder", "Habilitado", hashed_token, plain_key=nuevo_token)
                                        st.session_state['new_token_msg'] = f"Acceso creado para {res['nombre_completo']}. La llave única es:"
                                        st.session_state['new_token_code'] = nuevo_token
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error al crear: {e}")
                                else:
                                    st.error("Debes ingresar un correo electrónico válido.")
        else:
            st.warning("No se encontró ningún empleado en la nómina con ese criterio.")

with tab_editar:
    st.subheader("✏️ Modificar Acceso Existente (Avanzado)")
    with st.container():
        if usuarios:
            opciones_email = [f"{u.get('nombre_usuario', 'Sin Nombre')} ({u['email']})" for u in usuarios]
            seleccion = st.selectbox("Seleccionar Usuario:", opciones_email)
            email_sel = seleccion.split("(")[-1].replace(")", "") if seleccion else None
            
            if email_sel:
                user_data = next((u for u in usuarios if u['email'] == email_sel), None)
                
                with st.form("form_acceso"):
                    st.text_input("Correo Electrónico (No editable)", value=user_data['email'], disabled=True)
                    mod_nombre = st.text_input("Nombre Completo", value=user_data.get('nombre_usuario', ''))
                    mod_id = st.text_input("ID Empleado", value=user_data.get('id_empleado', ''))
                    mod_rol = st.selectbox("Rol", ["Líder", "Business Partner", "Administrador"], index=["Líder", "Business Partner", "Administrador"].index(user_data['rol']))
                    mod_estatus = st.selectbox("Estatus", ["Habilitado", "Deshabilitado"], index=0 if user_data['estatus_acceso'] == 'Habilitado' else 1)
                    generar_nueva_llave = st.checkbox("Generar Nueva Llave Única (Reset)")
                    
                    submit_mod = st.form_submit_button("Guardar Cambios")
                    
                    if submit_mod:
                        mod_nombre_val = mod_nombre.strip() if mod_nombre.strip() != "" else None
                        mod_id_val = mod_id.strip() if mod_id.strip() != "" else None
                        
                        if generar_nueva_llave:
                            nuevo_token = generar_token()
                            hashed_token = hashlib.sha256(nuevo_token.encode()).hexdigest()
                            actualizar_usuario(secret_key, email_sel, mod_rol, mod_estatus, mod_nombre_val, mod_id_val, hashed_token, plain_key=nuevo_token)
                            
                            st.session_state['new_token_msg'] = f"Usuario {email_sel} actualizado. La nueva llave única es:"
                            st.session_state['new_token_code'] = nuevo_token
                            st.rerun()
                        else:
                            actualizar_usuario(secret_key, email_sel, mod_rol, mod_estatus, mod_nombre_val, mod_id_val)
                            st.success(f"Usuario {email_sel} actualizado correctamente.")
                            st.rerun()