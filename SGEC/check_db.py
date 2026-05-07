import sqlite3
import os

print(f"Current Directory: {os.getcwd()}")
print("Databases in directory:")
for f in os.listdir():
    if f.endswith('.db'):
        print(f" - {f}")

for db in [f for f in os.listdir() if f.endswith('.db')]:
    print(f"\nTables in {db}:")
    try:
        conn = sqlite3.connect(db)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for t in tables:
            print(f"  - {t[0]}")
            if t[0] == 'Usuarios':
                cols = conn.execute("PRAGMA table_info(Usuarios)").fetchall()
                print(f"    Columns in Usuarios: {[c[1] for c in cols]}")
    except Exception as e:
        print(f"Error: {e}")
