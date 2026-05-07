import os

def patch_file(filepath, replacements):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath}, does not exist.")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
        else:
            print(f"Warning: Could not find '{old[:50]}...' in {filepath}")
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

patch_file('app.py', [('use_container_width=True', "width='stretch'")])
patch_file('pages/admin_access.py', [('use_container_width=True', "width='stretch'")])
patch_file('pages/simulation_chat.py', [('use_container_width=True', "width='stretch'")])
patch_file('pages/reporteria.py', [('use_container_width=True', "width='stretch'")])

ingest_replacements = [
    ('st.dataframe(df_emp.head(5))', 'st.dataframe(df_emp.head(5).astype(str))'),
    ('st.dataframe(df_ceco.head(5))', 'st.dataframe(df_ceco.head(5).astype(str))')
]
patch_file('pages/admin_ingestion.py', ingest_replacements)

print("Patching complete!")
