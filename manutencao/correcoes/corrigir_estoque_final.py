#!/usr/bin/env python3
"""
Script final para corrigir o problema de estoque de forma definitiva
"""

import sys
import os
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def corrigir_estoque_final():
    """Corrige o problema de estoque de forma definitiva"""
    print("=== CORREÇÃO FINAL DO ESTOQUE ===\n")
    
    try:
        # Caminho do banco APPDATA
        app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
        appdata_db = app_data_db_dir / 'sistema.db'
        
        print(f"1. Conectando ao banco: {appdata_db}")
        
        if not appdata_db.exists():
            print("❌ Banco APPDATA não existe!")
            return False
        
        # Fazer backup do banco atual
        backup_path = appdata_db.with_suffix('.db.backup_final')
        import shutil
        shutil.copy2(str(appdata_db), str(backup_path))
        print(f"2. Backup criado: {backup_path}")
        
        # Conectar ao banco
        conn = sqlite3.connect(str(appdata_db))
        cursor = conn.cursor()
        
        # Verificar estoque atual
        print("\n3. Verificando estoque atual:")
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        produtos_com_estoque = cursor.fetchone()[0]
        print(f"  - Produtos com estoque: {produtos_com_estoque}")
        
        if produtos_com_estoque > 0:
            cursor.execute("SELECT SUM(estoque * preco_custo) FROM produtos WHERE ativo = 1")
            valor_estoque = cursor.fetchone()[0] or 0
            print(f"  - Valor total em estoque: MT {valor_estoque:.2f}")
        
        # Verificar estrutura da tabela produtos
        print("\n4. Verificando estrutura da tabela produtos:")
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = cursor.fetchall()
        
        estoque_col = None
        temp_estoque_exists = False
        
        for col in colunas:
            print(f"  - {col[1]} ({col[2]})")
            if col[1] == 'estoque':
                estoque_col = col
            elif col[1] == 'temp_estoque':
                temp_estoque_exists = True
        
        # Verificar se há coluna temporária com dados
        if temp_estoque_exists:
            print("\n5. Encontrada coluna temp_estoque - verificando dados:")
            cursor.execute("SELECT COUNT(*) FROM produtos WHERE temp_estoque > 0")
            temp_estoque_count = cursor.fetchone()[0]
            print(f"  - Produtos com temp_estoque > 0: {temp_estoque_count}")
            
            if temp_estoque_count > 0:
                print("  - Dados encontrados na coluna temporária!")
                
                # Fazer backup dos dados da coluna temporária
                cursor.execute("SELECT id, temp_estoque FROM produtos WHERE temp_estoque > 0")
                dados_temp = cursor.fetchall()
                print(f"  - Backup de {len(dados_temp)} produtos com dados temporários")
                
                # Transferir dados da coluna temporária para a coluna principal
                print("\n6. Transferindo dados da coluna temporária:")
                for produto in dados_temp:
                    cursor.execute("UPDATE produtos SET estoque = ? WHERE id = ?", 
                                 (float(produto[1]), produto[0]))
                
                # Remover coluna temporária
                cursor.execute("ALTER TABLE produtos DROP COLUMN temp_estoque")
                print("  ✅ Coluna temp_estoque removida")
                
                conn.commit()
                print("  ✅ Dados transferidos com sucesso!")
            else:
                print("  - Nenhum dado encontrado na coluna temporária")
                # Remover coluna temporária vazia
                cursor.execute("ALTER TABLE produtos DROP COLUMN temp_estoque")
                print("  ✅ Coluna temp_estoque vazia removida")
                conn.commit()
        
        # Verificar e remover TODOS os índices problemáticos
        print("\n7. Verificando e removendo índices problemáticos:")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
        todos_indices = cursor.fetchall()
        
        indices_removidos = []
        for idx in todos_indices:
            idx_name = idx[0]
            idx_sql = idx[1] or ""
            
            # Verificar se o índice faz referência a temp_estoque ou tem problemas
            if 'temp_estoque' in idx_sql or 'idx_produtos_estoque' in idx_name:
                print(f"  - Removendo índice problemático: {idx_name}")
                try:
                    cursor.execute(f"DROP INDEX {idx_name}")
                    indices_removidos.append(idx_name)
                    print(f"    ✅ Índice {idx_name} removido")
                except Exception as e:
                    print(f"    ❌ Erro ao remover índice {idx_name}: {e}")
        
        if indices_removidos:
            print(f"  - Total de índices removidos: {len(indices_removidos)}")
        else:
            print("  - Nenhum índice problemático encontrado")
        
        # Recriar índice de estoque
        print("\n8. Recriando índice de estoque:")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_produtos_estoque 
                ON produtos(estoque, ativo)
            """)
            print("  ✅ Índice de estoque recriado com sucesso!")
        except Exception as e:
            print(f"  ❌ Erro ao recriar índice: {e}")
        
        # Verificar se há algum trigger que possa estar causando problemas
        print("\n9. Verificando triggers:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()
        
        for trigger in triggers:
            print(f"  - {trigger[0]}")
        
        # Verificar resultado final
        print("\n10. Verificando resultado final:")
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque > 0")
        produtos_final = cursor.fetchone()[0]
        print(f"  - Produtos com estoque: {produtos_final}")
        
        if produtos_final > 0:
            cursor.execute("SELECT SUM(estoque * preco_custo) FROM produtos WHERE ativo = 1")
            valor_final = cursor.fetchone()[0] or 0
            print(f"  - Valor total em estoque: MT {valor_final:.2f}")
            
            # Mostrar alguns produtos com estoque
            cursor.execute("SELECT id, nome, estoque, preco_custo FROM produtos WHERE estoque > 0 LIMIT 5")
            produtos = cursor.fetchall()
            print("  - Exemplos de produtos com estoque:")
            for p in produtos:
                print(f"    * ID {p[0]}: {p[1]} - Estoque: {p[2]}, Custo: MT {p[3]:.2f}")
        
        conn.close()
        
        print("\n🎉 Correção final concluída com sucesso!")
        
        if produtos_final > 0:
            print(f"✅ {produtos_final} produtos com estoque restaurados")
            print(f"✅ Valor total em estoque: MT {valor_final:.2f}")
        else:
            print("⚠️  Nenhum produto com estoque encontrado")
            print("   Recomendação: Restaurar um backup que tenha produtos com estoque")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na correção: {e}")
        return False

def main():
    print("=== CORREÇÃO FINAL DO ESTOQUE ===\n")
    
    if corrigir_estoque_final():
        print("\n✅ Correção final concluída!")
        print("\n📋 Próximos passos:")
        print("1. Execute o sistema: python main.py")
        print("2. Verifique se o estoque persiste entre execuções")
        print("3. Se necessário, restaure um backup com produtos")
    else:
        print("\n❌ Falha na correção. Verifique os erros acima.")

if __name__ == "__main__":
    main()
