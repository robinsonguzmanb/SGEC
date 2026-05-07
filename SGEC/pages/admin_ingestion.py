import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from db.database_manager import save_dataframe_to_table
from datetime import datetime
from utils.navigation import render_sidebar

render_sidebar()

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Debes iniciar sesión primero para acceder a esta página.")
    st.stop()
rol = st.session_state.get('rol')
if rol != "Administrador":
    st.error("No tienes permisos para acceder a esta página. Solo Administradores.")
    st.stop()
st.title("Administración - Ingesta de Datos (CORE-ADMIN)")
st.markdown("""
Esta herramienta te permite cargar archivos de nómina o presupuesto (Excel/CSV).
Asegúrate de mapear las columnas correctamente. Si hay datos faltantes en campos críticos, el archivo completo será rechazado.
""")
tab_empleados, tab_cecos = st.tabs(["Ingesta de Empleados", "Ingesta de CECOs"])
def validate_empleados(df, mapped_cols, is_comp=False):
    required_fields = ['id_empleado'] if is_comp else ['id_empleado', 'nombre_completo', 'id_ceco']
    errors = []
    
    for field in required_fields:
        if field not in mapped_cols or not mapped_cols[field]:
            errors.append(f"Falta mapear el campo requerido: {field}")
            return errors
            
    for index, row in df.iterrows():
        row_num = index + 2 
        for field in required_fields:
            col_name = mapped_cols[field]
            val = row.get(col_name)
            if pd.isna(val) or str(val).strip() == "":
                errors.append(f"Fila {row_num}: Falta valor para el campo crítico '{field}' (columna '{col_name}').")
                
    return errors
def validate_cecos(df, mapped_cols):
    required_fields = ['id_ceco', 'presupuesto_anual']
    errors = []
    
    for field in required_fields:
        if field not in mapped_cols or not mapped_cols[field]:
            errors.append(f"Falta mapear el campo requerido: {field}")
            return errors
            
    for index, row in df.iterrows():
        row_num = index + 2
        for field in required_fields:
            col_name = mapped_cols[field]
            val = row.get(col_name)
            if pd.isna(val) or str(val).strip() == "":
                errors.append(f"Fila {row_num}: Falta valor para el campo crítico '{field}' (columna '{col_name}').")
                
    return errors
with tab_empleados:
    st.subheader("Carga de Base de Datos de Empleados")
    
    from db.database_manager import get_connection
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM Empleados")
        total_emp = cursor.fetchone()[0]
        if total_emp > 0:
            st.info(f"📊 Estado Actual: Hay **{total_emp}** empleados en la base de datos.")
        else:
            st.warning("⚠️ La base de datos de Empleados está vacía.")
    except Exception:
        pass
    finally:
        conn.close()

    tab_main, tab_comp = st.tabs(["📄 Nómina Principal", "➕ Datos Complementarios (Actualización)"])
    
    with tab_main:
        uploaded_main = st.file_uploader("Sube la Nómina Principal (CSV, XLSX)", type=['csv', 'xlsx'], key="upload_emp_main")
    with tab_comp:
        uploaded_comp = st.file_uploader("Sube archivo con Datos Complementarios", type=['csv', 'xlsx'], key="upload_emp_comp")
        
    uploaded_file_emp = uploaded_main or uploaded_comp
    is_comp = uploaded_comp is not None

    if uploaded_file_emp:
        try:
            st.markdown("### Configuración de Lectura")
            col_cfg1, col_cfg2 = st.columns(2)
            
            if uploaded_file_emp.name.endswith('.csv'):
                with col_cfg1:
                    header_row_emp = st.number_input("Fila de Encabezados (1 = primera fila)", min_value=1, value=1, step=1, key="header_emp_csv")
                uploaded_file_emp.seek(0)
                df_emp = pd.read_csv(uploaded_file_emp, header=header_row_emp-1)
            else:
                uploaded_file_emp.seek(0)
                xls_emp = pd.ExcelFile(uploaded_file_emp)
                with col_cfg1:
                    hoja_sel_emp = st.selectbox("Selecciona la Hoja", xls_emp.sheet_names, key="sheet_emp")
                with col_cfg2:
                    header_row_emp = st.number_input("Fila de Encabezados (1 = primera fila)", min_value=1, value=1, step=1, key="header_emp_xls")
                
                uploaded_file_emp.seek(0)
                df_emp = pd.read_excel(uploaded_file_emp, sheet_name=hoja_sel_emp, header=header_row_emp-1)
            
            st.write("Vista previa de los datos:")
            st.dataframe(df_emp.head(5).astype(str))
            
            st.markdown("### Mapeo de Columnas")
            cols_excel = ["-- Seleccionar --"] + list(df_emp.columns)
            
            campos_sistema_emp = {
                'id_empleado': 'ID Empleado (PK)*',
                'nombre_completo': 'Nombre Completo' + ('' if is_comp else '*'),
                'correo_electronico': 'Correo Electrónico',
                'grado_actual': 'Grado Actual',
                'sueldo_base': 'Sueldo Base',
                'renta_anual': 'Renta Anualizada',
                'id_jefe_directo': 'ID Jefe Directo',
                'id_ceco': 'ID Centro de Costos (CECO)' + ('' if is_comp else '*'),
                'fecha_ingreso': 'Fecha de Ingreso',
                'fecha_ultimo_ajuste': 'Fecha de Último Ajuste',
                'estatus': 'Estatus'
            }
            
            mapped_cols_emp = {}
            col1, col2 = st.columns(2)
            
            for i, (sys_field, label) in enumerate(campos_sistema_emp.items()):
                with col1 if i % 2 == 0 else col2:
                    default_idx = 0
                    for j, c in enumerate(cols_excel):
                        if c.lower() in label.lower() or sys_field.lower() in c.lower():
                            default_idx = j
                            break
                    mapped_cols_emp[sys_field] = st.selectbox(label, options=cols_excel, index=default_idx, key=f"emp_{sys_field}")
            
            if st.button("Validar e Importar Empleados", type="primary"):
                final_mapping = {k: v for k, v in mapped_cols_emp.items() if v != "-- Seleccionar --"}
                
                # Auto-limpieza de filas basura al final del archivo (footers o filas en blanco)
                if 'id_empleado' in final_mapping:
                    excel_pk_col = final_mapping['id_empleado']
                    # Ignorar filas donde el PK esté vacío para cuadrar con la última fila real de datos
                    df_emp = df_emp.dropna(subset=[excel_pk_col])
                    df_emp = df_emp[df_emp[excel_pk_col].astype(str).str.strip() != '']
                    df_emp = df_emp[df_emp[excel_pk_col].astype(str).str.lower() != 'nan']
                    df_emp = df_emp.reset_index(drop=True)
                
                with st.spinner("Validando integridad..."):
                    errors = validate_empleados(df_emp, final_mapping, is_comp)
                
                if errors:
                    st.error("❌ Se encontraron errores de validación. El archivo fue rechazado.")
                    with st.expander("Ver detalle de errores"):
                        for e in errors:
                            st.write(e)
                    st.info("Por favor, corrige el archivo original y vuelve a subirlo.")
                else:
                    df_final = pd.DataFrame()
                    for sys_col, excel_col in final_mapping.items():
                        df_final[sys_col] = df_emp[excel_col]
                    
                    # Cálculo de la red (Materialized Path)
                    if 'id_empleado' in df_final.columns and 'id_jefe_directo' in df_final.columns:
                        df_final['id_jefe_directo'] = df_final['id_jefe_directo'].fillna('')
                        
                        jefes_dict = pd.Series(df_final['id_jefe_directo'].values, index=df_final['id_empleado'].values).to_dict()
                        
                        def calcular_ruta(emp_id, visitados=None):
                            if visitados is None:
                                visitados = set()
                            if emp_id in visitados or not emp_id or pd.isna(emp_id):
                                return ""
                            visitados.add(emp_id)
                            jefe = str(jefes_dict.get(emp_id, "")).strip()
                            if not jefe or pd.isna(jefe) or jefe.lower() == 'nan':
                                return f"|{emp_id}|"
                            
                            ruta_jefe = calcular_ruta(jefe, visitados)
                            if ruta_jefe:
                                return f"{ruta_jefe}{emp_id}|"
                            return f"|{emp_id}|"
                            
                        df_final['ruta_jerarquica'] = df_final['id_empleado'].apply(lambda x: calcular_ruta(x))
                    
                    try:
                        save_dataframe_to_table(st.session_state['secret_key'], df_final, 'Empleados')
                        
                        if 'correo_electronico' in df_final.columns and 'id_empleado' in df_final.columns:
                            from db.database_manager import get_connection
                            conn = get_connection()
                            cursor = conn.cursor()
                            for _, row in df_final.iterrows():
                                if pd.notnull(row['correo_electronico']) and str(row['correo_electronico']).strip() != "":
                                    email = str(row['correo_electronico']).strip()
                                    id_emp = row['id_empleado']
                                    nombre = str(row['nombre_completo']).strip()
                                    cursor.execute("""
                                        INSERT INTO Usuarios (email, id_empleado, nombre_usuario, rol, estatus_acceso)
                                        VALUES (?, ?, ?, 'Líder', 'Deshabilitado')
                                        ON CONFLICT(email) DO UPDATE SET 
                                        id_empleado=excluded.id_empleado, 
                                        nombre_usuario=excluded.nombre_usuario
                                    """, (email, id_emp, nombre))
                            conn.commit()
                            conn.close()
                            
                        # Recalcular presupuestos de CECOs basándose en empleados ingresados
                        try:
                            from db.database_manager import recalcular_presupuestos_consumidos
                            recalcular_presupuestos_consumidos(st.session_state['secret_key'])
                        except Exception as calc_e:
                            st.warning(f"La importación fue exitosa, pero hubo un detalle al recalcular presupuestos: {calc_e}")
                            
                        st.success(f"✅ ¡Importación exitosa! {len(df_final)} registros guardados en la tabla Empleados. Usuarios pre-cargados y presupuestos recalculados.")
                    except Exception as e:
                        st.error(f"Error al guardar en la base de datos: {e}")
                        
        except Exception as e:
            st.error(f"No se pudo procesar el archivo: {e}")
with tab_cecos:
    st.subheader("Carga de Catálogo de CECOs y Presupuestos")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM CECOs")
        total_cecos = cursor.fetchone()[0]
        if total_cecos > 0:
            st.info(f"📊 Estado Actual: Hay **{total_cecos}** Centros de Costo en la base de datos.")
        else:
            st.warning("⚠️ La base de datos de CECOs está vacía.")
    except Exception:
        pass
    finally:
        conn.close()

    uploaded_file_ceco = st.file_uploader("Sube el archivo de CECOs (CSV, XLSX)", type=['csv', 'xlsx'], key="upload_ceco")
    if uploaded_file_ceco:
        try:
            st.markdown("### Configuración de Lectura")
            col_cfg1, col_cfg2 = st.columns(2)
            
            if uploaded_file_ceco.name.endswith('.csv'):
                with col_cfg1:
                    header_row_ceco = st.number_input("Fila de Encabezados (1 = primera fila)", min_value=1, value=1, step=1, key="header_ceco_csv")
                uploaded_file_ceco.seek(0)
                df_ceco = pd.read_csv(uploaded_file_ceco, header=header_row_ceco-1)
            else:
                uploaded_file_ceco.seek(0)
                xls_ceco = pd.ExcelFile(uploaded_file_ceco)
                with col_cfg1:
                    hoja_sel_ceco = st.selectbox("Selecciona la Hoja", xls_ceco.sheet_names, key="sheet_ceco")
                with col_cfg2:
                    header_row_ceco = st.number_input("Fila de Encabezados (1 = primera fila)", min_value=1, value=1, step=1, key="header_ceco_xls")
                
                uploaded_file_ceco.seek(0)
                df_ceco = pd.read_excel(uploaded_file_ceco, sheet_name=hoja_sel_ceco, header=header_row_ceco-1)
            
            st.write("Vista previa de los datos:")
            st.dataframe(df_ceco.head(5).astype(str))
            
            st.markdown("### Mapeo de Columnas")
            cols_excel = ["-- Seleccionar --"] + list(df_ceco.columns)
            
            campos_sistema_ceco = {
                'id_ceco': 'ID CECO*',
                'nombre': 'Nombre del Centro de Costo',
                'presupuesto_anual': 'Presupuesto Anual Asignado*',
                'presupuesto_consumido': 'Presupuesto Consumido',
                'presupuesto_reservado': 'Presupuesto Reservado'
            }
            
            mapped_cols_ceco = {}
            for sys_field, label in campos_sistema_ceco.items():
                default_idx = 0
                for j, c in enumerate(cols_excel):
                    if sys_field.split('_')[0].lower() in c.lower():
                        default_idx = j
                        break
                mapped_cols_ceco[sys_field] = st.selectbox(label, options=cols_excel, index=default_idx, key=f"ceco_{sys_field}")
                
            if st.button("Validar e Importar CECOs", type="primary"):
                final_mapping = {k: v for k, v in mapped_cols_ceco.items() if v != "-- Seleccionar --"}
                
                # Auto-limpieza de filas basura al final del archivo (footers o filas en blanco)
                if 'id_ceco' in final_mapping:
                    excel_pk_col = final_mapping['id_ceco']
                    # Ignorar filas donde el PK esté vacío para cuadrar con la última fila real de datos
                    df_ceco = df_ceco.dropna(subset=[excel_pk_col])
                    df_ceco = df_ceco[df_ceco[excel_pk_col].astype(str).str.strip() != '']
                    df_ceco = df_ceco[df_ceco[excel_pk_col].astype(str).str.lower() != 'nan']
                    df_ceco = df_ceco.reset_index(drop=True)
                
                with st.spinner("Validando integridad..."):
                    errors = validate_cecos(df_ceco, final_mapping)
                
                if errors:
                    st.error("❌ Se encontraron errores de validación. El archivo fue rechazado.")
                    with st.expander("Ver detalle de errores"):
                        for e in errors:
                            st.write(e)
                    st.info("Por favor, corrige el archivo original y vuelve a subirlo.")
                else:
                    df_final = pd.DataFrame()
                    for sys_col, excel_col in final_mapping.items():
                        df_final[sys_col] = df_ceco[excel_col]
                    
                    if 'nombre' not in df_final.columns:
                        df_final['nombre'] = df_final['id_ceco'].apply(lambda x: f"CECO {x}")
                    else:
                        df_final['nombre'] = df_final.apply(lambda row: f"CECO {row['id_ceco']}" if pd.isna(row['nombre']) or str(row['nombre']).strip()=="" else row['nombre'], axis=1)
                        
                    if 'presupuesto_consumido' not in df_final.columns:
                        df_final['presupuesto_consumido'] = 0.0
                    if 'presupuesto_reservado' not in df_final.columns:
                        df_final['presupuesto_reservado'] = 0.0
                    try:
                        save_dataframe_to_table(st.session_state['secret_key'], df_final, 'CECOs')
                        
                        # Recalcular presupuestos de CECOs inmediatamente por si ya habían empleados cargados
                        try:
                            from db.database_manager import recalcular_presupuestos_consumidos
                            recalcular_presupuestos_consumidos(st.session_state['secret_key'])
                        except:
                            pass
                            
                        st.success(f"✅ ¡Importación exitosa! {len(df_final)} registros guardados en la tabla CECOs.")
                    except Exception as e:
                        st.error(f"Error al guardar en la base de datos: {e}")
        except Exception as e:
            st.error(f"No se pudo procesar el archivo: {e}")
