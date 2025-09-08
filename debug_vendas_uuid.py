#!/usr/bin/env python3
"""
Debug para verificar vendas e seus UUIDs
"""
import sqlite3
import os

def debug_vendas_locais():
    """Verificar vendas locais e seus UUIDs"""
    db_path = os.path.expanduser("~/AppData/Roaming/SistemaGestao/database/sistema.db")
    
    print("=== DEBUG VENDAS LOCAIS ===")
    print(f"Banco: {db_path}")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar todas as vendas
        cursor.execute("""
            SELECT id, data_venda, total, status, 
                   COALESCE(uuid, 'NULL') as uuid, 
                   COALESCE(synced, 'NULL') as synced,
                   LENGTH(COALESCE(uuid, '')) as uuid_length
            FROM vendas
            WHERE status != 'Anulada'
            ORDER BY id
        """)
        vendas = cursor.fetchall()
        
        print(f"Total de vendas válidas: {len(vendas)}")
        print()
        
        for venda in vendas:
            print(f"ID: {venda[0]}")
            print(f"Data: {venda[1]}")
            print(f"Total: MT {venda[2]}")
            print(f"Status: {venda[3]}")
            print(f"UUID: {venda[4]}")
            print(f"UUID Length: {venda[6]}")
            print(f"Synced: {venda[5]}")
            
            # Verificar se UUID é válido
            uuid_str = venda[4]
            if uuid_str and uuid_str != 'NULL':
                try:
                    import uuid
                    uuid.UUID(uuid_str)
                    print("✅ UUID válido")
                except ValueError:
                    print("❌ UUID INVÁLIDO!")
            else:
                print("⚠️  UUID ausente")
            
            print("-" * 40)
        
        # Verificar usuários também
        print("\n=== DEBUG USUÁRIOS LOCAIS ===")
        cursor.execute("""
            SELECT id, nome, usuario, is_admin, ativo, 
                   COALESCE(uuid, 'NULL') as uuid, 
                   COALESCE(synced, 'NULL') as synced,
                   LENGTH(COALESCE(uuid, '')) as uuid_length
            FROM usuarios
            ORDER BY id
        """)
        usuarios = cursor.fetchall()
        
        print(f"Total de usuários: {len(usuarios)}")
        print()
        
        for usuario in usuarios:
            print(f"ID: {usuario[0]}")
            print(f"Nome: {usuario[1]}")
            print(f"Login: {usuario[2]}")
            print(f"Admin: {usuario[3]}")
            print(f"Ativo: {usuario[4]}")
            print(f"UUID: {usuario[5]}")
            print(f"UUID Length: {usuario[7]}")
            print(f"Synced: {usuario[6]}")
            
            # Verificar se UUID é válido
            uuid_str = usuario[5]
            if uuid_str and uuid_str != 'NULL':
                try:
                    import uuid
                    uuid.UUID(uuid_str)
                    print("✅ UUID válido")
                except ValueError:
                    print("❌ UUID INVÁLIDO!")
            else:
                print("⚠️  UUID ausente")
            
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_vendas_locais()
