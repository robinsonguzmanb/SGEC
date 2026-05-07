import sys

def patch_file():
    with open('SGEC/app.py', 'r') as f:
        content = f.read()

    search_block = """    else:
        rol = st.session_state['rol']
        st.sidebar.title("SGEC Menu")
        st.sidebar.success(f"Conectado como: {rol}")

        if st.sidebar.button("Cerrar Sesión de Usuario"):
            st.session_state['authenticated'] = False
            st.session_state['rol'] = None
            st.session_state['email_usuario'] = None
            st.session_state['impersonating'] = False
            st.session_state['impersonate_id'] = None
            st.rerun()

        if 'admin_tools_unlocked' not in st.session_state:
            st.session_state['admin_tools_unlocked'] = False

        if st.session_state['rol'] == 'Administrador':
            if st.sidebar.button("Bloquear Bóveda (Apagar Sistema)"):
                import os
                if os.path.exists('.master_key'):
                    os.remove('.master_key')
                st.session_state.clear()
                st.rerun()
        impersonating = st.session_state.get('impersonating', False)
        efective_rol = st.session_state.get('impersonate_rol') if impersonating else rol

        if impersonating:
            st.markdown(\"\"\"
                <div style="background-color: #ff4b4b; padding: 10px; border-radius: 5px; color: white; text-align: center; margin-bottom: 20px;">
                    <strong>🕵️ MODO SUPANTACIÓN ACTIVO:</strong> Estás viendo la interfaz como: {email} ({rol})
                </div>
            \"\"\".format(email=st.session_state.get('impersonate_email'), rol=efective_rol), unsafe_allow_html=True)

            with st.expander("🛠️ Herramientas de Admin (Solo visibles en modo Impersonate)"):
                colA, colB, colC = st.columns(3)
                with colA:
                    if st.button("Terminar Suplantación", key="end_impersonate"):
                        st.session_state['impersonating'] = False
                        st.session_state['impersonate_email'] = None
                        st.session_state['impersonate_rol'] = None
                        st.rerun()
                with colB:
                    if st.button("Forzar Sincronización (Commit)"):
                        st.success("Sincronización silenciosa forzada. (Base de datos WAL asegurada).")
                with colC:
                    if st.button("Ver Tablas Core SQL (Debug)"):
                        from db.database_manager import execute_query
                        reservas_debug = execute_query("SELECT id_reserva, id_ceco, monto, estatus FROM Reservas ORDER BY id_reserva DESC LIMIT 5")
                        st.write("Últimas Reservas en DB:")
                        st.dataframe(reservas_debug)

        st.sidebar.markdown("---")
        st.sidebar.subheader("Módulos")

        def safe_page_link(filename, label, icon):
            path = f"pages/{filename}"
            try:
                st.sidebar.page_link(path, label=label, icon=icon)
            except Exception:
                if st.sidebar.button(f"{icon} {label}", width='stretch', key=f"nav_btn_{filename}"):
                    st.switch_page(path)
        if efective_rol == 'Administrador':
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔒 Zona de Administrador")
            if not st.session_state.get('admin_tools_unlocked'):
                admin_key = st.sidebar.text_input("Ingresa Master Key", type="password", key="admin_key_input")
                if st.sidebar.button("Desbloquear Opciones de Admin", type="primary"):
                    if admin_key == st.session_state['secret_key']:
                        st.session_state['admin_tools_unlocked'] = True
                        st.sidebar.success("Desbloqueado.")
                        st.rerun()
                    else:
                        st.sidebar.error("Clave Incorrecta")
            else:
                safe_page_link("admin_ingestion.py", label="Módulo de Ingesta", icon="📥")
                safe_page_link("admin_access.py", label="Gestión de Accesos", icon="🔐")
                safe_page_link("admin_gym.py", label="Admin Gym (LLM)", icon="⚙️")
                safe_page_link("admin_impersonate.py", label="Modo Suplantación", icon="🎭")

        if efective_rol in ['Administrador', 'Business Partner']:
            safe_page_link("bp_dashboard.py", label="BP Dashboard", icon="⚖️")
            safe_page_link("executive_dashboard.py", label="Dashboard Ejecutivo", icon="📈")
            safe_page_link("reporteria.py", label="Reportería", icon="📊")

        if efective_rol in ['Administrador', 'Líder']:
            safe_page_link("simulation_chat.py", label="Chat de Simulación", icon="🤖")"""

    replace_block = """    else:
        render_sidebar()
        rol = st.session_state['rol']
        impersonating = st.session_state.get('impersonating', False)
        efective_rol = st.session_state.get('impersonate_rol') if impersonating else rol

        if impersonating:
            st.markdown(\"\"\"
                <div style="background-color: #ff4b4b; padding: 10px; border-radius: 5px; color: white; text-align: center; margin-bottom: 20px;">
                    <strong>🕵️ MODO SUPANTACIÓN ACTIVO:</strong> Estás viendo la interfaz como: {email} ({rol})
                </div>
            \"\"\".format(email=st.session_state.get('impersonate_email'), rol=efective_rol), unsafe_allow_html=True)

            with st.expander("🛠️ Herramientas de Admin (Solo visibles en modo Impersonate)"):
                colA, colB, colC = st.columns(3)
                with colA:
                    if st.button("Terminar Suplantación", key="end_impersonate"):
                        st.session_state['impersonating'] = False
                        st.session_state['impersonate_email'] = None
                        st.session_state['impersonate_rol'] = None
                        st.rerun()
                with colB:
                    if st.button("Forzar Sincronización (Commit)"):
                        st.success("Sincronización silenciosa forzada. (Base de datos WAL asegurada).")
                with colC:
                    if st.button("Ver Tablas Core SQL (Debug)"):
                        from db.database_manager import execute_query
                        reservas_debug = execute_query("SELECT id_reserva, id_ceco, monto, estatus FROM Reservas ORDER BY id_reserva DESC LIMIT 5")
                        st.write("Últimas Reservas en DB:")
                        st.dataframe(reservas_debug)"""

    content = content.replace(search_block, replace_block)

    with open('SGEC/app.py', 'w') as f:
        f.write(content)

patch_file()
