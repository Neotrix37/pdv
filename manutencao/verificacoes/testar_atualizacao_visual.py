#!/usr/bin/env python3
"""
Script para testar a atualização visual dos cards do dashboard
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_atualizacao_visual():
    """Testa a atualização visual dos cards"""
    print("=== TESTE DE ATUALIZAÇÃO VISUAL ===\n")
    
    try:
        from database.database import Database
        import sqlite3
        
        print("1. Conectando ao banco...")
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        appdata_db = app_data_db_dir / 'sistema.db'
        
        if not appdata_db.exists():
            print("❌ Banco não existe!")
            return False
            
        conn = sqlite3.connect(str(appdata_db))
        cursor = conn.cursor()
        print("   ✅ Conectado ao banco")
        
        print("\n2. Verificando valores atuais...")
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) as total_vendas
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
            AND status != 'Anulada'
        """)
        vendas_bruto = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'vendas'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        """)
        saques_vendas = cursor.fetchone()[0]
        
        vendas_disponiveis = max(0, vendas_bruto - saques_vendas)
        
        print(f"   - Vendas brutas: MT {vendas_bruto:.2f}")
        print(f"   - Saques de vendas: MT {saques_vendas:.2f}")
        print(f"   - Vendas disponíveis: MT {vendas_disponiveis:.2f}")
        
        print("\n3. Simulando novo saque de MT 2.000,00...")
        cursor.execute("""
            INSERT INTO retiradas_caixa 
            (usuario_id, valor, origem, motivo, status, data_retirada)
            VALUES (1, 2000.0, 'vendas', 'Teste visual', 'Completo', datetime('now'))
        """)
        conn.commit()
        print("   ✅ Saque inserido")
        
        print("\n4. Verificando valores após saque...")
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'vendas'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        """)
        saques_vendas_novo = cursor.fetchone()[0]
        
        vendas_disponiveis_novo = max(0, vendas_bruto - saques_vendas_novo)
        
        print(f"   - Vendas brutas: MT {vendas_bruto:.2f}")
        print(f"   - Saques de vendas: MT {saques_vendas_novo:.2f}")
        print(f"   - Vendas disponíveis: MT {vendas_disponiveis_novo:.2f}")
        
        diferenca = vendas_disponiveis - vendas_disponiveis_novo
        print(f"   - Diferença: MT {diferenca:.2f}")
        
        if diferenca == 2000.0:
            print("   ✅ Cálculo correto!")
        else:
            print(f"   ❌ Cálculo incorreto! Esperado: 2000.00, Obtido: {diferenca:.2f}")
        
        print("\n5. Testando métodos do banco...")
        db = Database()
        vendas_disponiveis_db = db.get_vendas_disponiveis_mes()
        print(f"   - get_vendas_disponiveis_mes(): MT {vendas_disponiveis_db:.2f}")
        
        if abs(vendas_disponiveis_novo - vendas_disponiveis_db) < 0.01:
            print("   ✅ Método do banco correto!")
        else:
            print(f"   ❌ Método do banco incorreto! Esperado: {vendas_disponiveis_novo:.2f}, Obtido: {vendas_disponiveis_db:.2f}")
        
        print("\n6. Limpando dados de teste...")
        cursor.execute("DELETE FROM retiradas_caixa WHERE motivo = 'Teste visual'")
        conn.commit()
        print("   ✅ Dados removidos")
        
        conn.close()
        print("\n🎉 Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== TESTE DE ATUALIZAÇÃO VISUAL ===\n")
    if testar_atualizacao_visual():
        print("\n✅ Cálculos funcionando corretamente!")
        print("\n📋 Se os cards não atualizam visualmente:")
        print("1. Execute o sistema: python main.py")
        print("2. Faça um saque e verifique os logs")
        print("3. Navegue de volta ao dashboard")
        print("4. Os valores devem estar atualizados")
    else:
        print("\n❌ Problemas encontrados. Verifique os erros acima.")

if __name__ == "__main__":
    main()
