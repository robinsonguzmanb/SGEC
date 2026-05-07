import streamlit as st

def render_sidebar():
    if not st.session_state.get('authenticated', False):
        return

    rol = st.session_state.get('rol')
    st.sidebar.title("🏢 SGEC Menú")
    st.sidebar.markdown(f"**Usuario:** {st.session_state.get('email_usuario')}")
    st.sidebar.caption(f"**Rol:** {rol}")
    st.sidebar.markdown("---")

    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state['authenticated'] = False
        st.session_state['rol'] = None
        st.session_state['email_usuario'] = None
        st.session_state['impersonating'] = False
        st.session_state['impersonate_id'] = None
        st.rerun()

    if st.session_state.get('rol') == 'Administrador':
        if st.sidebar.button("Bloquear Bóveda", use_container_width=True):
            import os
            if os.path.exists('.master_key'):
                os.remove('.master_key')
            st.session_state.clear()
            st.rerun()

    impersonating = st.session_state.get('impersonating', False)
    efective_rol = st.session_state.get('impersonate_rol') if impersonating else rol

    st.sidebar.markdown("---")
    st.sidebar.subheader("Módulos")

    def safe_page_link(filename, label, icon):
        path = f"pages/{filename}"
        try:
            st.sidebar.page_link(path, label=label, icon=icon)
        except Exception:
            if st.sidebar.button(f"{icon} {label}", use_container_width=True, key=f"nav_btn_{filename}"):
                st.switch_page(path)

    # Home Link
    try:
        st.sidebar.page_link("app.py", label="Inicio", icon="🏠")
    except Exception:
        if st.sidebar.button("🏠 Inicio", use_container_width=True, key="nav_btn_home"):
            st.switch_page("app.py")

    if efective_rol == 'Administrador':
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔒 Admin")
        if not st.session_state.get('admin_tools_unlocked', False):
            admin_key = st.sidebar.text_input("Ingresa Master Key", type="password", key="admin_key_input")
            if st.sidebar.button("Desbloquear Admin", type="primary", use_container_width=True):
                if admin_key == st.session_state.get('secret_key'):
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
        safe_page_link("simulation_chat.py", label="Chat de Simulación", icon="🤖")
