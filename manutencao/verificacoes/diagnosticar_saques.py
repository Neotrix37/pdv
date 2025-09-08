#!/usr/bin/env python3
"""
Script para diagnosticar problemas com a consulta de saques
"""
import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def diagnosticar_saques():
    """Diagnostica problemas com a consulta de saques"""
    print("=== DIAGNÓSTICO DE SAQUES ===\n")
    
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
        
        print("\n2. Verificando tabela retiradas_caixa:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='retiradas_caixa'")
        if cursor.fetchone():
            print("   ✅ Tabela retiradas_caixa existe")
        else:
            print("   ❌ Tabela retiradas_caixa não existe!")
            return False
        
        print("\n3. Verificando estrutura da tabela:")
        cursor.execute("PRAGMA table_info(retiradas_caixa)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        print("\n4. Verificando todos os saques:")
        cursor.execute("""
            SELECT id, valor, origem, status, data_retirada, motivo
            FROM retiradas_caixa
            ORDER BY data_retirada DESC
        """)
        saques = cursor.fetchall()
        print(f"   - Total de saques: {len(saques)}")
        for saque in saques:
            print(f"     * ID {saque[0]}: MT {saque[1]:.2f} - {saque[2]} - Status: {saque[3]} - {saque[4]}")
        
        print("\n5. Verificando saques do mês atual:")
        cursor.execute("""
            SELECT id, valor, origem, status, data_retirada, motivo
            FROM retiradas_caixa
            WHERE strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            ORDER BY data_retirada DESC
        """)
        saques_mes = cursor.fetchall()
        print(f"   - Saques do mês atual: {len(saques_mes)}")
        for saque in saques_mes:
            print(f"     * ID {saque[0]}: MT {saque[1]:.2f} - {saque[2]} - Status: {saque[3]} - {saque[4]}")
        
        print("\n6. Verificando saques de vendas do mês:")
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'vendas'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        """)
        saques_vendas = cursor.fetchone()[0]
        print(f"   - Saques de vendas do mês: MT {saques_vendas:.2f}")
        
        print("\n7. Verificando saques de lucro do mês:")
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques
            FROM retiradas_caixa
            WHERE origem = 'lucro'
            AND strftime('%Y-%m', data_retirada) = strftime('%Y-%m', 'now')
            AND status = 'Completo'
        """)
        saques_lucro = cursor.fetchone()[0]
        print(f"   - Saques de lucro do mês: MT {saques_lucro:.2f}")
        
        print("\n8. Verificando saques de hoje:")
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0) as total_saques, COUNT(*) as qtd_saques
            FROM retiradas_caixa
            WHERE DATE(data_retirada) = DATE('now')
            AND status = 'Completo'
        """)
        saques_hoje = cursor.fetchone()
        print(f"   - Saques de hoje: MT {saques_hoje[0]:.2f} ({saques_hoje[1]} saques)")
        
        print("\n9. Testando métodos do banco:")
        from database.database import Database
        db = Database()
        
        vendas_disponiveis = db.get_vendas_disponiveis_mes()
        lucro_disponivel = db.get_lucro_disponivel_mes()
        
        print(f"   - get_vendas_disponiveis_mes(): MT {vendas_disponiveis:.2f}")
        print(f"   - get_lucro_disponivel_mes(): MT {lucro_disponivel:.2f}")
        
        conn.close()
        print("\n🎉 Diagnóstico concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== DIAGNÓSTICO DE SAQUES ===\n")
    if diagnosticar_saques():
        print("\n✅ Diagnóstico concluído!")
        print("\n📋 Se houver problemas:")
        print("1. Verifique se a tabela retiradas_caixa existe")
        print("2. Verifique se os saques têm status 'Completo'")
        print("3. Verifique se as datas estão corretas")
    else:
        print("\n❌ Problemas encontrados. Verifique os erros acima.")

if __name__ == "__main__":
    main()
