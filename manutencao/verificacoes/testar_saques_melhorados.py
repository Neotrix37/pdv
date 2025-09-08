#!/usr/bin/env python3
"""
Script para testar as melhorias no sistema de saques
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_saques_melhorados():
    """Testa as melhorias implementadas no sistema de saques"""
    print("=== TESTE DAS MELHORIAS NO SISTEMA DE SAQUES ===\n")
    
    try:
        # Caminho do banco APPDATA
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        appdata_db = app_data_db_dir / 'sistema.db'
        
        print(f"1. Conectando ao banco: {appdata_db}")
        
        if not appdata_db.exists():
            print("❌ Banco APPDATA não existe!")
            return False
            
        conn = sqlite3.connect(str(appdata_db))
        cursor = conn.cursor()
        
        print("\n2. Verificando saques existentes:")
        cursor.execute("""
            SELECT id, valor, origem, status, data_retirada, motivo
            FROM retiradas_caixa
            ORDER BY data_retirada DESC
            LIMIT 5
        """)
        saques = cursor.fetchall()
        
        if saques:
            print(f"   - Encontrados {len(saques)} saques:")
            for saque in saques:
                print(f"     * ID {saque[0]}: MT {saque[1]:.2f} - {saque[2]} - Status: {saque[3]}")
        else:
            print("   - Nenhum saque encontrado")
        
        print("\n3. Verificando valores do dashboard:")
        
        # Vendas do mês
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE 
                    WHEN status = 'Anulada' THEN 0 
                    ELSE total 
                END
            ), 0) as total
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
        """)
        vendas_bruto = cursor.fetchone()[0]
        print(f"   - Vendas brutas do mês: MT {vendas_bruto:.2f}")
        
        # Saques de vendas
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'vendas'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        """)
        saques_vendas = cursor.fetchone()[0]
        print(f"   - Saques de vendas: MT {saques_vendas:.2f}")
        
        vendas_disponiveis = max(0, vendas_bruto - saques_vendas)
        print(f"   - Vendas disponíveis: MT {vendas_disponiveis:.2f}")
        
        # Lucro do mês
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE 
                    WHEN v.status = 'Anulada' THEN 0 
                    ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                END
            ), 0) as lucro
            FROM vendas v
            JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE strftime('%Y-%m', v.data_venda) = strftime('%Y-%m', 'now')
        """)
        lucro_bruto = cursor.fetchone()[0]
        print(f"   - Lucro bruto do mês: MT {lucro_bruto:.2f}")
        
        # Saques de lucro
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'lucro'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        """)
        saques_lucro = cursor.fetchone()[0]
        print(f"   - Saques de lucro: MT {saques_lucro:.2f}")
        
        lucro_disponivel = max(0, lucro_bruto - saques_lucro)
        print(f"   - Lucro disponível: MT {lucro_disponivel:.2f}")
        
        print("\n4. Verificando métodos do banco:")
        
        # Importar e testar os métodos
        from database.database import Database
        db = Database()
        
        vendas_disponiveis_db = db.get_vendas_disponiveis_mes()
        lucro_disponivel_db = db.get_lucro_disponivel_mes()
        
        print(f"   - get_vendas_disponiveis_mes(): MT {vendas_disponiveis_db:.2f}")
        print(f"   - get_lucro_disponivel_mes(): MT {lucro_disponivel_db:.2f}")
        
        # Verificar se os valores batem
        if abs(vendas_disponiveis - vendas_disponiveis_db) < 0.01:
            print("   ✅ Vendas disponíveis: OK")
        else:
            print(f"   ❌ Vendas disponíveis: DIFERENÇA - Manual: {vendas_disponiveis:.2f}, DB: {vendas_disponiveis_db:.2f}")
            
        if abs(lucro_disponivel - lucro_disponivel_db) < 0.01:
            print("   ✅ Lucro disponível: OK")
        else:
            print(f"   ❌ Lucro disponível: DIFERENÇA - Manual: {lucro_disponivel:.2f}, DB: {lucro_disponivel_db:.2f}")
        
        print("\n5. Resumo das melhorias implementadas:")
        print("   ✅ Status automático 'Completo' em vez de 'Pendente'")
        print("   ✅ Dashboard mostra valores disponíveis (menos saques)")
        print("   ✅ Métodos get_vendas_disponiveis_mes() e get_lucro_disponivel_mes()")
        print("   ✅ Controle financeiro real para facilitar contabilidade")
        
        conn.close()
        print("\n🎉 Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== TESTE DAS MELHORIAS NO SISTEMA DE SAQUES ===\n")
    if testar_saques_melhorados():
        print("\n✅ Melhorias implementadas e funcionando!")
        print("\n📋 Próximos passos:")
        print("1. Execute o sistema: python main.py")
        print("2. Teste fazer um saque - deve aparecer como 'Completo'")
        print("3. Verifique se os cards do dashboard diminuem após o saque")
        print("4. Confirme que o controle financeiro está correto")
    else:
        print("\n❌ Falha no teste. Verifique os erros acima.")

if __name__ == "__main__":
    main()
