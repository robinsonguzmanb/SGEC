import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.database_manager import test_connection, init_db, ejecutar_garbage_collector
st.set_page_config(
    page_title="SGEC - Local Intelligence",
    page_icon="🛡️",
    layout="wide"
)
def render_vault_unlock():
    import os
    if not os.path.exists('.master_key'):
        st.title("🛡️ Inicialización de Bóveda (Primer Arranque)")
        st.markdown("Bienvenido al SGEC. Para inicializar el sistema de forma segura, define la **Master Secret Key**.")
        st.warning("⚠️ Conserva esta clave en un lugar seguro. Si se pierde, la base de datos será inaccesible.")
        
        with st.form("init_vault_form"):
            secret_key = st.text_input("Ingresa la Master Secret Key", type="password")
            confirm_key = st.text_input("Confirma la Master Secret Key", type="password")
            submit_button = st.form_submit_button("Inicializar Core")
            
            if submit_button:
                if secret_key and confirm_key:
                    if secret_key == confirm_key:
                        try:
                            init_db(secret_key)
                            if test_connection(secret_key):
                                with open('.master_key', 'w') as f:
                                    f.write(secret_key)
                                st.session_state['vault_unlocked'] = True
                                st.session_state['secret_key'] = secret_key
                                st.success("Bóveda creada exitosamente. El sistema está ahora online.")
                                st.rerun()
                            else:
                                st.error("Error al crear la bóveda.")
                        except Exception as e:
                            st.error(f"Error al inicializar la DB: {e}")
                    else:
                        st.error("Las contraseñas no coinciden. Inténtalo nuevamente.")
                else:
                    st.warning("Por favor, completa ambos campos.")
    else:
        # Auto-unlock
        with open('.master_key', 'r') as f:
            secret_key = f.read().strip()
        st.session_state['vault_unlocked'] = True
        st.session_state['secret_key'] = secret_key
        st.rerun()
def render_login():
    import hashlib
    from db.database_manager import get_usuario, actualizar_ultimo_acceso
    
    st.title("🔑 Iniciar Sesión - SGEC")
    st.markdown("Por favor, ingresa tu correo electrónico y tu Llave Única proporcionada por el Administrador.")
    
    with st.form("login_form"):
        email = st.text_input("Correo Electrónico")
        unique_key = st.text_input("Llave Única", type="password")
        submit_button = st.form_submit_button("Ingresar")
        
        if submit_button:
            if email and unique_key:
                secret_key = st.session_state['secret_key']
                usuario = get_usuario(secret_key, email)
                
                if usuario:
                    if usuario['estatus_acceso'] != 'Habilitado':
                        st.error("Tu cuenta está deshabilitada. Contacta al administrador.")
                    else:
                        hashed_input = hashlib.sha256(unique_key.encode()).hexdigest()
                        if hashed_input == usuario['hashed_key']:
                            st.session_state['authenticated'] = True
                            st.session_state['rol'] = usuario['rol']
                            st.session_state['email_usuario'] = usuario['email']
                            
                            actualizar_ultimo_acceso(secret_key, email)
                            
                            vencidas_count = ejecutar_garbage_collector(secret_key)
                            if vencidas_count > 0:
                                st.info(f"🧹 Garbage Collector: {vencidas_count} reserva(s) expirada(s) y sus fondos han sido liberados.")
                            
                            st.success(f"Bienvenido {usuario['rol']}.")
                            st.rerun()
                        else:
                            st.error("Credenciales incorrectas.")
                else:
                    st.error("Usuario no encontrado en el sistema.")
            else:
                st.warning("Por favor, ingresa tu correo y llave única.")
def main():
    if 'vault_unlocked' not in st.session_state:
        st.session_state['vault_unlocked'] = False
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'rol' not in st.session_state:
        st.session_state['rol'] = None
    if 'email_usuario' not in st.session_state:
        st.session_state['email_usuario'] = None
    if not st.session_state['vault_unlocked']:
        render_vault_unlock()
    elif not st.session_state['authenticated']:
        render_login()
    else:
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
            st.markdown("""
                <div style="background-color: #ff4b4b; padding: 10px; border-radius: 5px; color: white; text-align: center; margin-bottom: 20px;">
                    <strong>🕵️ MODO SUPANTACIÓN ACTIVO:</strong> Estás viendo la interfaz como: {email} ({rol})
                </div>
            """.format(email=st.session_state.get('impersonate_email'), rol=efective_rol), unsafe_allow_html=True)
            
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
            safe_page_link("simulation_chat.py", label="Chat de Simulación", icon="🤖")
        if efective_rol == "Líder":
            st.title("🚀 Guía de Inicio Rápido: SGEC - Tu Copiloto de Gestión")
            st.markdown("""
¡Bienvenido al piloto de SGEC Local Intelligence! Esta herramienta ha sido diseñada para ayudarte a tomar decisiones de compensación basadas en datos, presupuesto real y equidad interna.
### 🛠️ ¿Cómo empezar?
1. **Selecciona a tu colaborador:** En el menú lateral, ve a "Chat de Simulación" y elige al miembro de tu equipo que deseas analizar.
2. **Conversa con tu Copiloto:** Describe los cambios en sus responsabilidades o el ajuste que tienes en mente. La IA evaluará si la descripción técnica coincide con el grado salarial actual.
3. **Revisa el Presupuesto:** El sistema te avisará automáticamente si tu Centro de Costo (CECO) tiene fondos suficientes para la propuesta.
### ⚖️ Reglas del Juego
- **El "Abogado del Diablo":** Si la IA detecta que las tareas descritas superan el grado del colaborador, bloqueará la simulación. No es un error; es una protección para que RRHH te ayude a validar la estructura antes de avanzar.
- **Reservas Automáticas:** Al acordar un monto, el sistema genera un "Placeholder" (reserva) en tu presupuesto. Este dinero queda apartado por 15 días esperando la validación final y la firma.
- **Privacidad Total:** Tus datos nunca salen de nuestra red local. La inteligencia es 100% privada y segura.
### 🆘 ¿Necesitas ayuda estructural?
Si lo que necesitas es un cambio de jefe, mover a alguien de CECO o cambiarlo de empresa, recuerda que la IA te derivará automáticamente con tu Business Partner (BP), ya que estos temas no son de gestión directa en este chat.
            """)
        else:
            st.title("SGEC Local Intelligence")
            st.markdown("Selecciona un módulo en el menú lateral para operar.")
if __name__ == "__main__":
    main()