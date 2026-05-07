import subprocess
import sys
import os
def main():
    print("=== Iniciando Constructor del Instalador SGEC ===")
    
    try:
        import PyInstaller
    except ImportError:
        print("Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    print("Compilando el ejecutable SGEC_Instalador.exe...")
    
    sep = ';' if os.name == 'nt' else ':'
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",  # Esto oculta la consola negra
        "--name", "SGEC_Instalador",
        "--uac-admin",
        "--icon=icon.ico",
        f"--add-data=icon.ico{sep}.",
        f"--add-data=app.py{sep}.",
        f"--add-data=requirements.txt{sep}.",
        f"--add-data=db{sep}db",
        f"--add-data=pages{sep}pages",
        f"--add-data=utils{sep}utils",
        "launcher.py"
    ]
    
    subprocess.run(cmd, check=True)
    
    print("\n========================================================")
    print("CONSTRUCCION FINALIZADA.")
    print("El archivo ejecutable se encuentra en: dist/SGEC_Instalador.exe")
    print("========================================================")
if __name__ == "__main__":
    main()
