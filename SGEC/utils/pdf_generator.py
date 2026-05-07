import os
import hashlib
from fpdf import FPDF
import datetime
def generar_carta_oferta(empleado_id, nombre, cargo, nuevo_sueldo):
    out_dir = os.path.join(os.getcwd(), "outputs", "cartas")
    os.makedirs(out_dir, exist_ok=True)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="CARTA DE OFERTA / ACTUALIZACION", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.cell(200, 10, txt=f"Empleado ID: {empleado_id}", ln=True)
    pdf.cell(200, 10, txt=f"Nombre: {nombre}", ln=True)
    pdf.cell(200, 10, txt=f"Nuevo Grado/Cargo: {cargo}", ln=True)
    pdf.cell(200, 10, txt=f"Nuevo Sueldo Base: ${nuevo_sueldo:,.2f}", ln=True)
    
    filename = f"Oferta_{empleado_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(out_dir, filename)
    pdf.output(filepath)
    
    with open(filepath, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
        
    return filepath, file_hash