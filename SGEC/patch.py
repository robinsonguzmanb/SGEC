import os

def patch_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
        else:
            print(f"Warning: Could not find '{old[:50]}...' in {filepath}")
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Patch database_manager.py
db_path = r'db/database_manager.py'
db_replacements = [
    (
        'cursor.execute("ALTER TABLE Empleados ADD COLUMN ruta_jerarquica TEXT")\n    except Exception:\n        pass',
        'cursor.execute("ALTER TABLE Empleados ADD COLUMN ruta_jerarquica TEXT")\n    except Exception:\n        pass\n        \n    try:\n        cursor.execute("ALTER TABLE Empleados ADD COLUMN renta_anual TEXT")\n    except Exception:\n        pass'
    ),
    (
        "for col in ['nombre_completo', 'grado_actual', 'sueldo_base']:",
        "for col in ['nombre_completo', 'grado_actual', 'sueldo_base', 'renta_anual']:"
    ),
    (
        "    try:\n        r['sueldo_base'] = float(decrypt_val(f, r['sueldo_base']))\n    except:\n        r['sueldo_base'] = 0.0\n    return r",
        "    try:\n        r['sueldo_base'] = float(decrypt_val(f, r['sueldo_base']))\n    except:\n        r['sueldo_base'] = 0.0\n        \n    try:\n        if 'renta_anual' in r and r['renta_anual'] is not None:\n            r['renta_anual'] = float(decrypt_val(f, r['renta_anual']))\n        else:\n            r['renta_anual'] = r.get('sueldo_base', 0.0) * 12\n    except:\n        r['renta_anual'] = r.get('sueldo_base', 0.0) * 12\n        \n    return r"
    ),
    (
        'cursor.execute("SELECT id_ceco, sueldo_base FROM Empleados")',
        'cursor.execute("SELECT id_ceco, sueldo_base, renta_anual FROM Empleados")'
    ),
    (
        "        for row in empleados_raw:\n            id_ceco = row[0]\n            sueldo_enc = row[1]",
        "        for row in empleados_raw:\n            id_ceco = row[0]\n            sueldo_enc = row[1]\n            renta_enc = row[2]"
    ),
    (
        "            try:\n                sueldo = float(decrypt_val(f, sueldo_enc))\n            except:\n                sueldo = 0.0\n                \n            renta_anualizada = sueldo * 12",
        "            renta_anualizada = 0.0\n            if renta_enc is not None:\n                try:\n                    renta_anualizada = float(decrypt_val(f, renta_enc))\n                except:\n                    pass\n                    \n            if renta_anualizada == 0.0:\n                try:\n                    sueldo = float(decrypt_val(f, sueldo_enc))\n                    renta_anualizada = sueldo * 12\n                except:\n                    pass"
    ),
    (
        'query = "SELECT id_empleado, nombre_completo, grado_actual, sueldo_base, id_ceco FROM Empleados"',
        'query = "SELECT id_empleado, nombre_completo, grado_actual, sueldo_base, renta_anual, id_ceco FROM Empleados"'
    ),
    (
        'query = "SELECT id_empleado, nombre_completo, grado_actual, sueldo_base, id_ceco FROM Empleados WHERE id_empleado = ?"',
        'query = "SELECT id_empleado, nombre_completo, grado_actual, sueldo_base, renta_anual, id_ceco FROM Empleados WHERE id_empleado = ?"'
    )
]
patch_file(db_path, db_replacements)

# Patch admin_ingestion.py
ingest_path = r'pages/admin_ingestion.py'
ingest_replacements = [
    (
        "'sueldo_base': 'Sueldo Base',",
        "'sueldo_base': 'Sueldo Base',\n                'renta_anual': 'Renta Anualizada',"
    )
]
patch_file(ingest_path, ingest_replacements)
print("Patching complete!")
