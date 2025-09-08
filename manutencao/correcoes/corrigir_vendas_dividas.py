#!/usr/bin/env python3
"""
Script para corrigir vendas existentes que foram criadas a partir de dívidas quitadas.
Este script atualiza as vendas com origem 'divida_quitada' para incluir as informações
de valor original e desconto aplicado.
"""

import sqlite3
from pathlib import Path
import os

def corrigir_vendas_dividas():
    """Corrige vendas existentes que foram criadas a partir de dívidas quitadas"""
    
    # Caminho para o banco de dados
    db_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'database'
    db_path = db_dir / 'sistema.db'
    
    if not db_path.exists():
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("🔍 Buscando vendas com origem 'divida_quitada'...")
        
        # Buscar vendas que foram criadas a partir de dívidas quitadas
        vendas_dividas = cursor.execute("""
            SELECT v.id, v.total, v.origem
            FROM vendas v
            WHERE v.origem = 'divida_quitada'
            AND (v.valor_original_divida IS NULL OR v.valor_original_divida = 0)
        """).fetchall()
        
        print(f"📊 Encontradas {len(vendas_dividas)} vendas para corrigir")
        
        if not vendas_dividas:
            print("✅ Nenhuma venda precisa ser corrigida!")
            return True
        
        # Para cada venda, buscar a dívida correspondente
        for venda in vendas_dividas:
            venda_id = venda[0]
            venda_total = venda[1]
            
            print(f"\n🔄 Processando venda ID: {venda_id}")
            
            # Buscar a dívida que gerou esta venda
            # Como não temos uma relação direta, vamos buscar pela data mais próxima
            divida = cursor.execute("""
                SELECT d.id, d.valor_total, d.valor_original, d.desconto_aplicado, d.percentual_desconto
                FROM dividas d
                WHERE d.status = 'Quitado'
                AND d.valor_total = ?
                ORDER BY d.data_divida DESC
                LIMIT 1
            """, (venda_total,)).fetchone()
            
            if divida:
                divida_id = divida[0]
                valor_original = divida[2] or divida[1]  # Se valor_original for NULL, usar valor_total
                desconto_aplicado = divida[3] or 0
                
                print(f"   📋 Dívida encontrada: ID {divida_id}")
                print(f"   💰 Valor original: MT {valor_original:.2f}")
                print(f"   🎯 Desconto aplicado: MT {desconto_aplicado:.2f}")
                
                # Atualizar a venda com as informações da dívida
                cursor.execute("""
                    UPDATE vendas 
                    SET valor_original_divida = ?,
                        desconto_aplicado_divida = ?
                    WHERE id = ?
                """, (valor_original, desconto_aplicado, venda_id))
                
                print(f"   ✅ Venda atualizada com sucesso!")
            else:
                print(f"   ⚠️  Dívida correspondente não encontrada para venda {venda_id}")
        
        # Commit das alterações
        conn.commit()
        print(f"\n🎉 Processo concluído! {len(vendas_dividas)} vendas foram processadas.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a correção: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando correção de vendas de dívidas quitadas...")
    print("=" * 60)
    
    sucesso = corrigir_vendas_dividas()
    
    print("=" * 60)
    if sucesso:
        print("✅ Correção concluída com sucesso!")
    else:
        print("❌ Erro durante a correção!")
    
    input("\nPressione Enter para sair...") 