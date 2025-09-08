#!/usr/bin/env python3
"""
Script para investigar o que acontece durante a inicialização do banco de dados
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def investigar_inicializacao():
    """Investiga o que acontece durante a inicialização"""
    print("=== INVESTIGAÇÃO DA INICIALIZAÇÃO ===\n")
    
    try:
        # Caminho do banco APPDATA
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        appdata_db = app_data_db_dir / 'sistema.db'
        
        print(f"1. Conectando ao banco: {appdata_db}")
        
        if not appdata_db.exists():
            print("❌ Banco APPDATA não existe!")
            return False
        
        # Fazer backup do banco atual
        backup_path = appdata_db.with_suffix('.db.backup_investigacao')
        import shutil
        shutil.copy2(str(appdata_db), str(backup_path))
        print(f"2. Backup criado: {backup_path}")
        
        # Conectar ao banco
        conn = sqlite3.connect(str(appdata_db))
        cursor = conn.cursor()
        
        # Verificar estoque antes da inicialização
        print("\n3. Verificando estoque ANTES da inicialização:")
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        produtos_com_estoque_antes = cursor.fetchone()[0]
        print(f"  - Produtos com estoque: {produtos_com_estoque_antes}")
        
        if produtos_com_estoque_antes > 0:
            cursor.execute("SELECT SUM(estoque * preco_custo) FROM produtos WHERE ativo = 1")
            valor_estoque_antes = cursor.fetchone()[0] or 0
            print(f"  - Valor total em estoque: MT {valor_estoque_antes:.2f}")
            
            # Mostrar alguns produtos com estoque
            cursor.execute("SELECT id, nome, estoque, preco_custo FROM produtos WHERE estoque > 0 LIMIT 5")
            produtos = cursor.fetchall()
            print("  - Exemplos de produtos com estoque:")
            for p in produtos:
                print(f"    * ID {p[0]}: {p[1]} - Estoque: {p[2]}, Custo: MT {p[3]:.2f}")
        
        # Verificar estrutura da tabela produtos
        print("\n4. Verificando estrutura da tabela produtos:")
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = cursor.fetchall()
        
        estoque_col = None
        estoque_minimo_col = None
        
        for col in colunas:
            print(f"  - {col[1]} ({col[2]})")
            if col[1] == 'estoque':
                estoque_col = col
            elif col[1] == 'estoque_minimo':
                estoque_minimo_col = col
        
        # Verificar se há colunas temporárias
        temp_cols = [col for col in colunas if col[1].startswith('temp_')]
        if temp_cols:
            print(f"\n5. Encontradas {len(temp_cols)} colunas temporárias:")
            for col in temp_cols:
                print(f"  - {col[1]} ({col[2]})")
        
        # Verificar índices
        print("\n6. Verificando índices:")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
        indices = cursor.fetchall()
        
        for idx in indices:
            print(f"  - {idx[0]}: {idx[1]}")
        
        # Simular o processo de conversão que acontece na inicialização
        print("\n7. Simulando processo de conversão:")
        
        if estoque_col and estoque_col[2].upper() == 'INTEGER':
            print("  - Coluna estoque é INTEGER, seria convertida para REAL")
            
            # Verificar se há índice problemático
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql LIKE '%temp_estoque%'")
            indices_problema = cursor.fetchall()
            
            if indices_problema:
                print(f"  - Encontrados {len(indices_problema)} índices problemáticos:")
                for idx in indices_problema:
                    print(f"    * {idx[0]}")
            
            # Verificar se há coluna temporária
            if any(c[1] == 'temp_estoque' for c in colunas):
                print("  - Existe coluna temp_estoque")
            else:
                print("  - Não existe coluna temp_estoque")
        else:
            print("  - Coluna estoque já é REAL")
        
        # Verificar se há algum trigger ou constraint que possa estar zerando
        print("\n8. Verificando triggers e constraints:")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()
        
        for trigger in triggers:
            print(f"  - {trigger[0]}: {trigger[1]}")
        
        # Verificar se há algum código que zera estoque
        print("\n9. Verificando se há produtos com estoque NULL ou negativo:")
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"  - Produtos com estoque NULL: {null_count}")
        
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque < 0")
        negativo_count = cursor.fetchone()[0]
        print(f"  - Produtos com estoque negativo: {negativo_count}")
        
        # Verificar se há algum código que atualiza estoque para 0
        print("\n10. Verificando se há algum código que zera estoque:")
        
        # Verificar se há algum UPDATE que zera estoque
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque = 0")
        zero_count = cursor.fetchone()[0]
        print(f"  - Produtos com estoque = 0: {zero_count}")
        
        # Verificar se há algum código que converte estoque
        if estoque_col and estoque_col[2].upper() == 'INTEGER':
            print("  - ⚠️  ATENÇÃO: Coluna estoque é INTEGER e seria convertida!")
            print("  - Isso pode estar causando a perda de dados durante a conversão")
        
        conn.close()
        
        print("\n🎉 Investigação concluída!")
        print("\n📋 Análise:")
        if estoque_col and estoque_col[2].upper() == 'INTEGER':
            print("❌ PROBLEMA IDENTIFICADO: A coluna estoque é INTEGER e está sendo convertida para REAL")
            print("   Isso pode estar causando a perda de dados durante a conversão")
            print("   Recomendação: Corrigir a conversão para preservar os dados")
        else:
            print("✅ Coluna estoque já é REAL")
        
        if produtos_com_estoque_antes == 0:
            print("❌ PROBLEMA: Não há produtos com estoque no banco atual")
            print("   Recomendação: Restaurar um backup que tenha produtos com estoque")
        else:
            print(f"✅ Há {produtos_com_estoque_antes} produtos com estoque")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na investigação: {e}")
        return False

def main():
    print("=== INVESTIGAÇÃO DA INICIALIZAÇÃO ===\n")
    
    if investigar_inicializacao():
        print("\n✅ Investigação concluída com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Analise os resultados acima")
        print("2. Se necessário, execute correções específicas")
        print("3. Teste a inicialização novamente")
    else:
        print("\n❌ Falha na investigação. Verifique os erros acima.")

if __name__ == "__main__":
    main()
