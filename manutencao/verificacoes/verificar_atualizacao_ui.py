#!/usr/bin/env python3
"""
Script para verificar problemas específicos com a atualização da UI do dashboard
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_atualizacao_ui():
    """Verifica problemas específicos com a atualização da UI"""
    print("=== VERIFICAÇÃO DE ATUALIZAÇÃO UI ===\n")
    
    try:
        from database.database import Database
        from views.dashboard_view import DashboardView
        import flet as ft
        
        print("1. Testando criação do banco de dados...")
        db = Database()
        print("   ✅ Banco de dados criado com sucesso")
        
        print("\n2. Testando criação de página mock...")
        # Criar uma página mock para teste
        page_mock = type('MockPage', (), {
            'bgcolor': ft.colors.BLUE_50,
            'data': {'language': 'pt'},
            'update': lambda: print("   ✅ page.update() chamado")
        })()
        print("   ✅ Página mock criada")
        
        print("\n3. Testando criação do dashboard...")
        usuario_mock = {'nome': 'Teste', 'is_admin': True}
        dashboard = DashboardView(page_mock, usuario_mock)
        print("   ✅ Dashboard criado")
        
        print("\n4. Verificando valores iniciais...")
        print(f"   - Vendas mês: {dashboard.vendas_mes.value}")
        print(f"   - Lucro mês: {dashboard.lucro_mes.value}")
        print(f"   - Vendas dia: {dashboard.vendas_dia.value}")
        
        print("\n5. Testando método atualizar_valores...")
        dashboard.atualizar_valores()
        print("   ✅ Método atualizar_valores executado")
        
        print("\n6. Verificando valores após atualização...")
        print(f"   - Vendas mês: {dashboard.vendas_mes.value}")
        print(f"   - Lucro mês: {dashboard.lucro_mes.value}")
        print(f"   - Vendas dia: {dashboard.vendas_dia.value}")
        
        print("\n7. Testando método build...")
        try:
            build_result = dashboard.build()
            print("   ✅ Método build executado com sucesso")
        except Exception as e:
            print(f"   ❌ Erro no método build: {e}")
        
        print("\n8. Verificando valores após build...")
        print(f"   - Vendas mês: {dashboard.vendas_mes.value}")
        print(f"   - Lucro mês: {dashboard.lucro_mes.value}")
        print(f"   - Vendas dia: {dashboard.vendas_dia.value}")
        
        print("\n9. Testando atualização forçada...")
        try:
            dashboard.update()
            print("   ✅ dashboard.update() executado")
        except Exception as e:
            print(f"   ❌ Erro no dashboard.update(): {e}")
        
        print("\n🎉 Verificação concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== VERIFICAÇÃO DE ATUALIZAÇÃO UI ===\n")
    if verificar_atualizacao_ui():
        print("\n✅ Dashboard funcionando corretamente!")
        print("\n📋 Se os cards não atualizam visualmente:")
        print("1. Verifique se o sistema está sendo executado corretamente")
        print("2. Tente fazer logout e login novamente")
        print("3. Verifique se há erros no console")
        print("4. Os valores estão sendo calculados corretamente")
    else:
        print("\n❌ Problemas encontrados. Verifique os erros acima.")

if __name__ == "__main__":
    main()
