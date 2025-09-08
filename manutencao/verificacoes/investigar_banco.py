#!/usr/bin/env python3
"""
Script para investigar qual banco está sendo usado e comparar valores
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database

def verificar_caminho_banco():
    """Verifica qual banco está sendo usado"""
    print("=== VERIFICAÇÃO DE CAMINHO DO BANCO ===\n")
    
    try:
        db = Database()
        
        print(f"1. Caminho do banco atual: {db.db_path}")
        print(f"2. Caminho absoluto: {db.db_path.absolute()}")
        print(f"3. Banco existe: {db.db_path.exists()}")
        
        if db.db_path.exists():
            print(f"4. Tamanho do arquivo: {db.db_path.stat().st_size} bytes")
            print(f"5. Data de modificação: {db.db_path.stat().st_mtime}")
        
        return str(db.db_path.absolute())
        
    except Exception as e:
        print(f"❌ Erro ao verificar caminho: {e}")
        return None

def verificar_bancos_possiveis():
    """Verifica todos os possíveis bancos"""
    print("\n=== VERIFICAÇÃO DE TODOS OS BANCOS ===\n")
    
    # Definir diretórios possíveis
    raiz_projeto_db_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'database'
    sistema = os.name
    if sistema == 'nt' and 'APPDATA' in os.environ:  # Windows
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
    else:
        app_data_db_dir = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database'
    
    # Caminhos de banco
    antigo_db = raiz_projeto_db_dir / 'sistema.db'
    appdata_db = app_data_db_dir / 'sistema.db'
    
    bancos = [
        ("Banco antigo (raiz projeto)", antigo_db),
        ("Banco APPDATA", appdata_db)
    ]
    
    for nome, caminho in bancos:
        print(f"\n{nome}:")
        print(f"  Caminho: {caminho}")
        print(f"  Existe: {caminho.exists()}")
        
        if caminho.exists():
            try:
                # Conectar e verificar produtos
                conn = sqlite3.connect(str(caminho))
                cursor = conn.cursor()
                
                # Verificar se tabela produtos existe
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='produtos'
                """)
                
                if cursor.fetchone():
                    # Contar produtos
                    cursor.execute("SELECT COUNT(*) FROM produtos")
                    total_produtos = cursor.fetchone()[0]
                    
                    # Calcular valor estoque
                    cursor.execute("""
                        SELECT COALESCE(SUM(estoque * preco_custo), 0) as valor_total
                        FROM produtos
                        WHERE ativo = 1
                    """)
                    valor_estoque = cursor.fetchone()[0] or 0
                    
                    # Calcular valor potencial
                    cursor.execute("""
                        SELECT COALESCE(SUM(estoque * preco_venda), 0) as valor_total
                        FROM produtos
                        WHERE ativo = 1
                    """)
                    valor_potencial = cursor.fetchone()[0] or 0
                    
                    print(f"  Total produtos: {total_produtos}")
                    print(f"  Valor estoque: MT {valor_estoque:.2f}")
                    print(f"  Valor potencial: MT {valor_potencial:.2f}")
                    
                    # Mostrar alguns produtos com estoque
                    cursor.execute("""
                        SELECT id, codigo, nome, estoque, preco_custo, preco_venda
                        FROM produtos 
                        WHERE estoque > 0 
                        ORDER BY estoque DESC 
                        LIMIT 3
                    """)
                    
                    produtos = cursor.fetchall()
                    if produtos:
                        print("  Produtos com estoque:")
                        for produto in produtos:
                            print(f"    - ID {produto[0]}: {produto[2]} (Estoque: {produto[3]})")
                else:
                    print("  ❌ Tabela produtos não existe")
                
                conn.close()
                
            except Exception as e:
                print(f"  ❌ Erro ao verificar banco: {e}")
        else:
            print("  ❌ Banco não existe")

def testar_metodos_database():
    """Testa os métodos da classe Database"""
    print("\n=== TESTE DOS MÉTODOS DATABASE ===\n")
    
    try:
        db = Database()
        
        print("1. Testando get_valor_estoque():")
        valor_estoque = db.get_valor_estoque()
        print(f"   Resultado: MT {valor_estoque:.2f}")
        
        print("\n2. Testando get_valor_venda_estoque():")
        valor_potencial = db.get_valor_venda_estoque()
        print(f"   Resultado: MT {valor_potencial:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar métodos: {e}")
        return False

def main():
    print("=== INVESTIGAÇÃO DE BANCO ===\n")
    
    # 1. Verificar caminho do banco atual
    caminho_atual = verificar_caminho_banco()
    
    # 2. Verificar todos os bancos possíveis
    verificar_bancos_possiveis()
    
    # 3. Testar métodos da Database
    testar_metodos_database()
    
    print("\n🎉 Investigação concluída!")

if __name__ == "__main__":
    main()
