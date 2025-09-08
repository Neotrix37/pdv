#!/usr/bin/env python3
"""
Script para testar o que acontece durante a inicialização do banco de dados
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_inicializacao():
    """Testa o que acontece durante a inicialização"""
    print("=== TESTE DA INICIALIZAÇÃO ===\n")
    
    try:
        # Caminho do banco APPDATA
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        appdata_db = app_data_db_dir / 'sistema.db'
        
        print(f"1. Conectando ao banco: {appdata_db}")
        
        if not appdata_db.exists():
            print("❌ Banco APPDATA não existe!")
            return False
        
        # Fazer backup do banco atual
        backup_path = appdata_db.with_suffix('.db.backup_teste')
        import shutil
        shutil.copy2(str(appdata_db), str(backup_path))
        print(f"2. Backup criado: {backup_path}")
        
        # Conectar ao banco
        conn = sqlite3.connect(str(appdata_db))
        cursor = conn.cursor()
        
        # Verificar estoque ANTES da inicialização
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
        
        # Verificar se há coluna temporária
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = cursor.fetchall()
        temp_estoque_exists = any(c[1] == 'temp_estoque' for c in colunas)
        
        if temp_estoque_exists:
            print("\n4. Encontrada coluna temp_estoque - verificando dados:")
            cursor.execute("SELECT COUNT(*) FROM produtos WHERE temp_estoque > 0")
            temp_estoque_count = cursor.fetchone()[0]
            print(f"  - Produtos com temp_estoque > 0: {temp_estoque_count}")
            
            if temp_estoque_count > 0:
                cursor.execute("SELECT id, nome, temp_estoque, estoque FROM produtos WHERE temp_estoque > 0 LIMIT 5")
                produtos_temp = cursor.fetchall()
                print("  - Exemplos de produtos com temp_estoque:")
                for p in produtos_temp:
                    print(f"    * ID {p[0]}: {p[1]} - temp_estoque: {p[2]}, estoque: {p[3]}")
        
        # Simular o processo de conversão que acontece na inicialização
        print("\n5. Simulando processo de conversão:")
        
        if temp_estoque_exists:
            print("  - Tentando completar conversão de temp_estoque...")
            try:
                # Tentar completar a conversão
                cursor.execute("UPDATE produtos SET estoque = CAST(temp_estoque AS REAL)")
                cursor.execute("ALTER TABLE produtos DROP COLUMN temp_estoque")
                conn.commit()
                print("  ✅ Conversão completada com sucesso!")
            except Exception as e:
                print(f"  ❌ Erro na conversão: {e}")
                conn.rollback()
        
        # Verificar estoque DEPOIS da conversão
        print("\n6. Verificando estoque DEPOIS da conversão:")
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        produtos_com_estoque_depois = cursor.fetchone()[0]
        print(f"  - Produtos com estoque: {produtos_com_estoque_depois}")
        
        if produtos_com_estoque_depois > 0:
            cursor.execute("SELECT SUM(estoque * preco_custo) FROM produtos WHERE ativo = 1")
            valor_estoque_depois = cursor.fetchone()[0] or 0
            print(f"  - Valor total em estoque: MT {valor_estoque_depois:.2f}")
            
            # Mostrar alguns produtos com estoque
            cursor.execute("SELECT id, nome, estoque, preco_custo FROM produtos WHERE estoque > 0 LIMIT 5")
            produtos = cursor.fetchall()
            print("  - Exemplos de produtos com estoque:")
            for p in produtos:
                print(f"    * ID {p[0]}: {p[1]} - Estoque: {p[2]}, Custo: MT {p[3]:.2f}")
        
        # Verificar se houve perda de dados
        if produtos_com_estoque_antes > 0 and produtos_com_estoque_depois == 0:
            print("\n❌ PROBLEMA IDENTIFICADO: Todos os produtos perderam estoque!")
            print("   Isso indica que há um problema na conversão ou migração")
        elif produtos_com_estoque_antes != produtos_com_estoque_depois:
            print(f"\n⚠️  ATENÇÃO: Houve mudança no número de produtos com estoque")
            print(f"   Antes: {produtos_com_estoque_antes}, Depois: {produtos_com_estoque_depois}")
        else:
            print(f"\n✅ Nenhuma perda de dados detectada")
        
        conn.close()
        
        print("\n🎉 Teste concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    print("=== TESTE DA INICIALIZAÇÃO ===\n")
    
    if testar_inicializacao():
        print("\n✅ Teste concluído com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Analise os resultados acima")
        print("2. Se necessário, execute correções específicas")
        print("3. Teste a inicialização novamente")
    else:
        print("\n❌ Falha no teste. Verifique os erros acima.")

if __name__ == "__main__":
    main()
