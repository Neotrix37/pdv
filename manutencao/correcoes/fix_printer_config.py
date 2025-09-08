import sqlite3
import os

def fix_printer_config():
    # Caminho para o banco de dados
    db_path = os.path.join('database', 'meu.db')
    
    # Verifica se o arquivo do banco de dados existe
    if not os.path.exists(db_path):
        print(f"Erro: O arquivo do banco de dados não foi encontrado em {db_path}")
        return
    
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se a tabela printer_config existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='printer_config'
        """)
        
        if not cursor.fetchone():
            # Cria a tabela se não existir
            cursor.execute("""
                CREATE TABLE printer_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT NOT NULL,
                    endereco TEXT,
                    telefone TEXT,
                    nuit TEXT,
                    rodape TEXT DEFAULT 'Obrigado pela preferência!',
                    impressora_padrao TEXT,
                    imprimir_automatico INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    email TEXT
                )
            """)
            print("Tabela printer_config criada com sucesso!")
            
            # Insere um registro padrão
            cursor.execute("""
                INSERT INTO printer_config (
                    empresa, 
                    endereco, 
                    telefone, 
                    nuit, 
                    rodape,
                    email
                ) VALUES (
                    'Minha Empresa',
                    'Endereço da Empresa',
                    '(XX) XXXX-XXXX',
                    'XXXXXXXXX',
                    'Obrigado pela preferência!',
                    'contato@empresa.com'
                )
            """)
            print("Configuração padrão adicionada com sucesso!")
        else:
            # Verifica se já existe algum registro
            cursor.execute("SELECT COUNT(*) FROM printer_config")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Insere um registro padrão se a tabela estiver vazia
                cursor.execute("""
                    INSERT INTO printer_config (
                        empresa, 
                        endereco, 
                        telefone, 
                        nuit, 
                        rodape,
                        email
                    ) VALUES (
                        'Minha Empresa',
                        'Endereço da Empresa',
                        '(XX) XXXX-XXXX',
                        'XXXXXXXXX',
                        'Obrigado pela preferência!',
                        'contato@empresa.com'
                    )
                """)
                print("Configuração padrão adicionada com sucesso!")
            else:
                print("A tabela printer_config já existe e contém registros.")
        
        # Confirma as alterações
        conn.commit()
        print("Verificação concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro ao verificar/criar a tabela printer_config: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_printer_config()
