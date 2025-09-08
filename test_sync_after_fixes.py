#!/usr/bin/env python3
"""
Script para testar sincronização após correções dos UUIDs
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repositories.produto_repository import ProdutoRepository
from repositories.usuario_repository import UsuarioRepository
from repositories.cliente_repository import ClienteRepository
from repositories.venda_repository import VendaRepository

async def test_sync_after_fixes():
    """Testar sincronização após correções"""
    print("🔄 TESTANDO SINCRONIZAÇÃO APÓS CORREÇÕES")
    print("=" * 60)
    
    # Inicializar repositórios
    produto_repo = ProdutoRepository()
    usuario_repo = UsuarioRepository()
    cliente_repo = ClienteRepository()
    venda_repo = VendaRepository()
    
    try:
        print("\n📦 TESTANDO PRODUTOS:")
        produtos_enviados = await produto_repo.bulk_sync_produtos_antigos()
        print(f"✅ Produtos enviados: {produtos_enviados}")
        
        print("\n👥 TESTANDO USUÁRIOS:")
        usuarios_enviados = await usuario_repo.bulk_sync_usuarios_antigos()
        print(f"✅ Usuários enviados: {usuarios_enviados}")
        
        print("\n🏢 TESTANDO CLIENTES:")
        clientes_enviados = await cliente_repo.bulk_sync_clientes_antigos()
        print(f"✅ Clientes enviados: {clientes_enviados}")
        
        print("\n💰 TESTANDO VENDAS:")
        vendas_enviadas = await venda_repo.bulk_sync_vendas_antigas()
        print(f"✅ Vendas enviadas: {vendas_enviadas}")
        
        print("\n" + "=" * 60)
        print("✅ TESTE DE SINCRONIZAÇÃO CONCLUÍDO!")
        print(f"📊 RESUMO:")
        print(f"   - Produtos: {produtos_enviados}")
        print(f"   - Usuários: {usuarios_enviados}")
        print(f"   - Clientes: {clientes_enviados}")
        print(f"   - Vendas: {vendas_enviadas}")
        
        total = produtos_enviados + usuarios_enviados + clientes_enviados + vendas_enviadas
        print(f"   - TOTAL: {total} registros sincronizados")
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sync_after_fixes())
