#!/usr/bin/env python3
"""
Script para debugar vendas no SQLite local.
"""

import sqlite3
import os

def main():
    db_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "SistemaGestao", "database", "sistema.db")
    
    print(f"=== DEBUG VENDAS LOCAL ===")
    print(f"Banco: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Listar todas as vendas
    print("\n=== TODAS AS VENDAS ===")
    cursor.execute("""
        SELECT id, data_venda, total, status, synced, uuid
        FROM vendas 
        ORDER BY id
    """)
    vendas = cursor.fetchall()
    
    for venda in vendas:
        print(f"ID: {venda['id']}, Data: {venda['data_venda']}, Total: MT {venda['total']}, Status: {venda['status']}, Synced: {venda['synced']}, UUID: {venda['uuid']}")
    
    # Vendas não sincronizadas
    print("\n=== VENDAS NÃO SINCRONIZADAS ===")
    cursor.execute("""
        SELECT id, data_venda, total, status, synced, uuid
        FROM vendas 
        WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND uuid != ''
          AND status != 'Anulada'
        ORDER BY id
    """)
    nao_sync = cursor.fetchall()
    
    for venda in nao_sync:
        print(f"ID: {venda['id']}, Data: {venda['data_venda']}, Total: MT {venda['total']}, Status: {venda['status']}, Synced: {venda['synced']}, UUID: {venda['uuid']}")
    
    print(f"\nTotal de vendas: {len(vendas)}")
    print(f"Vendas não sincronizadas: {len(nao_sync)}")
    
    conn.close()

if __name__ == "__main__":
    main()
