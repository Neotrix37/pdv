"""
Script para configurar o banco de dados PostgreSQL.
Cria as tabelas necessárias e adiciona usuários padrão.
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, DDL, event
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar os modelos
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importa os modelos para garantir que as tabelas sejam criadas
from backend.app.models.usuario import Usuario, NivelAcesso
from backend.app.models.produto import Produto
from backend.app.models.venda import Venda, ItemVenda, StatusVenda, FormaPagamento
from backend.app.models.cliente import Cliente
from backend.app.models.base import Base

def check_dependencies():
    """Verifica se todas as dependências necessárias estão instaladas."""
    try:
        import sqlalchemy
        from passlib.context import CryptContext
        import bcrypt
        return True
    except ImportError as e:
        print(f"Erro: {e}")
        print("\nPor favor, instale as dependências necessárias executando:")
        print("pip install sqlalchemy passlib bcrypt psycopg2-binary python-dotenv")
        return False

def get_db_connection():
    """Estabelece conexão com o banco de dados PostgreSQL."""
    load_dotenv(Path(__file__).parent.parent.parent / 'backend' / '.env')
    
    db_config = {
        'database': os.getenv('PGDATABASE', 'railway'),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', 'PVVHzsCZDuQiwnuziBfcgukYLCuCxdau'),
        'host': os.getenv('PGHOST', 'interchange.proxy.rlwy.net'),
        'port': os.getenv('PGPORT', '33939')
    }
    
    db_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        sys.exit(1)

def drop_existing_objects(connection):
    """Remove objetos existentes no banco de dados."""
    # Desativa as restrições de chave estrangeira temporariamente
    connection.execute(text('SET session_replication_role = \'replica\';'))
    
    # Remove tabelas
    connection.execute(text('''
        DROP TABLE IF EXISTS itens_venda CASCADE;
        DROP TABLE IF EXISTS vendas CASCADE;
        DROP TABLE IF EXISTS produtos CASCADE;
        DROP TABLE IF EXISTS usuarios CASCADE;
        DROP TABLE IF EXISTS clientes CASCADE;
    '''))
    
    # Remove tipos enum
    connection.execute(text('''
        DROP TYPE IF EXISTS nivelacesso CASCADE;
        DROP TYPE IF EXISTS statusvenda CASCADE;
        DROP TYPE IF EXISTS formapagamento CASCADE;
    '''))
    
    # Reativa as restrições
    connection.execute(text('SET session_replication_role = \'origin\';'))

def create_tables(engine):
    """Cria todas as tabelas no banco de dados."""
    print("Criando tabelas...")
    
    with engine.connect() as connection:
        # Remove objetos existentes
        print("Removendo objetos existentes...")
        drop_existing_objects(connection)
        
        # Cria os tipos enum primeiro
        print("Criando tipos enum...")
        connection.execute(text('''
            CREATE TYPE nivelacesso AS ENUM ('admin', 'gerente', 'vendedor', 'caixa');
            CREATE TYPE statusvenda AS ENUM ('pendente', 'concluida', 'cancelada', 'estornada');
            CREATE TYPE formapagamento AS ENUM ('dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'transferencia', 'outro');
        '''))
        connection.commit()
        
        # Cria as tabelas
        print("Criando tabelas...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")

def create_default_users(session):
    """Cria os usuários padrão no sistema."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Usuário admin
    admin = session.query(Usuario).filter_by(usuario="admin37").first()
    if not admin:
        admin = Usuario(
            nome="Administrador",
            usuario="admin37",
            senha="842384",
            nivel_acesso=NivelAcesso.admin,
            ativo=True
        )
        session.add(admin)
        print("✅ Usuário admin37 criado com sucesso!")
    else:
        print("ℹ️  Usuário admin37 já existe.")
    
    # Usuário funcionário
    funcionario = session.query(Usuario).filter_by(usuario="alves").first()
    if not funcionario:
        funcionario = Usuario(
            nome="Alves",
            usuario="alves",
            senha="842384",
            nivel_acesso=NivelAcesso.vendedor,
            ativo=True
        )
        session.add(funcionario)
        print("✅ Usuário Alves criado com sucesso!")
    else:
        print("ℹ️  Usuário Alves já existe.")
    
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao salvar usuários: {e}")
        raise

def main():
    print("\n=== Configuração do Banco de Dados ===\n")
    
    # Verifica dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Conecta ao banco de dados
    engine = get_db_connection()
    
    try:
        # Cria as tabelas
        create_tables(engine)
        
        # Cria uma sessão para adicionar os usuários
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Adiciona os usuários padrão
        create_default_users(db)
        
        print("\n✅ Configuração do banco de dados concluída com sucesso!")
        print("\nUsuários disponíveis:")
        print("- admin37 (senha: 842384) - Nível: Administrador")
        print("- alves (senha: 842384) - Nível: Vendedor")
        
    except Exception as e:
        print(f"\n❌ Ocorreu um erro durante a configuração: {e}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()
        print("\nConexão com o banco de dados encerrada.")

if __name__ == "__main__":
    main()
