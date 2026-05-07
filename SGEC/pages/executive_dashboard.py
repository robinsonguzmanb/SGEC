import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from db.database_manager import execute_query
import io
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Debes iniciar sesión primero para acceder a esta página.")
    st.stop()
rol = st.session_state.get('rol')
if rol == "Líder":
    st.warning("No tienes permisos para ver el Dashboard Ejecutivo. Acceso denegado.")
    st.stop()
st.title("📈 Dashboard Ejecutivo")
st.markdown("Visibilidad macro y exportación de datos para Comités Gerenciales.")
secret_key = st.session_state['secret_key']
from db.database_manager import get_todas_las_reservas, get_todos_los_cecos, get_todos_empleados
reservas = get_todas_las_reservas(secret_key)
df_reservas = pd.DataFrame(reservas) if reservas else pd.DataFrame(columns=['id_reserva', 'monto', 'estatus', 'justificacion_ia', 'comentario_bp'])
cecos = get_todos_los_cecos(secret_key)
df_cecos = pd.DataFrame(cecos) if cecos else pd.DataFrame(columns=['id_ceco', 'presupuesto_anual', 'presupuesto_consumido', 'presupuesto_reservado'])
if not df_cecos.empty:
    df_cecos['saldo_disponible'] = df_cecos['presupuesto_anual'] - df_cecos['presupuesto_consumido'] - df_cecos['presupuesto_reservado']
    df_cecos['porcentaje_disponible'] = (df_cecos['saldo_disponible'] / df_cecos['presupuesto_anual']) * 100
empleados = get_todos_empleados(secret_key)
df_empleados = pd.DataFrame(empleados) if empleados else pd.DataFrame()
st.subheader("Indicadores Macro")
monto_total_reservado = df_reservas[df_reservas['estatus'].isin(['EN_VALIDACION', 'APROBADO', 'AJUSTE_REQUERIDO'])]['monto'].sum() if not df_reservas.empty else 0
total_presupuesto = df_cecos['presupuesto_anual'].sum() if not df_cecos.empty else 0
total_gastado = df_cecos['presupuesto_consumido'].sum() if not df_cecos.empty else 0
col1, col2, col3 = st.columns(3)
col1.metric("Presupuesto Anual Total", f"${total_presupuesto:,.2f}")
col2.metric("Total Gastado (Real)", f"${total_gastado:,.2f}")
col3.metric("Monto Total Reservado (Piloto)", f"${monto_total_reservado:,.2f}")
st.divider()
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Eficiencia de CECOs")
    if not df_cecos.empty:
        df_chart = df_cecos[['id_ceco', 'presupuesto_anual', 'presupuesto_consumido', 'presupuesto_reservado']].copy()
        df_chart['Gasto + Reserva'] = df_chart['presupuesto_consumido'] + df_chart['presupuesto_reservado']
        st.bar_chart(df_chart.set_index('id_ceco')[['presupuesto_anual', 'Gasto + Reserva']])
    else:
        st.info("Sin datos.")
with col_b:
    st.subheader("Embudo de Solicitudes")
    if not df_reservas.empty:
        conteo_estados = df_reservas['estatus'].value_counts()
        st.bar_chart(conteo_estados)
    else:
        st.info("Sin datos.")
st.divider()
st.subheader("🚨 Índice de Alerta (CECOs < 10% Disponible)")
if not df_cecos.empty:
    cecos_alerta = df_cecos[df_cecos['porcentaje_disponible'] < 10.0]
    if not cecos_alerta.empty:
        st.dataframe(cecos_alerta[['id_ceco', 'nombre', 'presupuesto_anual', 'saldo_disponible', 'porcentaje_disponible']].style.format({'porcentaje_disponible': "{:.2f}%"}))
    else:
        st.success("Todos los CECOs tienen un saldo saludable (> 10%).")
st.divider()
st.subheader("Exportación de Datos para Comité")
st.markdown("Descarga el reporte consolidado en formato Excel con todas las hojas necesarias.")
def generate_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if not df_empleados.empty:
            df_empleados.to_excel(writer, sheet_name='Nómina Actual', index=False)
        else:
            pd.DataFrame(['Sin datos']).to_excel(writer, sheet_name='Nómina Actual')
            
        if not df_cecos.empty:
            df_cecos.to_excel(writer, sheet_name='Estado CECOs', index=False)
            
        if not df_reservas.empty:
            df_reservas.to_excel(writer, sheet_name='Embudo y Reservas', index=False)
            
            log_cols = ['id_reserva', 'id_ceco', 'monto', 'estatus', 'fecha_reserva', 'justificacion_ia', 'comentario_bp']
            df_log = df_reservas[[c for c in log_cols if c in df_reservas.columns]]
            df_log.to_excel(writer, sheet_name='Log de Validaciones', index=False)
            
    return output.getvalue()
excel_data = generate_excel()
st.download_button(
    label="📥 Descargar Reporte Consolidado (Excel)",
    data=excel_data,
    file_name=f"Reporte_Ejecutivo_SGEC_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary"
)
