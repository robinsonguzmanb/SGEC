import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from db.database_manager import execute_query
from utils.navigation import render_sidebar

render_sidebar()

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Debes iniciar sesión primero para acceder a esta página.")
    st.stop()
st.title("📊 Reportería y Visibilidad de CECOs")
st.markdown("Consolidado del estado financiero por Centro de Costos, incluyendo presupuesto 'en el aire' (reservado).")
secret_key = st.session_state['secret_key']
from db.database_manager import get_todos_los_cecos, get_reservas_y_cartas
cecos = get_todos_los_cecos(secret_key)
if not cecos:
    st.info("No hay datos de CECOs para mostrar.")
    st.stop()
df = pd.DataFrame(cecos)
df['saldo_disponible'] = df['presupuesto_anual'] - df['presupuesto_consumido'] - df['presupuesto_reservado']
total_anual = df['presupuesto_anual'].sum()
total_consumido = df['presupuesto_consumido'].sum()
total_reservado = df['presupuesto_reservado'].sum()
total_disponible = df['saldo_disponible'].sum()
st.subheader("Resumen Global Financiero")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Presupuesto Total Anual", f"${total_anual:,.2f}")
col2.metric("Total Gastado (Nómina)", f"${total_consumido:,.2f}")
col3.metric("Total en Reserva (Validación)", f"${total_reservado:,.2f}")
col4.metric("Total Disponible Real", f"${total_disponible:,.2f}")
st.divider()
st.subheader("Detalle por Centro de Costos")
df_mostrar = df.copy()
for col in ['presupuesto_anual', 'presupuesto_consumido', 'presupuesto_reservado', 'saldo_disponible']:
    df_mostrar[col] = df_mostrar[col].apply(lambda x: f"${x:,.2f}")
st.dataframe(df_mostrar, width='stretch', hide_index=True)
st.divider()
st.subheader("Estado de Reservas Activas e Históricas")
reservas = get_reservas_y_cartas(secret_key)
if reservas:
    df_res = pd.DataFrame(reservas)
    df_res['monto'] = df_res['monto'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
    st.dataframe(df_res, width='stretch', hide_index=True)
else:
    st.info("No hay reservas registradas en el sistema.")