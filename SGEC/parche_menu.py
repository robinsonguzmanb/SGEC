import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

menu_code = """
        # STREAMLIT MULTIPAGE SETUP WORKAROUND (for standalone executables)
        # Forzamos la creacion manual del menu lateral basado en roles
        st.sidebar.markdown("---")
        st.sidebar.subheader("Módulos de Sistema")
        
        if efective_rol == 'Administrador':
            st.sidebar.page_link("pages/admin_ingestion.py", label="Módulo de Ingesta", icon="📥")
            st.sidebar.page_link("pages/admin_access.py", label="Gestión de Accesos", icon="🔐")
            st.sidebar.page_link("pages/admin_gym.py", label="Admin Gym (LLM)", icon="⚙️")
            st.sidebar.page_link("pages/admin_impersonate.py", label="Modo Suplantación", icon="🎭")
            
        if efective_rol in ['Administrador', 'Business Partner']:
            st.sidebar.page_link("pages/bp_dashboard.py", label="BP Dashboard", icon="⚖️")
            st.sidebar.page_link("pages/executive_dashboard.py", label="Dashboard Ejecutivo", icon="📈")
            st.sidebar.page_link("pages/reporteria.py", label="Reportería General", icon="📊")
            
        if efective_rol in ['Administrador', 'Líder']:
            st.sidebar.page_link("pages/simulation_chat.py", label="Chat de Simulación", icon="🤖")

        # Si el usuario es Líder O el Admin está suplantando a un Líder, mostramos la guía
"""

if "st.sidebar.page_link" not in content:
    content = content.replace(
        "# Si el usuario es Líder O el Admin está suplantando a un Líder, mostramos la guía",
        menu_code
    )
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("¡Menú inyectado exitosamente en app.py!")
else:
    print("El menú ya estaba inyectado.")