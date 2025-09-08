import sqlite3
from pathlib import Path
import sys

def criar_tabelas():
    # Caminho para o banco de dados
    db_path = Path("database/sistema.db")
    
    # Verificar se o arquivo do banco de dados existe
    if not db_path.exists():
        print("ERRO: O arquivo do banco de dados não foi encontrado em:", db_path.absolute())
        return False
    
    conn = None
    try:
        # Conectar ao banco de dados
        print(f"Conectando ao banco de dados em: {db_path.absolute()}")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("✅ Conectado ao banco de dados com sucesso!")
        
        # Criar tabela de compras
        print("Criando tabela 'compras'...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            valor_total REAL NOT NULL,
            usuario_id INTEGER NOT NULL,
            observacoes TEXT,
            data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )''')
        print("✅ Tabela 'compras' criada/verificada com sucesso!")
        
        # Criar tabela de itens da compra
        print("Criando tabela 'compra_itens'...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS compra_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id INTEGER NOT NULL,
            produto_id INTEGER,
            produto_nome TEXT NOT NULL,
            quantidade REAL NOT NULL,
            preco_unitario REAL NOT NULL,
            preco_venda REAL NOT NULL,
            lucro_unitario REAL NOT NULL,
            lucro_total REAL NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE SET NULL
        )''')
        print("✅ Tabela 'compra_itens' criada/verificada com sucesso!")
        
        # Confirmar as alterações
        conn.commit()
        print("\n✅ Todas as tabelas foram criadas/verificadas com sucesso!")
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ ERRO ao criar as tabelas: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("\nConexão com o banco de dados fechada.")

if __name__ == "__main__":
    print("="*50)
    print("ATUALIZAÇÃO DO BANCO DE DADOS")
    print("="*50)
    
    print("\nIniciando processo de atualização...")
    sucesso = criar_tabelas()
    
    if sucesso:
        print("\n✅ Atualização concluída com sucesso!")
        print("Por favor, reinicie o aplicativo para aplicar as alterações.")
    else:
        print("\n❌ Ocorreu um erro durante a atualização.")
        print("Verifique as mensagens acima para mais detalhes.")
    
    print("\nPressione Enter para sair...")
    input()