#!/usr/bin/env python3
"""
Script para verificar saques e testar a funcionalidade
"""

import sys
import os
import sqlite3

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database

def verificar_saques():
    """Verifica os saques no banco de dados"""
    print("=== VERIFICAÇÃO DE SAQUES ===\n")
    
    try:
        db = Database()
        cursor = db.conn.cursor()
        
        # 1. Verificar se a tabela retiradas_caixa existe
        print("1. Verificando tabela retiradas_caixa...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='retiradas_caixa'
        """)
        
        if not cursor.fetchone():
            print("❌ ERRO: Tabela retiradas_caixa não existe!")
            return False
        
        print("✅ Tabela retiradas_caixa existe")
        
        # 2. Verificar estrutura da tabela
        print("\n2. Estrutura da tabela retiradas_caixa:")
        cursor.execute("PRAGMA table_info(retiradas_caixa)")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 3. Contar total de saques
        print("\n3. Estatísticas de saques:")
        cursor.execute("SELECT COUNT(*) as total FROM retiradas_caixa")
        total_saques = cursor.fetchone()[0]
        print(f"  - Total de saques: {total_saques}")
        
        # 4. Contar saques por status
        cursor.execute("""
            SELECT status, COUNT(*) as quantidade, SUM(valor) as valor_total
            FROM retiradas_caixa 
            GROUP BY status
        """)
        
        print("\n4. Saques por status:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} saques (R$ {row[2]:.2f})")
        
        # 5. Contar saques por origem
        cursor.execute("""
            SELECT origem, COUNT(*) as quantidade, SUM(valor) as valor_total
            FROM retiradas_caixa 
            GROUP BY origem
        """)
        
        print("\n5. Saques por origem:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} saques (R$ {row[2]:.2f})")
        
        # 6. Mostrar saques de hoje
        print("\n6. Saques de hoje:")
        cursor.execute("""
            SELECT 
                id,
                usuario_id,
                valor,
                motivo,
                origem,
                status,
                data_retirada,
                created_at
            FROM retiradas_caixa 
            WHERE DATE(data_retirada) = DATE('now')
            ORDER BY data_retirada DESC
        """)
        
        saques_hoje = cursor.fetchall()
        if saques_hoje:
            for saque in saques_hoje:
                print(f"  - ID {saque[0]}: R$ {saque[2]:.2f} ({saque[4]}) - {saque[3]} - Status: {saque[5]}")
                print(f"    Data: {saque[6]} | Usuário ID: {saque[1]}")
        else:
            print("  - Nenhum saque hoje")
        
        # 7. Mostrar últimos 5 saques
        print("\n7. Últimos 5 saques:")
        cursor.execute("""
            SELECT 
                id,
                usuario_id,
                valor,
                motivo,
                origem,
                status,
                data_retirada
            FROM retiradas_caixa 
            ORDER BY data_retirada DESC
            LIMIT 5
        """)
        
        ultimos_saques = cursor.fetchall()
        for saque in ultimos_saques:
            print(f"  - ID {saque[0]}: R$ {saque[2]:.2f} ({saque[4]}) - {saque[3]} - Status: {saque[5]}")
            print(f"    Data: {saque[6]} | Usuário ID: {saque[1]}")
        
        # 8. Verificar usuários que fizeram saques
        print("\n8. Usuários que fizeram saques:")
        cursor.execute("""
            SELECT 
                u.nome,
                COUNT(rc.id) as total_saques,
                SUM(rc.valor) as valor_total
            FROM retiradas_caixa rc
            JOIN usuarios u ON rc.usuario_id = u.id
            GROUP BY u.id, u.nome
            ORDER BY valor_total DESC
        """)
        
        usuarios_saques = cursor.fetchall()
        for usuario in usuarios_saques:
            print(f"  - {usuario[0]}: {usuario[1]} saques (R$ {usuario[2]:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar saques: {e}")
        return False

def testar_calculo_saldo():
    """Testa o cálculo de saldo disponível"""
    print("\n=== TESTE DE CÁLCULO DE SALDO ===\n")
    
    try:
        db = Database()
        cursor = db.conn.cursor()
        
        # Calcular saldo de vendas
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) as total_vendas
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
            AND status != 'Anulada'
        """)
        total_vendas = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'vendas'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
        """)
        total_saques_vendas = cursor.fetchone()[0] or 0
        
        saldo_vendas = total_vendas - total_saques_vendas
        
        print(f"1. Saldo de Vendas:")
        print(f"   - Total vendas do mês: R$ {total_vendas:.2f}")
        print(f"   - Total saques de vendas: R$ {total_saques_vendas:.2f}")
        print(f"   - Saldo disponível: R$ {saldo_vendas:.2f}")
        
        # Calcular saldo de lucro
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN v.status = 'Anulada' THEN 0 
                     ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                END
            ), 0) as lucro_bruto
            FROM vendas v
            JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE strftime('%Y-%m', v.data_venda) = strftime('%Y-%m', 'now')
        """)
        lucro_bruto = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'lucro'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
        """)
        total_saques_lucro = cursor.fetchone()[0] or 0
        
        saldo_lucro = lucro_bruto - total_saques_lucro
        
        print(f"\n2. Saldo de Lucro:")
        print(f"   - Lucro bruto do mês: R$ {lucro_bruto:.2f}")
        print(f"   - Total saques de lucro: R$ {total_saques_lucro:.2f}")
        print(f"   - Saldo disponível: R$ {saldo_lucro:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar cálculo de saldo: {e}")
        return False

def main():
    print("=== VERIFICAÇÃO E TESTE DE SAQUES ===\n")
    
    # 1. Verificar saques
    if not verificar_saques():
        print("❌ Falha na verificação de saques!")
        return
    
    # 2. Testar cálculo de saldo
    if not testar_calculo_saldo():
        print("❌ Falha no teste de cálculo de saldo!")
        return
    
    print("\n🎉 Verificação concluída com sucesso!")

if __name__ == "__main__":
    main()
