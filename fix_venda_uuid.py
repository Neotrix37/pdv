#!/usr/bin/env python3
"""
Script para corrigir vendas sem UUID e sincronizar.
"""

import sqlite3
import os
import uuid
import asyncio
import sys

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repositories.venda_repository import VendaRepository

def fix_vendas_sem_uuid():
    """Adiciona UUID para vendas que não têm."""
    db_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "SistemaGestao", "database", "sistema.db")
    
    print("=== CORRIGINDO VENDAS SEM UUID ===")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Buscar vendas sem UUID
    cursor.execute("""
        SELECT id, data_venda, total, status
        FROM vendas 
        WHERE uuid IS NULL OR uuid = ''
    """)
    vendas_sem_uuid = cursor.fetchall()
    
    print(f"Encontradas {len(vendas_sem_uuid)} vendas sem UUID")
    
    for venda in vendas_sem_uuid:
        novo_uuid = str(uuid.uuid4())
        cursor.execute("""
            UPDATE vendas 
            SET uuid = ?, synced = 0
            WHERE id = ?
        """, (novo_uuid, venda['id']))
        print(f"Venda ID {venda['id']} (MT {venda['total']}) recebeu UUID: {novo_uuid}")
    
    conn.commit()
    conn.close()
    print("✅ UUIDs corrigidos!")

async def main():
    print("=== CORREÇÃO E SINCRONIZAÇÃO DE VENDAS ===")
    
    # Primeiro, corrigir UUIDs
    fix_vendas_sem_uuid()
    
    # Depois, sincronizar
    print("\n=== SINCRONIZANDO VENDAS ===")
    try:
        repo = VendaRepository()
        resultado = await repo.sincronizar_mudancas()
        
        print(f"\n=== RESULTADO DA SINCRONIZAÇÃO ===")
        print(f"Status: {resultado.get('status', 'desconhecido')}")
        print(f"Vendas sincronizadas: {resultado.get('vendas_sincronizadas', 0)}")
        print(f"Mudanças pendentes: {resultado.get('mudancas_pendentes', 0)}")
        
        if resultado.get('status') == 'success':
            print("✅ Sincronização concluída com sucesso!")
        else:
            print("❌ Erro na sincronização")
            
    except Exception as e:
        print(f"❌ Erro durante sincronização: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
