import os
import sys
import shutil
import subprocess
import urllib.request
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import traceback

# Evitar ventanas negras al usar subprocess
CREATE_NO_WINDOW = 0x08000000

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador SGEC - Cencosud")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        # Estilo moderno
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=25)
        
        # Encabezado
        header_frame = tk.Frame(self.root, bg="#1E3A8A", height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_label = tk.Label(header_frame, text="Smart Generation Engine (SGEC)", fg="white", bg="#1E3A8A", font=("Helvetica", 16, "bold"))
        header_label.pack(pady=25)
        
        # Contenido
        content_frame = tk.Frame(self.root, padx=40, pady=30)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_var = tk.StringVar(value="Preparando instalación...")
        self.status_label = ttk.Label(content_frame, textvariable=self.status_var, font=("Helvetica", 11, "bold"))
        self.status_label.pack(pady=(10, 5))
        
        self.progress = ttk.Progressbar(content_frame, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=15)
        
        self.detail_var = tk.StringVar(value="")
        self.detail_label = ttk.Label(content_frame, textvariable=self.detail_var, font=("Helvetica", 9), foreground="gray")
        self.detail_label.pack(pady=5)
        
        self.btn_close = ttk.Button(content_frame, text="Cerrar Instalador", command=self.root.destroy, state=tk.DISABLED)
        self.btn_close.pack(side=tk.BOTTOM, pady=20)
        
        # Auto-start
        self.start_installation()

    def update_progress(self, value, status_text, detail_text=""):
        def _update():
            self.progress['value'] = value
            if status_text:
                self.status_var.set(status_text)
            if detail_text is not None:
                self.detail_var.set(detail_text)
        self.root.after(0, _update)

    def start_installation(self):
        thread = threading.Thread(target=self.run_install)
        thread.daemon = True
        thread.start()

    def run_install(self):
        INSTALL_DIR = r"C:\SGEC"
        try:
            self.update_progress(5, "Iniciando instalación...", f"Directorio destino: {INSTALL_DIR}")
            if not os.path.exists(INSTALL_DIR):
                os.makedirs(INSTALL_DIR, exist_ok=True)
                
            self.update_progress(10, "Copiando archivos del sistema (Cerebro Core)...", "")
            for item in ['app.py', 'requirements.txt', 'db', 'pages', 'utils']:
                src = resource_path(item)
                dst = os.path.join(INSTALL_DIR, item)
                if os.path.exists(src):
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                        
            os.makedirs(os.path.join(INSTALL_DIR, "outputs", "cartas"), exist_ok=True)
            os.makedirs(os.path.join(INSTALL_DIR, "db"), exist_ok=True)
            
            self.update_progress(20, "Verificando motor de IA local (Ollama)...", "")
            try:
                subprocess.run(["where", "ollama"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
            except subprocess.CalledProcessError:
                self.update_progress(25, "Descargando Ollama...", "Descargando instalador oficial...")
                ollama_path = os.path.join(INSTALL_DIR, "OllamaSetup.exe")
                
                def show_progress(block_num, block_size, total_size):
                    downloaded = block_num * block_size
                    if total_size > 0:
                        percent = downloaded * 100 / total_size
                        self.update_progress(25 + (percent * 0.15), None, f"{downloaded/(1024*1024):.1f} MB / {total_size/(1024*1024):.1f} MB")
                
                urllib.request.urlretrieve('https://ollama.com/download/OllamaSetup.exe', ollama_path, reporthook=show_progress)
                self.update_progress(40, "Instalando Ollama...", "ATENCIÓN: Por favor sigue los pasos en la ventana emergente de instalación.")
                subprocess.run([ollama_path], check=False)
                try:
                    os.remove(ollama_path)
                except Exception:
                    pass
            
            self.update_progress(45, "Descargando Red Neuronal Llama 3 (4.7 GB)...", "Esto puede tardar varios minutos dependiendo de tu conexión. No cierres la ventana.")
            subprocess.run(["ollama", "pull", "llama3"], check=False, creationflags=CREATE_NO_WINDOW)
            
            self.update_progress(70, "Configurando Entorno Virtual Python...", "Aislando el ecosistema...")
            venv_dir = os.path.join(INSTALL_DIR, "venv")
            if not os.path.exists(venv_dir):
                subprocess.run(["python", "-m", "venv", venv_dir], check=True, creationflags=CREATE_NO_WINDOW)
            
            self.update_progress(80, "Instalando librerías y dependencias (Pip)...", "Instalando Pandas, Streamlit y PyPDF2...")
            pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
            req_file = os.path.join(INSTALL_DIR, "requirements.txt")
            
            subprocess.run([pip_exe, "install", "-r", req_file], capture_output=True, text=True, check=True, creationflags=CREATE_NO_WINDOW)
            
            self.update_progress(90, "Configurando Accesos Directos...", "Generando archivos de ejecución BAT y PS1.")
            bat_path = os.path.join(INSTALL_DIR, "start_sgec.bat")
            with open(bat_path, "w") as f:
                f.write("@echo off\n")
                f.write("cd /d %~dp0\n")
                f.write("call venv\\Scripts\\activate.bat\n")
                f.write("start /B \"\" streamlit run app.py --server.headless true\n")
                f.write("timeout /t 3 /nobreak >nul\n")
                f.write("start http://localhost:8501\n")
                
            ps_script = os.path.join(INSTALL_DIR, "create_shortcut.ps1")
            with open(ps_script, "w") as f:
                f.write('$WshShell = New-Object -comObject WScript.Shell\n')
                f.write('$Shortcut = $WshShell.CreateShortcut("$Home\\Desktop\\SGEC - Gestion Local.lnk")\n')
                f.write(f'$Shortcut.TargetPath = "{bat_path}"\n')
                f.write(f'$Shortcut.WorkingDirectory = "{INSTALL_DIR}"\n')
                f.write('$Shortcut.Description = "Iniciar SGEC"\n')
                # Try to apply icon if possible
                f.write(f'$Shortcut.IconLocation = "{INSTALL_DIR}\\app.py, 0"\n')
                f.write('$Shortcut.Save()\n')
                
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script], check=False, creationflags=CREATE_NO_WINDOW)
            try:
                os.remove(ps_script)
            except Exception:
                pass
                
            self.update_progress(100, "¡Instalación Completada Exitosamente!", "Ya puedes iniciar el sistema desde el acceso directo del escritorio.")
            
            def _finish():
                self.btn_close.config(state=tk.NORMAL)
            self.root.after(0, _finish)
            
        except Exception as e:
            error_details = traceback.format_exc()
            self.update_progress(0, "❌ Error Crítico en la Instalación", str(e))
            def _show_err():
                self.btn_close.config(state=tk.NORMAL)
                messagebox.showerror("Error Fatal", f"Ocurrió un error:\n{str(e)}\n\nDetalles guardados en C:\\SGEC\\error_log.txt")
                try:
                    with open(r"C:\SGEC\error_log.txt", "w") as log:
                        log.write(error_details)
                except:
                    pass
            self.root.after(0, _show_err)

def main():
    root = tk.Tk()
    
    # Try to set icon if it exists
    icon_path = resource_path('icon.ico')
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except:
            pass
            
    app = InstallerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
