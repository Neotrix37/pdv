"""
Script para gerenciar tabelas em um banco de dados PostgreSQL.
Permite listar e remover tabelas de forma segura.
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

def get_db_connection():
    """
    Estabelece conexão com o banco de dados PostgreSQL.
    Usa as variáveis de ambiente do arquivo .env ou valores padrão.
    """
    load_dotenv('../../../backend/.env')  # Ajuste o caminho conforme necessário
    
    db_config = {
        'dbname': os.getenv('PGDATABASE', 'railway'),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', 'PVVHzsCZDuQiwnuziBfcgukYLCuCxdau'),
        'host': os.getenv('PGHOST', 'interchange.proxy.rlwy.net'),
        'port': os.getenv('PGPORT', '33939')
    }
    
    try:
        print("Conectando ao banco de dados...")
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        sys.exit(1)

def list_tables(conn):
    """Lista todas as tabelas do banco de dados."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        return [table[0] for table in cursor.fetchall()]

def drop_tables(conn, tables):
    """
    Remove as tabelas especificadas do banco de dados.
    
    Args:
        conn: Conexão com o banco de dados
        tables: Lista de nomes de tabelas para remover
    """
    if not tables:
        print("Nenhuma tabela para remover.")
        return False
        
    with conn.cursor() as cursor:
        try:
            # Desativa temporariamente as restrições de chave estrangeira
            cursor.execute("SET session_replication_role = 'replica';")
            
            for table in tables:
                try:
                    # Usa sql.SQL e sql.Identifier para prevenir SQL injection
                    cursor.execute(
                        sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                            sql.Identifier(table)
                        )
                    )
                    print(f"✅ Tabela '{table}' removida com sucesso.")
                except Exception as e:
                    print(f"❌ Erro ao remover tabela '{table}': {e}")
            
            # Reativa as restrições de chave estrangeira
            cursor.execute("SET session_replication_role = 'origin';")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a remoção das tabelas: {e}")
            # Tenta reativar as restrições em caso de erro
            try:
                cursor.execute("SET session_replication_role = 'origin';")
            except:
                pass
            return False

def main():
    print("\n=== Gerenciador de Tabelas PostgreSQL ===\n")
    
    # Estabelece conexão com o banco de dados
    conn = get_db_connection()
    
    try:
        # Lista as tabelas existentes
        print("🔍 Buscando tabelas no banco de dados...")
        tables = list_tables(conn)
        
        if not tables:
            print("ℹ️ Nenhuma tabela encontrada no banco de dados.")
            return
            
        print("\n📋 Tabelas encontradas:")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
            
        # Confirmação do usuário
        print("\n⚠️  ATENÇÃO: Esta operação é IRREVERSÍVEL e removerá TODAS as tabelas listadas acima.")
        confirm = input("\n❓ Deseja realmente continuar? (s/n): ")
        
        if confirm.lower() == 's':
            print("\n🔄 Removendo tabelas...")
            success = drop_tables(conn, tables)
            
            if success:
                print("\n✅ Todas as tabelas foram removidas com sucesso!")
            else:
                print("\n❌ Ocorreram erros durante a remoção das tabelas.")
        else:
            print("\n❌ Operação cancelada pelo usuário.")
            
    except KeyboardInterrupt:
        print("\n\nOperação interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")
    finally:
        conn.close()
        print("\nConexão com o banco de dados encerrada.")

if __name__ == "__main__":
    main()
