@echo off
echo === VERIFICANDO USUARIOS E VENDAS LOCAIS ===
echo.

echo Verificando usuarios...
python -c "
import sqlite3
import os

db_path = os.path.expanduser('~/AppData/Roaming/SistemaGestao/database/sistema.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('=== USUARIOS ===')
cursor.execute('''
    SELECT id, nome, usuario, is_admin, ativo, 
           COALESCE(uuid, 'NULL') as uuid, 
           COALESCE(synced, 'NULL') as synced
    FROM usuarios
    ORDER BY id
''')
usuarios = cursor.fetchall()

for u in usuarios:
    print(f'ID: {u[0]} | Nome: {u[1]} | Login: {u[2]} | UUID: {u[5]} | Synced: {u[6]}')

print()
print('=== VENDAS ===')
cursor.execute('''
    SELECT id, data_venda, total, status, 
           COALESCE(uuid, 'NULL') as uuid, 
           COALESCE(synced, 'NULL') as synced
    FROM vendas
    WHERE status != \"Anulada\"
    ORDER BY id
''')
vendas = cursor.fetchall()

for v in vendas:
    print(f'ID: {v[0]} | Data: {v[1]} | Total: {v[2]} | UUID: {v[4]} | Synced: {v[5]}')

conn.close()
"

echo.
echo === VERIFICACAO CONCLUIDA ===
pause
