#!/usr/bin/env python3
"""
Script para diagnosticar por que cliente online não mostra vendas
"""
import sqlite3
import os
from datetime import datetime

def debug_vendas_database():
    """Diagnostica o banco de dados de vendas"""
    
    # Possíveis locais do banco
    db_paths = [
        r"C:\Users\saide\AppData\Roaming\SistemaGestao\database\sistema.db",
        r"C:\Users\saide\sinc\pdv3\database\sistema.db",
        r"sistema.db",
        r"database\sistema.db"
    ]
    
    print("=== DIAGNÓSTICO VENDAS ONLINE ===\n")
    
    for db_path in db_paths:
        print(f"🔍 Verificando: {db_path}")
        
        if not os.path.exists(db_path):
            print("   ❌ Arquivo não encontrado\n")
            continue
            
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se tabela vendas existe
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='vendas'
                """)
                
                if not cursor.fetchone():
                    print("   ❌ Tabela 'vendas' não existe\n")
                    continue
                
                print("   ✅ Tabela 'vendas' encontrada")
                
                # Contar total de vendas
                cursor.execute("SELECT COUNT(*) FROM vendas")
                total_vendas = cursor.fetchone()[0]
                print(f"   📊 Total de vendas: {total_vendas}")
                
                # Vendas de hoje
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(total), 0) 
                    FROM vendas 
                    WHERE DATE(data_venda) = DATE('now')
                """)
                vendas_hoje = cursor.fetchone()
                print(f"   📅 Vendas hoje: {vendas_hoje[0]} vendas, MT {vendas_hoje[1]}")
                
                # Vendas do mês
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(total), 0) 
                    FROM vendas 
                    WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
                """)
                vendas_mes = cursor.fetchone()
                print(f"   📊 Vendas mês: {vendas_mes[0]} vendas, MT {vendas_mes[1]}")
                
                # Últimas 5 vendas
                cursor.execute("""
                    SELECT id, data_venda, total, status 
                    FROM vendas 
                    ORDER BY data_venda DESC 
                    LIMIT 5
                """)
                ultimas_vendas = cursor.fetchall()
                
                print("   📋 Últimas 5 vendas:")
                for venda in ultimas_vendas:
                    print(f"      ID {venda[0]}: {venda[1]} - MT {venda[2]} ({venda[3]})")
                
                print(f"   📍 Banco encontrado em: {os.path.abspath(db_path)}\n")
                
        except Exception as e:
            print(f"   ❌ Erro ao acessar banco: {e}\n")

def debug_environment():
    """Verifica variáveis de ambiente"""
    print("=== VARIÁVEIS DE AMBIENTE ===")
    
    env_vars = [
        'APPDATA',
        'USERPROFILE', 
        'DATABASE_URL',
        'DB_PATH'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NÃO DEFINIDA')
        print(f"{var}: {value}")
    
    print(f"\nDiretório atual: {os.getcwd()}")
    print(f"Data/hora atual: {datetime.now()}")

if __name__ == "__main__":
    debug_vendas_database()
    print()
    debug_environment()
