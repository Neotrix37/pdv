#!/usr/bin/env python3
"""
Script para adicionar UUIDs faltantes em clientes e vendas
"""
import sqlite3
import uuid

def adicionar_uuids_faltantes():
    """Adiciona UUIDs para clientes e vendas que não têm."""
    print("=== ADICIONANDO UUIDS FALTANTES ===")
    
    db_path = r"C:\Users\saide\AppData\Roaming\SistemaGestao\database\sistema.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Adicionar UUIDs para clientes sem UUID
        cursor.execute("""
            SELECT id, nome FROM clientes 
            WHERE uuid IS NULL OR uuid = ''
        """)
        clientes_sem_uuid = cursor.fetchall()
        
        print(f"Clientes sem UUID: {len(clientes_sem_uuid)}")
        for cliente in clientes_sem_uuid:
            novo_uuid = str(uuid.uuid4())
            cursor.execute("""
                UPDATE clientes 
                SET uuid = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (novo_uuid, cliente[0]))
            print(f"  UUID adicionado para cliente {cliente[1]}: {novo_uuid}")
        
        # 2. Adicionar UUIDs para vendas sem UUID
        cursor.execute("""
            SELECT id, data_venda, total FROM vendas 
            WHERE uuid IS NULL OR uuid = ''
        """)
        vendas_sem_uuid = cursor.fetchall()
        
        print(f"Vendas sem UUID: {len(vendas_sem_uuid)}")
        for venda in vendas_sem_uuid:
            novo_uuid = str(uuid.uuid4())
            cursor.execute("""
                UPDATE vendas 
                SET uuid = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (novo_uuid, venda[0]))
            print(f"  UUID adicionado para venda {venda[0]} (MT {venda[2]}): {novo_uuid}")
        
        conn.commit()
        
        # 3. Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE uuid IS NOT NULL AND uuid != ''")
        clientes_com_uuid = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vendas WHERE uuid IS NOT NULL AND uuid != ''")
        vendas_com_uuid = cursor.fetchone()[0]
        
        print(f"Resultado:")
        print(f"  Clientes com UUID: {clientes_com_uuid}")
        print(f"  Vendas com UUID: {vendas_com_uuid}")
        
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()
    
    print("=== UUIDS ADICIONADOS ===")

if __name__ == "__main__":
    adicionar_uuids_faltantes()
