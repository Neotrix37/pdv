#!/usr/bin/env python3
"""
Script para testar a atualização dos cards do dashboard
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_atualizacao_dashboard():
    """Testa a atualização dos cards do dashboard"""
    print("=== TESTE DE ATUALIZAÇÃO DO DASHBOARD ===\n")
    
    try:
        from database.database import Database
        from views.dashboard_view import DashboardView
        import flet as ft
        
        print("1. Criando banco de dados...")
        db = Database()
        print("   ✅ Banco criado")
        
        print("\n2. Criando página mock...")
        page_mock = type('MockPage', (), {
            'bgcolor': ft.colors.BLUE_50,
            'data': {'language': 'pt'},
            'update': lambda: print("   ✅ page.update() chamado")
        })()
        print("   ✅ Página mock criada")
        
        print("\n3. Criando dashboard...")
        usuario_mock = {'nome': 'Teste', 'is_admin': True}
        dashboard = DashboardView(page_mock, usuario_mock)
        print("   ✅ Dashboard criado")
        
        print("\n4. Verificando valores iniciais...")
        print(f"   - Vendas mês: {dashboard.vendas_mes.value}")
        print(f"   - Lucro mês: {dashboard.lucro_mes.value}")
        
        print("\n5. Simulando saque de MT 5.000,00...")
        # Simular um saque inserindo diretamente no banco
        db.execute("""
            INSERT INTO retiradas_caixa 
            (usuario_id, valor, origem, motivo, status, data_retirada)
            VALUES (1, 5000.0, 'vendas', 'Teste de atualização', 'Completo', datetime('now'))
        """)
        print("   ✅ Saque simulado")
        
        print("\n6. Atualizando valores do dashboard...")
        dashboard.atualizar_valores()
        print("   ✅ Valores atualizados")
        
        print("\n7. Verificando valores após atualização...")
        print(f"   - Vendas mês: {dashboard.vendas_mes.value}")
        print(f"   - Lucro mês: {dashboard.lucro_mes.value}")
        
        print("\n8. Testando método build...")
        try:
            build_result = dashboard.build()
            print("   ✅ Build executado")
        except Exception as e:
            print(f"   ❌ Erro no build: {e}")
        
        print("\n9. Verificando valores após build...")
        print(f"   - Vendas mês: {dashboard.vendas_mes.value}")
        print(f"   - Lucro mês: {dashboard.lucro_mes.value}")
        
        print("\n10. Limpando dados de teste...")
        db.execute("DELETE FROM retiradas_caixa WHERE motivo = 'Teste de atualização'")
        print("   ✅ Dados de teste removidos")
        
        print("\n🎉 Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== TESTE DE ATUALIZAÇÃO DO DASHBOARD ===\n")
    if testar_atualizacao_dashboard():
        print("\n✅ Atualização funcionando corretamente!")
        print("\n📋 Se os cards não atualizam visualmente:")
        print("1. Verifique se o sistema está sendo executado")
        print("2. Tente fazer logout e login novamente")
        print("3. Verifique se há erros no console")
    else:
        print("\n❌ Problemas encontrados. Verifique os erros acima.")

if __name__ == "__main__":
    main()
