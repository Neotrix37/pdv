#!/usr/bin/env python3
"""
Script para sincronizar vendas manualmente do SQLite local para o backend.
Execute: python sync_vendas_manual.py
"""

import asyncio
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repositories.venda_repository import VendaRepository

async def main():
    print("=== SINCRONIZAÇÃO MANUAL DE VENDAS ===")
    
    try:
        repo = VendaRepository()
        print("Iniciando sincronização de vendas...")
        
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
