import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from db.database_manager import execute_query, aprobar_reserva, rechazar_reserva, solicitar_ajuste_reserva
from utils.navigation import render_sidebar

render_sidebar()

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning("Debes iniciar sesión primero para acceder a esta página.")
    st.stop()
rol = st.session_state.get('rol')
if rol not in ["Business Partner", "Administrador"]:
    st.error("No tienes permisos para acceder a esta página.")
    st.stop()
st.title("⚖️ Dashboard Business Partner (BP)")
st.markdown("Bandeja de Entrada Inteligente: Gestiona las aprobaciones pendientes derivadas por la IA.")
secret_key = st.session_state['secret_key']
from db.database_manager import get_reservas_pendientes
pendientes = get_reservas_pendientes(secret_key)
if not pendientes:
    st.success("🎉 No hay casos pendientes de aprobación.")
    st.stop()
st.subheader("Casos Pendientes de Revisión")
for caso in pendientes:
    with st.expander(f"Caso #{caso['id_reserva']} - {caso['descripcion']} - {caso['fecha_reserva']}", expanded=False):
        st.write(f"**CECO Afectado:** {caso['id_ceco']}")
        st.write(f"**Monto Reservado:** ${caso['monto']:,.2f}")
        
        st.markdown("#### 🤖 Contexto y Justificación de la IA")
        if caso['justificacion_ia']:
            st.info(caso['justificacion_ia'])
        else:
            st.warning("No se registró justificación de la IA para este caso.")
            
        comentario_bp = st.text_input(f"Comentario del Experto (Opcional)", key=f"comentario_{caso['id_reserva']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Aprobar Cambio", key=f"btn_aprobar_{caso['id_reserva']}", type="primary"):
                aprobar_reserva(secret_key, caso['id_reserva'], comentario_bp=comentario_bp)
                st.success("Caso aprobado exitosamente.")
                st.rerun()
                
        with col2:
            if st.button("❌ Rechazar (Liberar Saldo)", key=f"btn_rechazar_{caso['id_reserva']}"):
                rechazar_reserva(secret_key, caso['id_reserva'], caso['id_ceco'], caso['monto'], comentario_bp)
                st.success("Caso rechazado. Saldo liberado al CECO.")
                st.rerun()
                
        with col3:
            if st.button("⚠️ Solicitar Ajuste", key=f"btn_ajuste_{caso['id_reserva']}"):
                solicitar_ajuste_reserva(secret_key, caso['id_reserva'], comentario_bp)
                st.success("Ajuste solicitado. El líder debe modificar la propuesta.")
                st.rerun()