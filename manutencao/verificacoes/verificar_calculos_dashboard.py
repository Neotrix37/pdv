#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar exatamente como o dashboard está calculando os valores
"""

import sqlite3
import os
from datetime import datetime

def verificar_calculos():
    """Verifica os cálculos exatos do dashboard"""
    
    # Usar o banco atual (após restauração)
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from database.database import Database
    
    print("VERIFICACAO DOS CALCULOS DO DASHBOARD")
    print("=" * 50)
    print(f"Data atual do sistema: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mes atual para calculo: {datetime.now().strftime('%Y-%m')}")
    
    try:
        db = Database()
        
        # 1. Verificar vendas brutas do mês atual
        print("\n1. VENDAS BRUTAS DO MES ATUAL:")
        query_vendas = """
            SELECT 
                COUNT(*) as total_registros,
                COALESCE(SUM(
                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE total 
                    END
                ), 0) as total_vendas,
                COALESCE(SUM(
                    CASE 
                        WHEN status = 'Anulada' THEN total
                        ELSE 0 
                    END
                ), 0) as total_anuladas,
                COUNT(CASE WHEN status = 'Anulada' THEN 1 END) as qtd_anuladas
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
        """
        
        result = db.fetchone(query_vendas)
        print(f"  Total de registros no mes: {result['total_registros']}")
        print(f"  Vendas validas: MT {result['total_vendas']:.2f}")
        print(f"  Vendas anuladas: MT {result['total_anuladas']:.2f}")
        print(f"  Quantidade anuladas: {result['qtd_anuladas']}")
        
        # 2. Verificar saques do mês
        print("\n2. SAQUES DE VENDAS DO MES:")
        query_saques = """
            SELECT 
                COUNT(*) as total_saques,
                COALESCE(SUM(valor), 0) as total_valor
            FROM retiradas_caixa
            WHERE origem = 'vendas'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        """
        
        result_saques = db.fetchone(query_saques)
        print(f"  Total de saques: {result_saques['total_saques']}")
        print(f"  Valor total dos saques: MT {result_saques['total_valor']:.2f}")
        
        # 3. Calcular vendas disponíveis (como no dashboard)
        vendas_brutas = result['total_vendas']
        saques_vendas = result_saques['total_valor']
        vendas_disponiveis = max(0, vendas_brutas - saques_vendas)
        
        print(f"\n3. CALCULO FINAL:")
        print(f"  Vendas brutas: MT {vendas_brutas:.2f}")
        print(f"  Menos saques: MT {saques_vendas:.2f}")
        print(f"  = Vendas disponiveis: MT {vendas_disponiveis:.2f}")
        
        # 4. Comparar com a função do sistema
        print(f"\n4. COMPARACAO COM FUNCAO DO SISTEMA:")
        vendas_sistema = db.get_vendas_disponiveis_mes()
        print(f"  Funcao get_vendas_disponiveis_mes(): MT {vendas_sistema:.2f}")
        
        if abs(vendas_disponiveis - vendas_sistema) < 0.01:
            print("  ✓ Calculos coincidem!")
        else:
            print("  ✗ Calculos NAO coincidem!")
        
        # 5. Verificar todas as vendas de agosto detalhadamente
        print(f"\n5. DETALHES DAS VENDAS DE AGOSTO 2025:")
        query_detalhes = """
            SELECT 
                DATE(data_venda) as data,
                COUNT(*) as qtd,
                COALESCE(SUM(total), 0) as valor,
                status
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = '2025-08'
            GROUP BY DATE(data_venda), status
            ORDER BY data DESC, status
        """
        
        vendas_detalhes = db.fetchall(query_detalhes)
        for venda in vendas_detalhes:
            status = venda['status'] or 'Normal'
            print(f"  {venda['data']}: {venda['qtd']} vendas - MT {venda['valor']:.2f} ({status})")
        
        # 6. Verificar se há problemas na tabela retiradas_caixa
        print(f"\n6. VERIFICACAO DA TABELA RETIRADAS_CAIXA:")
        try:
            cursor = db.conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM retiradas_caixa")
            total_retiradas = cursor.fetchone()[0]
            print(f"  Total de registros em retiradas_caixa: {total_retiradas}")
            
            if total_retiradas > 0:
                cursor.execute("""
                    SELECT origem, status, COUNT(*) as qtd, SUM(valor) as total
                    FROM retiradas_caixa 
                    GROUP BY origem, status
                """)
                retiradas = cursor.fetchall()
                for ret in retiradas:
                    print(f"  {ret[0]} ({ret[1]}): {ret[2]} registros - MT {ret[3]:.2f}")
        except Exception as e:
            print(f"  Erro ao verificar retiradas_caixa: {e}")
        
        print(f"\n" + "=" * 50)
        print("CONCLUSAO:")
        if vendas_disponiveis == 100.00:
            print("O valor MT 100.00 esta correto baseado nos calculos:")
            print("- Vendas brutas do mes menos saques realizados")
            print("- Isso explica por que nao mostra os MT 71.273,00 totais")
        else:
            print(f"Valor calculado: MT {vendas_disponiveis:.2f}")
            print("Verifique se ha saques ou vendas anuladas impactando o calculo")
        
    except Exception as e:
        print(f"Erro durante verificacao: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_calculos()
