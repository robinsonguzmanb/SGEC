import sys

def patch_file():
    with open('SGEC/app.py', 'r') as f:
        content = f.read()

    search_block = """st.set_page_config(
    page_title="SGEC - Local Intelligence",
    page_icon="🛡️",
    layout="wide"
)"""

    replace_block = """from utils.navigation import render_sidebar

st.set_page_config(
    page_title="SGEC - Local Intelligence",
    page_icon="🛡️",
    layout="wide"
)"""

    content = content.replace(search_block, replace_block)

    search_block2 = """def render_vault_unlock():
    import os
    if not os.path.exists('.master_key'):
        st.title("🛡️ Inicialización de Bóveda (Primer Arranque)")
        st.markdown("Bienvenido al SGEC. Para inicializar el sistema de forma segura, define la **Master Secret Key**.")
        st.warning("⚠️ Conserva esta clave en un lugar seguro. Si se pierde, la base de datos será inaccesible.")

        with st.form("init_vault_form"):
            secret_key = st.text_input("Ingresa la Master Secret Key", type="password")
            confirm_key = st.text_input("Confirma la Master Secret Key", type="password")
            submit_button = st.form_submit_button("Inicializar Core")"""

    replace_block2 = """def render_vault_unlock():
    import os
    if not os.path.exists('.master_key'):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🛡️ Inicialización de Bóveda")
            st.markdown("Bienvenido a **SGEC - Local Intelligence**.")
            st.info("Para inicializar el sistema de forma segura, define la **Master Secret Key**.")
            st.warning("⚠️ Conserva esta clave en un lugar seguro. Si se pierde, la base de datos será inaccesible.")

            with st.form("init_vault_form"):
                secret_key = st.text_input("Ingresa la Master Secret Key", type="password")
                confirm_key = st.text_input("Confirma la Master Secret Key", type="password")
                submit_button = st.form_submit_button("Inicializar Core", use_container_width=True)"""

    content = content.replace(search_block2, replace_block2)

    search_block3 = """def render_login():
    import hashlib
    from db.database_manager import get_usuario, actualizar_ultimo_acceso

    st.title("🔑 Iniciar Sesión - SGEC")
    st.markdown("Por favor, ingresa tu correo electrónico y tu Llave Única proporcionada por el Administrador.")

    with st.form("login_form"):
        email = st.text_input("Correo Electrónico")
        unique_key = st.text_input("Llave Única", type="password")
        submit_button = st.form_submit_button("Ingresar")"""

    replace_block3 = """def render_login():
    import hashlib
    from db.database_manager import get_usuario, actualizar_ultimo_acceso

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏢 Bienvenido a SGEC")
        st.markdown("<h4 style='text-align: center; color: #555;'>Local Intelligence</h4>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("Por favor, ingresa tus credenciales corporativas.")

        with st.form("login_form"):
            email = st.text_input("Correo Electrónico Corporativo")
            unique_key = st.text_input("Llave Única", type="password")
            submit_button = st.form_submit_button("Ingresar", use_container_width=True)"""

    content = content.replace(search_block3, replace_block3)

    with open('SGEC/app.py', 'w') as f:
        f.write(content)

patch_file()
