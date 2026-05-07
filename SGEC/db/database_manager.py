import sqlite3
import pandas as pd
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
DB_PATH = 'sgec.db'
def get_fernet(secret_key):
    salt = b'sgec_salt_v1'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return Fernet(key)
def encrypt_val(fernet_obj, val):
    if val is None or pd.isna(val) or str(val).strip() == "":
        return None
    return fernet_obj.encrypt(str(val).encode()).decode()
def decrypt_val(fernet_obj, val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return fernet_obj.decrypt(val.encode()).decode()
    except Exception:
        return val
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn
def init_db(secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Vault_Test (
        id INTEGER PRIMARY KEY,
        test_payload TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS CECOs (
        id_ceco TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        presupuesto_anual REAL NOT NULL,
        presupuesto_consumido REAL DEFAULT 0,
        presupuesto_reservado REAL DEFAULT 0
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Empleados (
        id_empleado TEXT PRIMARY KEY,
        nombre_completo TEXT NOT NULL,
        correo_electronico TEXT,
        grado_actual TEXT,
        sueldo_base TEXT,
        id_jefe_directo TEXT,
        id_ceco TEXT,
        fecha_ingreso TEXT,
        fecha_ultimo_ajuste TEXT,
        estatus TEXT,
        ruta_jerarquica TEXT,
        FOREIGN KEY (id_ceco) REFERENCES CECOs(id_ceco)
    )
    ''')
    
    try:
        cursor.execute("ALTER TABLE Empleados ADD COLUMN ruta_jerarquica TEXT")
    except Exception:
        pass
        
    try:
        cursor.execute("ALTER TABLE Empleados ADD COLUMN renta_anual TEXT")
    except Exception:
        pass
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reservas (
        id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
        id_ceco TEXT NOT NULL,
        monto REAL NOT NULL,
        descripcion TEXT,
        fecha_reserva TEXT,
        estatus TEXT DEFAULT 'EN_VALIDACION',
        justificacion_ia TEXT,
        comentario_bp TEXT,
        FOREIGN KEY (id_ceco) REFERENCES CECOs(id_ceco)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Cartas_Emitidas (
        id_carta INTEGER PRIMARY KEY AUTOINCREMENT,
        id_empleado TEXT NOT NULL,
        id_reserva INTEGER,
        hash_seguridad TEXT NOT NULL,
        fecha_generacion TEXT NOT NULL,
        FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado),
        FOREIGN KEY (id_reserva) REFERENCES Reservas(id_reserva)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Historial (
        id_historial INTEGER PRIMARY KEY AUTOINCREMENT,
        id_empleado TEXT NOT NULL,
        campo_modificado TEXT NOT NULL,
        valor_anterior TEXT,
        valor_nuevo TEXT,
        fecha_modificacion TEXT,
        usuario TEXT,
        FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reglas_Grado (
        grado TEXT PRIMARY KEY,
        sueldo_minimo REAL,
        sueldo_maximo REAL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Simulaciones_Entrenamiento (
        id_simulacion INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_prueba TEXT NOT NULL,
        system_prompt TEXT NOT NULL,
        temperatura REAL NOT NULL,
        respuesta_ia TEXT NOT NULL,
        fecha_simulacion TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Auditoria_GC (
        id_log INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_ejecucion TEXT NOT NULL,
        reservas_afectadas INTEGER NOT NULL,
        monto_total_liberado REAL NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS Conocimiento_Gym USING fts5(
        nombre_doc,
        contenido
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Usuarios (
        email TEXT PRIMARY KEY,
        id_empleado TEXT,
        hashed_key TEXT,
        rol TEXT DEFAULT 'Líder',
        estatus_acceso TEXT DEFAULT 'Deshabilitado',
        fecha_ultimo_acceso TEXT
    )
    ''')
    
    try:
        cursor.execute("ALTER TABLE Usuarios ADD COLUMN llave_enc TEXT")
    except Exception:
        pass
        
    try:
        cursor.execute("ALTER TABLE Usuarios ADD COLUMN nombre_usuario TEXT")
    except Exception:
        pass
    
    cursor.execute('''
    INSERT OR IGNORE INTO Usuarios (email, id_empleado, hashed_key, rol, estatus_acceso)
    VALUES ('admin@sgec.com', 'ADMIN_00', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Administrador', 'Habilitado')
    ''')
    
    cursor.execute("SELECT count(*) FROM Vault_Test")
    if cursor.fetchone()[0] == 0:
        f = get_fernet(secret_key)
        enc_test = encrypt_val(f, "VAULT_OK")
        cursor.execute("INSERT INTO Vault_Test (test_payload) VALUES (?)", (enc_test,))
    
    conn.commit()
    conn.close()
def test_connection(secret_key):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT test_payload FROM Vault_Test LIMIT 1")
        row = cursor.fetchone()
        if row:
            f = get_fernet(secret_key)
            dec = decrypt_val(f, row[0])
            if dec == "VAULT_OK":
                return True
        return False
    except Exception:
        return False
    finally:
        conn.close()
def execute_query(query, params=()):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        return []
    finally:
        conn.close()
def save_dataframe_to_table(secret_key, df, table_name):
    conn = get_connection()
    try:
        if table_name == 'Empleados':
            f = get_fernet(secret_key)
            df_enc = df.copy()
            for col in ['nombre_completo', 'grado_actual', 'sueldo_base', 'renta_anual']:
                if col in df_enc.columns:
                    df_enc[col] = df_enc[col].apply(lambda x: encrypt_val(f, x))
            df_to_save = df_enc
        else:
            df_to_save = df
            
        temp_table = f"temp_{table_name}"
        df_to_save.to_sql(temp_table, conn, if_exists='replace', index=False)
        
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({temp_table})")
        columns = [row[1] for row in cursor.fetchall()]
        cols_str = ", ".join(columns)
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        pk_col = next((row[1] for row in cursor.fetchall() if row[5] > 0), None)
        
        if pk_col and pk_col in columns:
            update_clause = ", ".join([f"{col} = excluded.{col}" for col in columns if col != pk_col])
            if update_clause:
                query = f"INSERT INTO {table_name} ({cols_str}) SELECT {cols_str} FROM {temp_table} WHERE 1=1 ON CONFLICT({pk_col}) DO UPDATE SET {update_clause}"
            else:
                query = f"INSERT OR IGNORE INTO {table_name} ({cols_str}) SELECT {cols_str} FROM {temp_table}"
            cursor.execute(query)
        else:
            cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({cols_str}) SELECT {cols_str} FROM {temp_table}")
            
        cursor.execute(f"DROP TABLE {temp_table}")
        conn.commit()
    finally:
        conn.close()
def _decrypt_empleado_row(f, r):
    r['nombre_completo'] = decrypt_val(f, r['nombre_completo'])
    r['grado_actual'] = decrypt_val(f, r['grado_actual'])
    try:
        r['sueldo_base'] = float(decrypt_val(f, r['sueldo_base']))
    except:
        r['sueldo_base'] = 0.0
        
    try:
        if 'renta_anual' in r and r['renta_anual'] is not None:
            r['renta_anual'] = float(decrypt_val(f, r['renta_anual']))
        else:
            r['renta_anual'] = r.get('sueldo_base', 0.0) * 12
    except:
        r['renta_anual'] = r.get('sueldo_base', 0.0) * 12
        
    return r

def recalcular_presupuestos_consumidos(secret_key):
    """
    Recalcula el presupuesto consumido de cada CECO sumando 
    la renta anualizada (sueldo_base * 12) de todos los empleados asociados.
    """
    conn = get_connection()
    try:
        f = get_fernet(secret_key)
        cursor = conn.cursor()
        
        # Obtener todos los empleados
        cursor.execute("SELECT id_ceco, sueldo_base, renta_anual FROM Empleados")
        empleados_raw = cursor.fetchall()
        
        # Primero resetear todos los consumidos a 0 para re-calcular limpio
        cursor.execute("UPDATE CECOs SET presupuesto_consumido = 0")
        
        # Agrupar por ceco
        suma_por_ceco = {}
        for row in empleados_raw:
            id_ceco = row[0]
            sueldo_enc = row[1]
            renta_enc = row[2]
            if not id_ceco or str(id_ceco).strip() == "":
                continue
                
            renta_anualizada = 0.0
            if renta_enc is not None:
                try:
                    renta_anualizada = float(decrypt_val(f, renta_enc))
                except:
                    pass
                    
            if renta_anualizada == 0.0:
                try:
                    sueldo = float(decrypt_val(f, sueldo_enc))
                    renta_anualizada = sueldo * 12
                except:
                    pass
            
            if id_ceco in suma_por_ceco:
                suma_por_ceco[id_ceco] += renta_anualizada
            else:
                suma_por_ceco[id_ceco] = renta_anualizada
                
        # Actualizar en la base de datos
        for ceco_id, suma in suma_por_ceco.items():
            cursor.execute("UPDATE CECOs SET presupuesto_consumido = ? WHERE id_ceco = ?", (suma, ceco_id))
            
        conn.commit()
    except Exception as e:
        print(f"Error al recalcular presupuestos: {e}")
    finally:
        conn.close()
def get_empleados(secret_key):
    f = get_fernet(secret_key)
    query = "SELECT id_empleado, nombre_completo, grado_actual, sueldo_base, renta_anual, id_ceco, correo_electronico FROM Empleados"
    res = execute_query(query)
    return [_decrypt_empleado_row(f, r) for r in res]
def get_empleado_by_id(secret_key, empleado_id):
    f = get_fernet(secret_key)
    query = "SELECT id_empleado, nombre_completo, grado_actual, sueldo_base, renta_anual, id_ceco, correo_electronico FROM Empleados WHERE id_empleado = ?"
    res = execute_query(query, (empleado_id,))
    if res:
        return _decrypt_empleado_row(f, res[0])
    return None
def get_empleados_por_lider(secret_key, email_lider):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_empleado, rol FROM Usuarios WHERE email = ?", (email_lider,))
        row = cursor.fetchone()
        if not row:
            return []
            
        id_emp_lider, rol = row
        if rol in ["Administrador", "Business Partner"]:
            cursor.execute("SELECT id_empleado, nombre_completo, grado_actual, sueldo_base, id_ceco FROM Empleados")
        else:
            search_pattern = f"%|{id_emp_lider}|%"
            cursor.execute("""
                SELECT id_empleado, nombre_completo, grado_actual, sueldo_base, id_ceco 
                FROM Empleados 
                WHERE ruta_jerarquica LIKE ? OR id_empleado = ?
            """, (search_pattern, id_emp_lider))
            
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        
        f = get_fernet(secret_key)
        lista = [dict(zip(columns, r)) for r in results]
        return [_decrypt_empleado_row(f, r) for r in lista]
    finally:
        conn.close()
def get_reglas_grado(secret_key):
    query = "SELECT grado, sueldo_minimo, sueldo_maximo FROM Reglas_Grado"
    reglas = execute_query(query)
    if not reglas:
        return "No hay reglas de grado definidas en la base de datos."
    texto_reglas = "Reglas Salariales por Grado:\n"
    for r in reglas:
        texto_reglas += f"- Grado {r['grado']}: Sueldo Mínimo {r['sueldo_minimo']} | Sueldo Máximo {r['sueldo_maximo']}\n"
    return texto_reglas
def get_ceco_completo(secret_key, id_ceco):
    query = "SELECT * FROM CECOs WHERE id_ceco = ?"
    results = execute_query(query, (id_ceco,))
    return results[0] if results else None
def crear_reserva(secret_key, id_ceco, monto, descripcion, fecha, estatus="EN_VALIDACION", justificacion_ia=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Reservas (id_ceco, monto, descripcion, fecha_reserva, estatus, justificacion_ia) VALUES (?, ?, ?, ?, ?, ?)",
                       (id_ceco, monto, descripcion, fecha, estatus, justificacion_ia))
        id_reserva = cursor.lastrowid
        cursor.execute("UPDATE CECOs SET presupuesto_reservado = presupuesto_reservado + ? WHERE id_ceco = ?", (monto, id_ceco))
        conn.commit()
        return id_reserva
    finally:
        conn.close()
def aprobar_reserva(secret_key, id_reserva, comentario_bp=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Reservas SET estatus = 'APROBADO', comentario_bp = ? WHERE id_reserva = ?", (comentario_bp, id_reserva))
        conn.commit()
    finally:
        conn.close()
def rechazar_reserva(secret_key, id_reserva, id_ceco, monto, comentario_bp):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Reservas SET estatus = 'RECHAZADO', comentario_bp = ? WHERE id_reserva = ?", (comentario_bp, id_reserva))
        cursor.execute("UPDATE CECOs SET presupuesto_reservado = presupuesto_reservado - ? WHERE id_ceco = ?", (monto, id_ceco))
        conn.commit()
    finally:
        conn.close()
def solicitar_ajuste_reserva(secret_key, id_reserva, comentario_bp):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Reservas SET estatus = 'AJUSTE_REQUERIDO', comentario_bp = ? WHERE id_reserva = ?", (comentario_bp, id_reserva))
        conn.commit()
    finally:
        conn.close()
def guardar_simulacion_gym(secret_key, prompt_prueba, system_prompt, temperatura, respuesta_ia, fecha):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Simulaciones_Entrenamiento (prompt_prueba, system_prompt, temperatura, respuesta_ia, fecha_simulacion) 
            VALUES (?, ?, ?, ?, ?)
        """, (prompt_prueba, system_prompt, temperatura, respuesta_ia, fecha))
        conn.commit()
    finally:
        conn.close()
def guardar_carta_emitida(secret_key, id_empleado, id_reserva, hash_seguridad, fecha):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Cartas_Emitidas (id_empleado, id_reserva, hash_seguridad, fecha_generacion) VALUES (?, ?, ?, ?)",
                       (id_empleado, id_reserva, hash_seguridad, fecha))
        cursor.execute("SELECT id_ceco, monto FROM Reservas WHERE id_reserva = ?", (id_reserva,))
        row = cursor.fetchone()
        if row:
            id_ceco, monto = row
            cursor.execute("UPDATE CECOs SET presupuesto_reservado = presupuesto_reservado - ?, presupuesto_consumido = presupuesto_consumido + ? WHERE id_ceco = ?", 
                           (monto, monto, id_ceco))
        conn.commit()
    finally:
        conn.close()
def ejecutar_garbage_collector(secret_key):
    import datetime
    conn = get_connection()
    try:
        cursor = conn.cursor()
        limite_fecha = (datetime.datetime.now() - datetime.timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT r.id_reserva, r.id_ceco, r.monto 
            FROM Reservas r
            LEFT JOIN Cartas_Emitidas c ON r.id_reserva = c.id_reserva
            WHERE c.id_carta IS NULL 
              AND r.estatus IN ('EN_VALIDACION', 'APROBADO')
              AND r.fecha_reserva < ?
        """, (limite_fecha,))
        vencidas = cursor.fetchall()
        count = 0
        monto_total = 0.0
        for row in vencidas:
            id_res, id_ceco, monto = row
            cursor.execute("UPDATE Reservas SET estatus = 'EXPIRADO', comentario_bp = 'Expirado por Garbage Collector (> 15 días)' WHERE id_reserva = ?", (id_res,))
            cursor.execute("UPDATE CECOs SET presupuesto_reservado = presupuesto_reservado - ? WHERE id_ceco = ?", (monto, id_ceco))
            count += 1
            monto_total += monto
            
        if count > 0:
            fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO Auditoria_GC (fecha_ejecucion, reservas_afectadas, monto_total_liberado) VALUES (?, ?, ?)", 
                           (fecha_str, count, monto_total))
        conn.commit()
        return count
    finally:
        conn.close()
def get_usuario(secret_key, email):
    query = "SELECT * FROM Usuarios WHERE email = ?"
    results = execute_query(query, (email,))
    return results[0] if results else None
def actualizar_ultimo_acceso(secret_key, email):
    import datetime
    conn = get_connection()
    try:
        cursor = conn.cursor()
        fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE Usuarios SET fecha_ultimo_acceso = ? WHERE email = ?", (fecha_str, email))
        conn.commit()
    finally:
        conn.close()
def get_all_usuarios(secret_key):
    query = "SELECT email, id_empleado, rol, estatus_acceso, fecha_ultimo_acceso FROM Usuarios ORDER BY email"
    return execute_query(query)
def get_usuarios_habilitados(secret_key):
    query = "SELECT email, rol, estatus_acceso FROM Usuarios WHERE estatus_acceso = 'Habilitado' AND rol != 'Administrador'"
    return execute_query(query)
def actualizar_usuario(secret_key, email, rol, estatus, hashed_key=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if hashed_key:
            cursor.execute("UPDATE Usuarios SET rol = ?, estatus_acceso = ?, hashed_key = ? WHERE email = ?", (rol, estatus, hashed_key, email))
        else:
            cursor.execute("UPDATE Usuarios SET rol = ?, estatus_acceso = ? WHERE email = ?", (rol, estatus, email))
        conn.commit()
    finally:
        conn.close()
def get_todas_las_reservas(secret_key):
    query = "SELECT * FROM Reservas"
    return execute_query(query)
def get_todos_los_cecos(secret_key):
    query = "SELECT * FROM CECOs"
    return execute_query(query)
def get_reservas_pendientes(secret_key):
    query = """
        SELECT r.id_reserva, r.id_ceco, r.monto, r.descripcion, r.fecha_reserva, r.estatus, r.justificacion_ia
        FROM Reservas r
        WHERE r.estatus = 'EN_VALIDACION'
    """
    return execute_query(query)
def get_reservas_y_cartas(secret_key):
    query = """
        SELECT r.id_reserva, r.id_ceco, r.monto, r.descripcion, r.fecha_reserva, r.estatus,
               c.hash_seguridad, c.fecha_generacion
        FROM Reservas r
        LEFT JOIN Cartas_Emitidas c ON r.id_reserva = c.id_reserva
        ORDER BY r.id_reserva DESC
    """
    return execute_query(query)
def get_todos_empleados(secret_key):
    return get_empleados(secret_key)

def guardar_conocimiento_gym(secret_key, nombre_doc, texto):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Limpiar texto
        import re
        texto_limpio = re.sub(r'\s+', ' ', texto).strip()
        
        # Fragmentación simple (aprox 1500 caracteres por chunk)
        chunks = []
        words = texto_limpio.split(' ')
        current_chunk = []
        current_length = 0
        for w in words:
            current_chunk.append(w)
            current_length += len(w) + 1
            if current_length > 1500:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        for ch in chunks:
            if len(ch.strip()) > 10:
                cursor.execute("INSERT INTO Conocimiento_Gym (nombre_doc, contenido) VALUES (?, ?)", (nombre_doc, ch))
                
        conn.commit()
        return len(chunks)
    finally:
        conn.close()

def buscar_conocimiento_gym(query_text, limit=5):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        import re
        clean_query = re.sub(r'[^\w\s]', ' ', query_text)
        words = [w for w in clean_query.split() if len(w) > 3]
        
        if not words:
            return []
            
        match_query = " OR ".join(words)
        
        sql = """
            SELECT nombre_doc, contenido 
            FROM Conocimiento_Gym 
            WHERE Conocimiento_Gym MATCH ? 
            ORDER BY rank 
            LIMIT ?
        """
        cursor.execute(sql, (match_query, limit))
        results = cursor.fetchall()
        return [{"doc": r[0], "texto": r[1]} for r in results]
    except Exception as e:
        print(f"Error en búsqueda FTS5: {e}")
        return []
    finally:
        conn.close()

def vaciar_conocimiento_gym(secret_key):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Conocimiento_Gym")
        conn.commit()
    finally:
        conn.close()

def obtener_stats_conocimiento(secret_key):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM Conocimiento_Gym")
        total_chunks = cursor.fetchone()[0]
        
        cursor.execute("SELECT count(DISTINCT nombre_doc) FROM Conocimiento_Gym")
        total_docs = cursor.fetchone()[0]
        return {"chunks": total_chunks, "docs": total_docs}
    except Exception:
        return {"chunks": 0, "docs": 0}
    finally:
        conn.close()
