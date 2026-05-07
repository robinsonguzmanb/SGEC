import os
import glob

print("Aplicando parche de rutas a app.py...")
with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

if "import sys" not in content[:200]:
    content = content.replace(
        "import streamlit as st",
        "import streamlit as st\nimport sys\nimport os\nsys.path.append(os.path.dirname(os.path.abspath(__file__)))"
    )
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("app.py parchado exitosamente.")
else:
    print("app.py ya estaba parchado.")

print("\nAplicando parche de rutas a la carpeta pages/...")
for filepath in glob.glob("pages/*.py"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "import sys" not in content[:200]:
        content = content.replace(
            "import streamlit as st",
            "import streamlit as st\nimport sys\nimport os\nsys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))"
        )
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{filepath} parchado exitosamente.")
    else:
        print(f"{filepath} ya estaba parchado.")

print("\n¡Parche completado! Ahora puedes compilar de nuevo.")