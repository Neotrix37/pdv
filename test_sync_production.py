#!/usr/bin/env python3
"""
Script para testar sincronização com o backend em produção
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Adicionar o diretório do PDV3 ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sync_manager import sync_all_tables

async def test_sync():
    """Testa a sincronização com o backend em produção."""
    print("🚀 Testando sincronização com backend em produção")
    print("URL:", "https://prototipo-production-c729.up.railway.app/api")
    print("-" * 60)
    
    try:
        # Executar sincronização
        result = await sync_all_tables()
        
        # Exibir resultados
        print("\n📊 RESULTADO DA SINCRONIZAÇÃO:")
        print("=" * 60)
        
        summary = result.get('summary', {})
        print(f"Status: {summary.get('status', 'unknown')}")
        print(f"Duração: {summary.get('duration_seconds', 0):.2f} segundos")
        print(f"Enviados: {summary.get('total_uploaded', 0)} registros")
        print(f"Recebidos: {summary.get('total_downloaded', 0)} registros")
        print(f"Conflitos: {summary.get('total_conflicts', 0)} registros")
        print(f"Mensagem: {summary.get('message', '')}")
        
        # Detalhes por tabela
        print("\n📋 DETALHES POR TABELA:")
        print("-" * 60)
        
        tables = result.get('tables', {})
        for table_name, table_result in tables.items():
            status_icon = "✅" if table_result['status'] == 'success' else "⚠️" if table_result['status'] == 'partial' else "❌"
            print(f"{status_icon} {table_name}:")
            print(f"   Enviados: {table_result['uploaded']}")
            print(f"   Recebidos: {table_result['downloaded']}")
            print(f"   Conflitos: {table_result['conflicts']}")
            if table_result['message']:
                print(f"   Mensagem: {table_result['message']}")
            print()
        
        # Salvar resultado em arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"sync_test_result_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultado salvo em: {result_file}")
        
        # Status final
        if summary.get('status') == 'success':
            print("\n🎉 SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        elif summary.get('status') == 'partial':
            print("\n⚠️ SINCRONIZAÇÃO CONCLUÍDA COM AVISOS")
        else:
            print("\n❌ FALHA NA SINCRONIZAÇÃO")
            
        return result
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Função principal."""
    print("PDV3 - Teste de Sincronização com Backend em Produção")
    print("=" * 60)
    
    # Executar teste
    result = asyncio.run(test_sync())
    
    # Aguardar input do usuário
    input("\nPressione Enter para finalizar...")
    
    return result

if __name__ == "__main__":
    main()
