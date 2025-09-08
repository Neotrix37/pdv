#!/usr/bin/env python3
"""
Script para atualizar saques existentes para status 'Completo'
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def atualizar_saques_existentes():
    """Atualiza saques existentes para status 'Completo'"""
    print("=== ATUALIZAÇÃO DE SAQUES EXISTENTES ===\n")
    
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
        
        print("\n2. Verificando saques pendentes:")
        cursor.execute("""
            SELECT id, valor, origem, status, data_retirada, motivo
            FROM retiradas_caixa
            WHERE status = 'pendente'
            ORDER BY data_retirada DESC
        """)
        saques_pendentes = cursor.fetchall()
        
        if saques_pendentes:
            print(f"   - Encontrados {len(saques_pendentes)} saques pendentes:")
            for saque in saques_pendentes:
                print(f"     * ID {saque[0]}: MT {saque[1]:.2f} - {saque[2]} - {saque[4]}")
            
            print(f"\n3. Atualizando {len(saques_pendentes)} saques para 'Completo'...")
            
            cursor.execute("""
                UPDATE retiradas_caixa
                SET status = 'Completo', updated_at = CURRENT_TIMESTAMP
                WHERE status = 'pendente'
            """)
            
            conn.commit()
            print("   ✅ Saques atualizados com sucesso!")
            
            print("\n4. Verificando resultado:")
            cursor.execute("""
                SELECT id, valor, origem, status, data_retirada
                FROM retiradas_caixa
                ORDER BY data_retirada DESC
                LIMIT 5
            """)
            saques_atualizados = cursor.fetchall()
            
            for saque in saques_atualizados:
                print(f"     * ID {saque[0]}: MT {saque[1]:.2f} - {saque[2]} - Status: {saque[3]}")
                
        else:
            print("   - Nenhum saque pendente encontrado")
        
        print("\n5. Verificando valores do dashboard após atualização:")
        
        # Vendas disponíveis
        cursor.execute("""
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE total 
                    END
                ), 0) as vendas_bruto,
                COALESCE((
                    SELECT SUM(valor) 
                    FROM retiradas_caixa 
                    WHERE origem = 'vendas' 
                    AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
                    AND status = 'Completo'
                ), 0) as saques_vendas
            FROM vendas
            WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
        """)
        resultado_vendas = cursor.fetchone()
        vendas_bruto = resultado_vendas[0]
        saques_vendas = resultado_vendas[1]
        vendas_disponiveis = max(0, vendas_bruto - saques_vendas)
        
        print(f"   - Vendas brutas: MT {vendas_bruto:.2f}")
        print(f"   - Saques de vendas: MT {saques_vendas:.2f}")
        print(f"   - Vendas disponíveis: MT {vendas_disponiveis:.2f}")
        
        # Lucro disponível
        cursor.execute("""
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN v.status = 'Anulada' THEN 0 
                        ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                    END
                ), 0) as lucro_bruto,
                COALESCE((
                    SELECT SUM(valor) 
                    FROM retiradas_caixa 
                    WHERE origem = 'lucro' 
                    AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
                    AND status = 'Completo'
                ), 0) as saques_lucro
            FROM vendas v
            JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE strftime('%Y-%m', v.data_venda) = strftime('%Y-%m', 'now')
        """)
        resultado_lucro = cursor.fetchone()
        lucro_bruto = resultado_lucro[0]
        saques_lucro = resultado_lucro[1]
        lucro_disponivel = max(0, lucro_bruto - saques_lucro)
        
        print(f"   - Lucro bruto: MT {lucro_bruto:.2f}")
        print(f"   - Saques de lucro: MT {saques_lucro:.2f}")
        print(f"   - Lucro disponível: MT {lucro_disponivel:.2f}")
        
        conn.close()
        print("\n🎉 Atualização concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na atualização: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== ATUALIZAÇÃO DE SAQUES EXISTENTES ===\n")
    if atualizar_saques_existentes():
        print("\n✅ Saques atualizados com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Execute o sistema: python main.py")
        print("2. Verifique se os cards do dashboard mostram valores corretos")
        print("3. Teste fazer um novo saque - deve aparecer como 'Completo'")
        print("4. Confirme que os valores diminuem após cada saque")
    else:
        print("\n❌ Falha na atualização. Verifique os erros acima.")

if __name__ == "__main__":
    main()
