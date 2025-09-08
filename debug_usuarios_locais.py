#!/usr/bin/env python3
"""
Debug para verificar usuários locais e seus UUIDs
"""
import sqlite3
import os

def debug_usuarios_locais():
    """Verificar usuários locais e seus UUIDs"""
    db_path = os.path.expanduser("~/AppData/Roaming/SistemaGestao/database/sistema.db")
    
    print("=== DEBUG USUÁRIOS LOCAIS ===")
    print(f"Banco: {db_path}")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar todos os usuários
        cursor.execute("""
            SELECT id, nome, usuario, is_admin, ativo, 
                   COALESCE(uuid, 'NULL') as uuid, 
                   COALESCE(synced, 'NULL') as synced,
                   created_at, updated_at
            FROM usuarios
            ORDER BY id
        """)
        usuarios = cursor.fetchall()
        
        print(f"Total de usuários encontrados: {len(usuarios)}")
        print()
        
        for usuario in usuarios:
            print(f"ID: {usuario[0]}")
            print(f"Nome: {usuario[1]}")
            print(f"Login: {usuario[2]}")
            print(f"Admin: {usuario[3]}")
            print(f"Ativo: {usuario[4]}")
            print(f"UUID: {usuario[5]}")
            print(f"Synced: {usuario[6]}")
            print(f"Created: {usuario[7]}")
            print(f"Updated: {usuario[8]}")
            print("-" * 40)
        
        # Verificar critérios de sincronização
        print("\n=== CRITÉRIOS DE SINCRONIZAÇÃO ===")
        
        # Usuários que deveriam ser sincronizados (servidor vazio)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM usuarios 
            WHERE uuid IS NOT NULL AND uuid != '' AND ativo = 1
        """)
        usuarios_com_uuid = cursor.fetchone()[0]
        print(f"Usuários com UUID válido e ativos: {usuarios_com_uuid}")
        
        # Usuários não sincronizados
        cursor.execute("""
            SELECT COUNT(*) 
            FROM usuarios 
            WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND uuid != '' AND ativo = 1
        """)
        usuarios_nao_sync = cursor.fetchone()[0]
        print(f"Usuários não sincronizados: {usuarios_nao_sync}")
        
        # Listar usuários sem UUID
        cursor.execute("""
            SELECT id, nome, usuario
            FROM usuarios 
            WHERE (uuid IS NULL OR uuid = '') AND ativo = 1
        """)
        usuarios_sem_uuid = cursor.fetchall()
        
        if usuarios_sem_uuid:
            print(f"\n⚠️  Usuários SEM UUID ({len(usuarios_sem_uuid)}):")
            for u in usuarios_sem_uuid:
                print(f"  - ID {u[0]}: {u[1]} (login: {u[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_usuarios_locais()
