#!/usr/bin/env python3
"""
Script para sincronizar produtos primeiro, depois vendas.
"""

import asyncio
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repositories.produto_repository import ProdutoRepository
from repositories.venda_repository import VendaRepository

async def main():
    print("=== SINCRONIZAÇÃO PRODUTOS → VENDAS ===")
    
    try:
        # 1. Sincronizar produtos primeiro
        print("\n1. SINCRONIZANDO PRODUTOS...")
        produto_repo = ProdutoRepository()
        resultado_produtos = await produto_repo.sincronizar_mudancas()
        
        print(f"Produtos - Status: {resultado_produtos.get('status', 'desconhecido')}")
        print(f"Produtos sincronizados: {resultado_produtos.get('produtos_sincronizados', 0)}")
        
        # 2. Depois sincronizar vendas
        print("\n2. SINCRONIZANDO VENDAS...")
        venda_repo = VendaRepository()
        resultado_vendas = await venda_repo.sincronizar_mudancas()
        
        print(f"Vendas - Status: {resultado_vendas.get('status', 'desconhecido')}")
        print(f"Vendas sincronizadas: {resultado_vendas.get('vendas_sincronizadas', 0)}")
        
        print(f"\n=== RESULTADO FINAL ===")
        if (resultado_produtos.get('status') == 'success' and 
            resultado_vendas.get('status') == 'success'):
            print("✅ Sincronização completa bem-sucedida!")
        else:
            print("❌ Alguns problemas na sincronização")
            
    except Exception as e:
        print(f"❌ Erro durante sincronização: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
