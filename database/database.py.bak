import sqlite3
from pathlib import Path
import threading
from werkzeug.security import generate_password_hash
import os
import hashlib
from datetime import datetime
from time import strftime
import platform
import shutil

class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def _create_connection(self):
        """Cria uma nova conexão com o banco de dados com configurações otimizadas"""
        try:
            # Aumenta o timeout para evitar erros de 'database is locked'
            conn = sqlite3.connect(str(self.db_path.absolute()), 
                                  check_same_thread=False, 
                                  timeout=30.0)
            conn.row_factory = sqlite3.Row
            
            # Configura pragmas para melhor desempenho e estabilidade
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA busy_timeout = 30000")  # 30 segundos de timeout
            conn.commit()
            
            return conn
        except sqlite3.Error as e:
            print(f"Erro ao criar conexão com o banco de dados: {e}")
            # Tenta novamente após um pequeno atraso
            import time
            time.sleep(1)
            return sqlite3.connect(str(self.db_path.absolute()), 
                                 check_same_thread=False, 
                                 timeout=60.0)
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            # Definir diretórios possíveis para o banco de dados
            raiz_projeto_db_dir = Path(os.path.dirname(os.path.dirname(__file__))) / 'database'
            sistema = platform.system().lower()
            if sistema == 'windows' and 'APPDATA' in os.environ:
                app_data_db_dir = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database'
            else:
                app_data_db_dir = Path(os.path.expanduser('~')) / '.sistemagestao' / 'database'

            # Caminhos de banco
            antigo_db = raiz_projeto_db_dir / 'sistema.db'
            app_data_db_dir.mkdir(parents=True, exist_ok=True)
            appdata_db = app_data_db_dir / 'sistema.db'

            # Migração: se existir banco antigo e (não existir no APPDATA ou antigo for mais recente), copiar
            try:
                if antigo_db.exists():
                    precisa_copiar = (not appdata_db.exists())
                    if not precisa_copiar:
                        try:
                            precisa_copiar = antigo_db.stat().st_mtime > appdata_db.stat().st_mtime
                        except Exception:
                            precisa_copiar = False
                    if precisa_copiar:
                        shutil.copy2(str(antigo_db), str(appdata_db))
                        print("Banco migrado para APPDATA com sucesso.")
            except Exception as mig_err:
                print(f"Falha ao migrar banco para APPDATA: {mig_err}")

            # Sempre preferir APPDATA para a conexão; se falhar, usar antigo como fallback
            prefered_db_path = appdata_db
            if not prefered_db_path.exists() and antigo_db.exists():
                prefered_db_path = antigo_db
            
            # Caminho absoluto para o banco de dados
            self.db_path = prefered_db_path
            
            # Conexão com o banco de dados usando o método otimizado
            self.conn = self._create_connection()
            
            # Inicializa as tabelas
            self._init_database()
            self.initialized = True

    def _init_database(self):
        """Inicializa o banco de dados criando as tabelas necessárias se não existirem"""
        try:
            # Usa um lock para garantir que apenas uma thread inicialize o banco de dados por vez
            with self._lock:
                cursor = self.conn.cursor()
                
                # Configura timeout para evitar erros de 'database is locked'
                cursor.execute("PRAGMA busy_timeout = 30000")  # 30 segundos
            
            # Criar tabela de descontos se não existir
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS descontos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_desconto DATETIME NOT NULL,
                valor REAL NOT NULL,
                tipo TEXT NOT NULL,  -- 'vendas' ou 'lucro'
                descricao TEXT,
                usuario_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
            ''')
            
            # Criar tabela de usuários se não existir
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                usuario TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                nivel INTEGER NOT NULL DEFAULT 1,
                ativo INTEGER NOT NULL DEFAULT 1,
                is_admin INTEGER NOT NULL DEFAULT 0,
                salario REAL DEFAULT 0,
                pode_abastecer INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Adicionar coluna pode_abastecer se não existir
            try:
                cursor.execute('ALTER TABLE usuarios ADD COLUMN pode_abastecer INTEGER NOT NULL DEFAULT 0')
                self.conn.commit()
                print("Coluna 'pode_abastecer' adicionada à tabela usuarios")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("Coluna 'pode_abastecer' já existe na tabela usuarios")
                else:
                    print(f"Erro ao adicionar coluna pode_abastecer: {e}")
            
            self.conn.commit()

            # Criar tabela de clientes
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                nuit TEXT,
                telefone TEXT,
                email TEXT,
                endereco TEXT,
                especial INTEGER DEFAULT 0,
                desconto_divida REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            self.conn.commit()

            # Verificar se a coluna salario existe na tabela usuarios
            cursor.execute("PRAGMA table_info(usuarios)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            if 'salario' not in colunas_nomes:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN salario REAL DEFAULT 0")
                self.conn.commit()

            # Verificar e adicionar colunas de cliente especial
            cursor.execute("PRAGMA table_info(clientes)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            if 'especial' not in colunas_nomes:
                cursor.execute("ALTER TABLE clientes ADD COLUMN especial INTEGER DEFAULT 0")
                self.conn.commit()
                
            if 'desconto_divida' not in colunas_nomes:
                cursor.execute("ALTER TABLE clientes ADD COLUMN desconto_divida REAL DEFAULT 0")
                self.conn.commit()

# Tabela de dívidas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dividas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    data_divida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valor_total REAL NOT NULL,
                    valor_original REAL DEFAULT 0,
                    desconto_aplicado REAL DEFAULT 0,
                    percentual_desconto REAL DEFAULT 0,
                    valor_pago REAL DEFAULT 0,
                    status TEXT DEFAULT 'Pendente',
                    observacao TEXT,
                    usuario_id INTEGER NOT NULL,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)
            
            # Tabela de itens da dívida
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS itens_divida (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    divida_id INTEGER NOT NULL,
                    produto_id INTEGER NOT NULL,
                    quantidade REAL NOT NULL,
                    preco_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    peso_kg REAL DEFAULT 0,
                    FOREIGN KEY (divida_id) REFERENCES dividas(id),
                    FOREIGN KEY (produto_id) REFERENCES produtos(id)
                )
            """)
            
            # Tabela de pagamentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagamentos_divida (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    divida_id INTEGER NOT NULL,
                    data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valor REAL NOT NULL,
                    forma_pagamento TEXT NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    FOREIGN KEY (divida_id) REFERENCES dividas(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)

            # Criar usuário admin padrão apenas se não existir
            cursor.execute('SELECT COUNT(*) FROM usuarios WHERE usuario = ?', ('admin',))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                INSERT INTO usuarios (nome, usuario, senha, is_admin, ativo, nivel, salario)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'Administrador',
                    'admin',
                    generate_password_hash('842384'),
                    1,  # is_admin = True
                    1,  # ativo = True
                    2,  # nivel = 2 (admin)
                    0.0  # salario inicial
                ))
                self.conn.commit()
                print("Usuário admin criado com sucesso!")

            # (Removido: DDL duplicada de clientes)

            # Criar tabela de categorias
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Verificar se existem categorias
            categorias = cursor.execute('SELECT COUNT(*) as total FROM categorias').fetchone()
            if categorias['total'] == 0:
                # Inserir categorias padrão
                categorias_padrao = [
                    ('Alimentos', 'Produtos alimentícios em geral'),
                    ('Bebidas', 'Bebidas em geral'),
                    ('Limpeza', 'Produtos de limpeza'),
                    ('Higiene', 'Produtos de higiene pessoal'),
                    ('Congelados', 'Produtos congelados'),
                    ('Mercearia', 'Produtos de mercearia em geral'),
                    ('Padaria', 'Produtos de padaria'),
                    ('Hortifruti', 'Frutas, legumes e verduras'),
                    ('Açougue', 'Carnes em geral'),
                    ('Laticínios', 'Leite e derivados'),
                    ('Outros', 'Outros tipos de produtos')
                ]
                cursor.executemany(
                    'INSERT INTO categorias (nome, descricao) VALUES (?, ?)',
                    categorias_padrao
                )
                self.conn.commit()
                print("Categorias padrão criadas com sucesso!")

            # Criar tabela de fornecedores
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                email TEXT,
                endereco TEXT,
                cnpj TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Inserir fornecedor padrão
            cursor.execute('''
                INSERT OR IGNORE INTO fornecedores (id, nome, ativo)
                VALUES (1, 'Fornecedor Padrão', 1)
            ''')

            # Criar tabela de compras
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fornecedor TEXT NOT NULL,
                valor_total REAL NOT NULL,
                usuario_id INTEGER NOT NULL,
                observacoes TEXT,
                data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            ''')

            # Criar tabela de itens da compra
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
            )
            ''')

            # Criar tabela de produtos
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                descricao TEXT,
                preco_custo REAL NOT NULL,
                preco_venda REAL NOT NULL,
                estoque REAL NOT NULL DEFAULT 0,
                estoque_minimo REAL NOT NULL DEFAULT 0,
                ativo INTEGER NOT NULL DEFAULT 1,
                venda_por_peso INTEGER DEFAULT 0,
                unidade_medida TEXT DEFAULT 'un',
                categoria_id INTEGER,
                fornecedor_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
            )
            ''')

            # Verificar e adicionar colunas ausentes na tabela produtos
            cursor.execute("PRAGMA table_info(produtos)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            # Adicionar categoria_id se não existir
            if 'categoria_id' not in colunas_nomes:
                try:
                    cursor.execute("""
                        ALTER TABLE produtos
                        ADD COLUMN categoria_id INTEGER REFERENCES categorias(id)
                    """)
                    self.conn.commit()
                    print("Coluna categoria_id adicionada com sucesso!")
                except Exception as e:
                    self.conn.rollback()
                    print(f"Erro ao adicionar coluna categoria_id: {e}")
            
            # Adicionar fornecedor_id se não existir
            if 'fornecedor_id' not in colunas_nomes:
                try:
                    cursor.execute("""
                        ALTER TABLE produtos
                        ADD COLUMN fornecedor_id INTEGER DEFAULT 1 REFERENCES fornecedores(id)
                    """)
                    self.conn.commit()
                    print("Coluna fornecedor_id adicionada com sucesso!")
                except Exception as e:
                    self.conn.rollback()
                    print(f"Erro ao adicionar coluna fornecedor_id: {e}")
            
            # Verificar se há coluna temporária temp_estoque e restaurar dados se necessário
            cursor.execute("PRAGMA table_info(produtos)")
            colunas = cursor.fetchall()
            temp_estoque_exists = any(c[1] == 'temp_estoque' for c in colunas)
            
            if temp_estoque_exists:
                print("Encontrada coluna temp_estoque - restaurando dados...")
                try:
                    # Primeiro, verificar e remover índices que referenciam temp_estoque
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type = 'index' 
                        AND sql LIKE '%temp_estoque%'
                    """)
                    indices_problema = cursor.fetchall()
                    
                    for idx in indices_problema:
                        try:
                            cursor.execute(f"DROP INDEX IF EXISTS {idx[0]}")
                            print(f"Índice problemático {idx[0]} removido")
                        except Exception as e:
                            print(f"Erro ao remover índice {idx[0]}: {e}")
                    
                    # Verificar se há dados na coluna temporária
                    cursor.execute("SELECT COUNT(*) FROM productos WHERE temp_estoque > 0")
                    temp_estoque_count = cursor.fetchone()[0]
                    
                    if temp_estoque_count > 0:
                        print(f"Restaurando {temp_estoque_count} produtos com dados temporários")
                        # Transferir dados da coluna temporária para a coluna principal
                        cursor.execute("SELECT id, temp_estoque FROM productos WHERE temp_estoque > 0")
                        dados_temp = cursor.fetchall()
                        
                        for produto in dados_temp:
                            cursor.execute("UPDATE productos SET estoque = ? WHERE id = ?", 
                                         (float(produto[1]), produto[0]))
                    
                    # Remover coluna temporária
                    cursor.execute("""
                        CREATE TABLE produtos_backup AS 
                        SELECT id, codigo, nome, descricao, preco_custo, preco_venda, 
                               estoque, estoque_minimo, ativo, venda_por_peso, 
                               unidade_medida, categoria_id, fornecedor_id, 
                               created_at, updated_at
                        FROM productos
                    """)
                    
                    cursor.execute("DROP TABLE productos")
                    cursor.execute("ALTER TABLE productos_backup RENAME TO productos")
                    
                    # Recriar índices necessários
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_productos_estoque 
                        ON productos(estoque, ativo)
                    """)
                    
                    cursor.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_productos_codigo 
                        ON productos(codigo)
                    """)
                    
                    self.conn.commit()
                    print("Dados de estoque restaurados com sucesso!")
                except Exception as e:
                    self.conn.rollback()
                    print(f"Erro ao processar coluna temp_estoque: {e}")
                    raise
            
            # Verificar e remover índices problemáticos
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql LIKE '%temp_estoque%'")
            indices_problema = cursor.fetchall()
            
            for idx in indices_problema:
                try:
                    cursor.execute(f"DROP INDEX {idx[0]}")
                    print(f"Índice problemático {idx[0]} removido")
                except Exception as e:
                    print(f"Erro ao remover índice {idx[0]}: {e}")
            
            # Recriar índice de estoque se necessário
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_produtos_estoque 
                    ON produtos(estoque, ativo)
                """)
                print("Índice de estoque verificado/criado")
            except Exception as e:
                print(f"Erro ao verificar índice de estoque: {e}")

            # Criar tabela de vendas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                total REAL NOT NULL,
                forma_pagamento TEXT NOT NULL,
                valor_recebido REAL,
                troco REAL,
                data_venda DATETIME NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
            ''')

            # Criar tabela de itens da venda
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS itens_venda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                preco_custo_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venda_id) REFERENCES vendas (id),
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
            ''')

            # Verificar se as colunas já existem antes de tentar criar
            cursor.execute("PRAGMA table_info(itens_venda)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            # Só adiciona as colunas se não existirem
            if 'status' not in colunas_nomes:
                cursor.execute("ALTER TABLE itens_venda ADD COLUMN status TEXT")
                
            if 'motivo_alteracao' not in colunas_nomes:
                cursor.execute("ALTER TABLE itens_venda ADD COLUMN motivo_alteracao TEXT")
                
            if 'alterado_por' not in colunas_nomes:
                cursor.execute("ALTER TABLE itens_venda ADD COLUMN alterado_por INTEGER REFERENCES usuarios(id)")
                
            if 'data_alteracao' not in colunas_nomes:
                cursor.execute("ALTER TABLE itens_venda ADD COLUMN data_alteracao TIMESTAMP")
            
            # Verificar se a coluna peso_kg existe na tabela itens_venda
            if 'peso_kg' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE itens_venda
                    ADD COLUMN peso_kg REAL DEFAULT 0
                """)
            
            # Verificar se a coluna peso_kg existe na tabela itens_divida
            cursor.execute("PRAGMA table_info(itens_divida)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            if 'peso_kg' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE itens_divida
                    ADD COLUMN peso_kg REAL DEFAULT 0
                """)
            
            self.conn.commit()
            
            # Criar tabela printer_config se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS printer_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT NOT NULL,
                    endereco TEXT,
                    telefone TEXT,
                    nuit TEXT,
                    rodape TEXT DEFAULT 'Obrigado pela preferência!',
                    impressora_padrao TEXT,
                    imprimir_automatico INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Criar trigger para atualização automática
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS printer_config_updated_at 
                AFTER UPDATE ON printer_config
                BEGIN
                    UPDATE printer_config 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            """)
            
            # Verificar se existe alguma configuração
            cursor.execute("SELECT COUNT(*) as total FROM printer_config")
            total = cursor.fetchone()[0]
            
            # Inserir configuração padrão apenas se não existir nenhuma configuração
            if total == 0:
                cursor.execute("""
                    INSERT INTO printer_config (
                        empresa, 
                        endereco, 
                        telefone, 
                        nuit, 
                        rodape
                    ) VALUES (
                        'Nome da Empresa',
                        'Endereço da Empresa',
                        'Telefone',
                        'NUIT',
                        'Obrigado pela preferência!'
                    )
                """)
                self.conn.commit()

            # Criar tabela de contas a pagar
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contas_pagar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_vencimento DATE NOT NULL,
                    data_pagamento DATE,
                    categoria TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pendente',  -- 'Pendente' ou 'Pago'
                    observacao TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            """)

            # Criar tabela de movimentação de caixa
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentacao_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_movimento DATETIME NOT NULL,
                    tipo TEXT NOT NULL,  -- 'Entrada' ou 'Saída'
                    valor REAL NOT NULL,
                    descricao TEXT NOT NULL,
                    categoria TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            """)

            # Inserir algumas categorias padrão para contas a pagar
            categorias = [
                ('Fornecedores',),
                ('Aluguel',),
                ('Energia',),
                ('Água',),
                ('Internet',),
                ('Salários',),
                ('Impostos',),
                ('Manutenção',),
                ('Marketing',),
                ('Outros',)
            ]
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias_despesa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                )
            """)

            # Inserir categorias apenas se não existirem
            for categoria in categorias:
                try:
                    cursor.execute("""
                        INSERT INTO categorias_despesa (nome)
                        VALUES (?)
                    """, categoria)
                except:
                    pass  # Ignora se a categoria já existe

            # (Removido: DDL duplicada de contas_pagar e movimentacao_caixa)

            # Create trigger for sales
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS after_venda_insert 
                AFTER INSERT ON vendas
                BEGIN
                    INSERT INTO movimentacao_caixa (
                        data_movimento,
                        tipo,
                        valor,
                        descricao,
                        usuario_id
                    )
                    VALUES (
                        NEW.data_venda,
                        'Entrada',
                        NEW.total,
                        'Venda #' || NEW.id,
                        NEW.usuario_id
                    );
                END
            """)

            # Create trigger for paid bills
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS after_conta_pagar_update 
                AFTER UPDATE OF status ON contas_pagar
                WHEN NEW.status = 'Pago' AND OLD.status = 'Pendente'
                BEGIN
                    INSERT INTO movimentacao_caixa (
                        data_movimento,
                        tipo,
                        valor,
                        descricao,
                        usuario_id
                    )
                    VALUES (
                        NEW.data_pagamento,
                        'Saída',
                        NEW.valor,
                        'Pagamento: ' || NEW.descricao,
                        NEW.usuario_id
                    );
                END
            """)

            # Criar tabela de despesas recorrentes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS despesas_recorrentes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_vencimento DATE NOT NULL,
                    data_pagamento DATE,
                    status TEXT NOT NULL DEFAULT 'Pendente',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Criar trigger para atualização automática
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS despesas_recorrentes_updated_at 
                AFTER UPDATE ON despesas_recorrentes
                BEGIN
                    UPDATE despesas_recorrentes 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            """)

            # Criar tabela de orçamentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orcamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ano INTEGER NOT NULL,
                    mes INTEGER NOT NULL,
                    categoria TEXT NOT NULL,
                    tipo TEXT NOT NULL,  -- 'Receita' ou 'Despesa'
                    valor_previsto REAL NOT NULL,
                    valor_realizado REAL DEFAULT 0,
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Trigger para atualizar data de modificação
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS orcamentos_updated_at 
                AFTER UPDATE ON orcamentos
                BEGIN
                    UPDATE orcamentos 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            """)

            # Criar tabela de configurações da fatura
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_fatura (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_empresa TEXT,
                endereco TEXT,
                telefone TEXT,
                nuit TEXT,
                website TEXT,
                email TEXT,
                logo_path TEXT,
                rodape TEXT
            )
            ''')

            # Criar tabela de formas de pagamento
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS formas_pagamento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    ativo INTEGER DEFAULT 1
                )
            """)

            # Inserir formas de pagamento padrão
            formas_pagamento = [
                ('Dinheiro',),
                ('M-PESA',),
                ('E-Mola',),
                ('Cartão',),
                ('Transferência',),
                ('Millennium BIM',),
                ('BCI',),
                ('Standard Bank',),
                ('ABSA Bank',),
                ('Letshego',),
                ('MyBucks',)
            ]

            # Inserir formas apenas se não existirem
            for forma in formas_pagamento:
                try:
                    cursor.execute("""
                        INSERT INTO formas_pagamento (nome)
                        VALUES (?)
                    """, forma)
                except:
                    pass  # Ignora se já existe

            # Verificar e adicionar colunas de desconto na tabela dividas
            cursor.execute("PRAGMA table_info(dividas)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            if 'valor_original' not in colunas_nomes:
                cursor.execute("ALTER TABLE dividas ADD COLUMN valor_original REAL DEFAULT 0")
                self.conn.commit()
                
            if 'desconto_aplicado' not in colunas_nomes:
                cursor.execute("ALTER TABLE dividas ADD COLUMN desconto_aplicado REAL DEFAULT 0")
                self.conn.commit()
                
            if 'percentual_desconto' not in colunas_nomes:
                cursor.execute("ALTER TABLE dividas ADD COLUMN percentual_desconto REAL DEFAULT 0")
                self.conn.commit()

            # Verificar e adicionar novas colunas na tabela vendas
            cursor.execute("PRAGMA table_info(vendas)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            # Adicionar coluna status se não existir
            if 'status' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE vendas
                    ADD COLUMN status TEXT NOT NULL DEFAULT 'Ativa'
                """)
            
            # Adicionar coluna motivo_alteracao se não existir
            if 'motivo_alteracao' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE vendas
                    ADD COLUMN motivo_alteracao TEXT
                """)
            
            # Adicionar coluna alterado_por se não existir
            if 'alterado_por' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE vendas
                    ADD COLUMN alterado_por INTEGER
                    REFERENCES usuarios(id)
                """)
            
            # Adicionar coluna data_alteracao se não existir
            if 'data_alteracao' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE vendas
                    ADD COLUMN data_alteracao TIMESTAMP
                """)

            # Adicionar coluna origem na tabela vendas se não existir
            cursor.execute("PRAGMA table_info(vendas)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            if 'origem' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE vendas
                    ADD COLUMN origem TEXT DEFAULT 'venda_direta'
                """)
            
            # Adicionar colunas para armazenar valores originais da dívida
            if 'valor_original_divida' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE vendas
                    ADD COLUMN valor_original_divida REAL DEFAULT 0
                """)
                
            if 'desconto_aplicado_divida' not in colunas_nomes:
                cursor.execute("""
                    ALTER TABLE vendas
                    ADD COLUMN desconto_aplicado_divida REAL DEFAULT 0
                """)
            
            # Criar trigger para quando uma dívida for quitada
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS after_divida_quitada
                AFTER UPDATE ON dividas
                WHEN NEW.status = 'Quitado' AND OLD.status = 'Pendente'
                BEGIN
                    -- Inserir na tabela de vendas (sem afetar estoque)
                    INSERT INTO vendas (
                        usuario_id,
                        total,
                        forma_pagamento,
                        valor_recebido,
                        troco,
                        data_venda,
                        origem,
                        valor_original_divida,
                        desconto_aplicado_divida
                    )
                    SELECT 
                        d.usuario_id,
                        d.valor_total,
                        (SELECT forma_pagamento FROM pagamentos_divida 
                         WHERE divida_id = d.id 
                         ORDER BY data_pagamento DESC LIMIT 1),
                        d.valor_total,
                        0,
                        datetime('now', 'localtime'),
                        'divida_quitada',
                        d.valor_original,
                        d.desconto_aplicado
                    FROM dividas d
                    WHERE d.id = NEW.id;

                    -- Inserir itens da venda (sem afetar estoque)
                    INSERT INTO itens_venda (
                        venda_id,
                        produto_id,
                        quantidade,
                        preco_unitario,
                        preco_custo_unitario,
                        subtotal,
                        peso_kg
                    )
                    SELECT 
                        last_insert_rowid(),
                        id.produto_id,
                        id.quantidade,
                        id.preco_unitario,
                        (SELECT preco_custo FROM produtos WHERE id = id.produto_id),
                        id.subtotal,
                        id.peso_kg
                    FROM itens_divida id
                    WHERE id.divida_id = NEW.id;
                END
            """)

            # Adicionar índices para melhorar performance de busca
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_produtos_busca 
                ON produtos(nome, ativo)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_produtos_estoque 
                ON produtos(estoque, ativo)
            """)

            # Verificar se a coluna venda_por_peso existe
            cursor.execute("PRAGMA table_info(produtos)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            # Se a coluna venda_por_peso não existir, adiciona
            if 'venda_por_peso' not in colunas_nomes:
                try:
                    cursor.execute("""
                        ALTER TABLE produtos
                        ADD COLUMN venda_por_peso INTEGER DEFAULT 0
                    """)
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    print(f"Erro ao adicionar coluna venda_por_peso: {e}")

            # Se a coluna unidade_medida não existir, adiciona
            if 'unidade_medida' not in colunas_nomes:
                try:
                    cursor.execute("""
                        ALTER TABLE produtos
                        ADD COLUMN unidade_medida TEXT DEFAULT 'un'
                    """)
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    print(f"Erro ao adicionar coluna unidade_medida: {e}")

            # Criar tabela de fechamentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fechamentos_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    data_fechamento DATETIME NOT NULL,
                    valor_sistema REAL NOT NULL,
                    valor_informado REAL NOT NULL,
                    diferenca REAL NOT NULL,
                    observacoes TEXT,
                    status TEXT DEFAULT 'Pendente',
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            """)

            # Criar tabela de fechamentos por forma de pagamento
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fechamentos_formas_pagamento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fechamento_id INTEGER NOT NULL,
                    forma_pagamento TEXT NOT NULL,
                    valor_sistema REAL NOT NULL,
                    valor_informado REAL NOT NULL,
                    diferenca REAL NOT NULL,
                    FOREIGN KEY (fechamento_id) REFERENCES fechamentos_caixa (id)
                )
            """)

            # Criar tabela de relação entre vendas e fechamentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vendas_fechamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venda_id INTEGER NOT NULL,
                    fechamento_id INTEGER NOT NULL,
                    FOREIGN KEY (venda_id) REFERENCES vendas (id),
                    FOREIGN KEY (fechamento_id) REFERENCES fechamentos_caixa (id)
                )
            """)

            # Trigger para atualizar data de modificação do fechamento
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS fechamentos_caixa_updated_at 
                AFTER UPDATE ON fechamentos_caixa
                BEGIN
                    UPDATE fechamentos_caixa 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            """)

            # Tabela de retiradas de caixa (uma única definição)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS retiradas_caixa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                aprovador_id INTEGER,
                valor REAL NOT NULL,
                motivo TEXT NOT NULL,
                observacao TEXT,
                origem TEXT NOT NULL DEFAULT 'vendas',
                status TEXT NOT NULL DEFAULT 'pendente',
                data_retirada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_aprovacao TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (aprovador_id) REFERENCES usuarios(id)
            )
            ''')
            
            # Criar trigger para atualização automática do updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS retiradas_caixa_updated_at 
                AFTER UPDATE ON retiradas_caixa
                BEGIN
                    UPDATE retiradas_caixa 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            ''')
            
            self.conn.commit()
            print("Banco de dados inicializado com sucesso!")
            
        except Exception as e:
            print(f"Erro ao inicializar o banco de dados: {str(e)}")
            raise

    def garantir_tabela_retiradas_caixa(self):
        """Garante que a tabela retiradas_caixa exista com a estrutura correta"""
        try:
            cursor = self.conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='retiradas_caixa'
            """)
            
            if not cursor.fetchone():
                print("Criando tabela retiradas_caixa...")
                cursor.execute('''
                    CREATE TABLE retiradas_caixa (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id INTEGER NOT NULL,
                        aprovador_id INTEGER,
                        valor REAL NOT NULL,
                        motivo TEXT NOT NULL,
                        observacao TEXT,
                        origem TEXT NOT NULL DEFAULT 'vendas',
                        status TEXT NOT NULL DEFAULT 'pendente',
                        data_retirada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_aprovacao TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                        FOREIGN KEY (aprovador_id) REFERENCES usuarios (id)
                    )
                ''')
                
                # Criar trigger para atualização automática do updated_at
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS retiradas_caixa_updated_at 
                    AFTER UPDATE ON retiradas_caixa
                    BEGIN
                        UPDATE retiradas_caixa 
                        SET updated_at = datetime('now', 'localtime') 
                        WHERE id = NEW.id;
                    END
                ''')
                
                self.conn.commit()
                print("Tabela retiradas_caixa criada com sucesso!")
                return True
            
            # Verificar estrutura da tabela e adicionar colunas ausentes
            cursor.execute("PRAGMA table_info(retiradas_caixa)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            # Lista de colunas necessárias com suas definições
            colunas_necessarias = {
                'origem': "TEXT NOT NULL DEFAULT 'vendas'",
                'status': "TEXT NOT NULL DEFAULT 'pendente'",
                'aprovador_id': "INTEGER REFERENCES usuarios(id)",
                'data_aprovacao': "TIMESTAMP",
                'motivo': "TEXT NOT NULL DEFAULT 'Retirada de caixa'",
                'observacao': "TEXT",
                'created_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                'updated_at': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            
            for coluna, definicao in colunas_necessarias.items():
                if coluna not in column_names:
                    print(f"Adicionando coluna '{coluna}' à tabela retiradas_caixa...")
                    try:
                        cursor.execute(f"""
                        ALTER TABLE retiradas_caixa
                            ADD COLUMN {coluna} {definicao}
                        """)
                        self.conn.commit()
                        print(f"Coluna '{coluna}' adicionada com sucesso!")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e):
                            print(f"Erro ao adicionar coluna '{coluna}': {e}")
            
            # Verificar se o trigger existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='trigger' AND name='retiradas_caixa_updated_at'
            """)
            
            if not cursor.fetchone():
                print("Criando trigger para updated_at...")
                try:
                    cursor.execute("""
                        CREATE TRIGGER IF NOT EXISTS retiradas_caixa_updated_at 
                        AFTER UPDATE ON retiradas_caixa
                        BEGIN
                            UPDATE retiradas_caixa 
                            SET updated_at = datetime('now', 'localtime') 
                            WHERE id = NEW.id;
                        END
                    """)
                    self.conn.commit()
                    print("Trigger criado com sucesso!")
                except Exception as e:
                    print(f"Erro ao criar trigger: {e}")
            
            return True
            
        except Exception as e:
            print(f"Erro ao verificar/criar tabela retiradas_caixa: {str(e)}")
            self.conn.rollback()
            return False

    def execute(self, sql, params=()):
        """Executa uma instrução SQL com tratamento de erros e retry para evitar 'database is locked'"""
        import time
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            with self._lock:
                try:
                    cursor = self.conn.cursor()
                    # Configura timeout para evitar erros de 'database is locked'
                    cursor.execute("PRAGMA busy_timeout = 30000")  # 30 segundos
                    cursor.execute(sql, params)
                    self.conn.commit()  # Garante que as alterações sejam salvas
                    return cursor
                except sqlite3.OperationalError as e:
                    if 'database is locked' in str(e) and attempt < max_retries - 1:
                        print(f"Erro 'database is locked' na tentativa {attempt+1}. Tentando novamente em {retry_delay} segundos...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Aumenta o tempo de espera exponencialmente
                    else:
                        print(f"Erro ao executar SQL após {attempt+1} tentativas: {e}")
                        raise
                except Exception as e:
                    print(f"Erro ao executar SQL: {e}")
                    raise

    def fetchone(self, sql, params=None, dictionary=False):
        """Executa uma consulta e retorna uma única linha com tratamento de erros e retry"""
        import time
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                with self._lock:
                    cursor = self.conn.cursor()
                    # Configura timeout para evitar erros de 'database is locked'
                    cursor.execute("PRAGMA busy_timeout = 30000")  # 30 segundos
                    if dictionary:
                        cursor.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
                    cursor.execute(sql, params or ())
                    return cursor.fetchone()
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    print(f"Erro 'database is locked' na tentativa {attempt+1} de fetchone. Tentando novamente em {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Aumenta o tempo de espera exponencialmente
                else:
                    print(f"Erro ao executar fetchone após {attempt+1} tentativas: {e}")
                    return None
            except Exception as e:
                print(f"Erro ao executar fetchone: {e}")
                return None

    def fetchall(self, sql, params=(), dictionary=False):
        """Executa uma consulta e retorna todas as linhas com tratamento de erros e retry"""
        import time
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                with self._lock:
                    cursor = self.conn.cursor()
                    # Configura timeout para evitar erros de 'database is locked'
                    cursor.execute("PRAGMA busy_timeout = 30000")  # 30 segundos
                    if dictionary:
                        cursor.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
                    cursor.execute(sql, params)
                    return cursor.fetchall()
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    print(f"Erro 'database is locked' na tentativa {attempt+1} de fetchall. Tentando novamente em {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Aumenta o tempo de espera exponencialmente
                else:
                    print(f"Erro ao executar fetchall após {attempt+1} tentativas: {e}")
                    return []
            except Exception as e:
                print(f"Erro ao executar fetchall: {e}")
                return []

    def get_valor_estoque(self):
        """Calcula o valor total em estoque baseado no preço de custo"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(estoque * preco_custo), 0) as valor_total
                FROM produtos
                WHERE ativo = 1
            """)
            valor = cursor.fetchone()[0]
            print(f"get_valor_estoque(): MT {valor:.2f}")
            return valor

    def get_valor_venda_estoque(self):
        """Calcula o valor total potencial de vendas baseado no preço de venda"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(estoque * preco_venda), 0) as valor_total
                FROM produtos
                WHERE ativo = 1
            """)
            valor = cursor.fetchone()[0]
            print(f"get_valor_venda_estoque(): MT {valor:.2f}")
            return valor
            
    def get_lucro_potencial_estoque(self):
        """Calcula o lucro potencial se todo o estoque for vendido"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(estoque * preco_venda), 0) as valor_total_venda,
                    COALESCE(SUM(estoque * preco_custo), 0) as valor_total_custo
                FROM produtos
                WHERE ativo = 1
            """)
            result = cursor.fetchone()
            lucro_potencial = result[0] - result[1]
            print(f"get_lucro_potencial_estoque(): MT {lucro_potencial:.2f}")
            return max(0, lucro_potencial)  # Garante que não retorne valor negativo

    def close_all_connections(self):
        """Fecha todas as conexões com o banco de dados"""
        import gc
        import time
        
        try:
            if hasattr(self, 'conn') and self.conn:
                # Tenta executar PRAGMA para liberar todas as conexões
                try:
                    cursor = self.conn.cursor()
                    # Desativa o modo WAL temporariamente para facilitar o fechamento
                    cursor.execute("PRAGMA journal_mode = DELETE")
                    # Otimiza o banco de dados
                    cursor.execute("PRAGMA optimize")
                    # Força a sincronização de todos os dados pendentes
                    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    # Libera memória cache
                    cursor.execute("PRAGMA shrink_memory")
                    self.conn.commit()
                except Exception as pragma_error:
                    print(f"Aviso ao executar PRAGMA: {pragma_error}")
                
                # Fecha a conexão
                try:
                    self.conn.close()
                except Exception as close_error:
                    print(f"Erro ao fechar conexão: {close_error}")
                finally:
                    self.conn = None
            
            # Força a coleta de lixo para liberar recursos
            gc.collect()
            
            # Aguarda um momento para garantir que o SO libere o arquivo
            # Aumenta o tempo de espera para garantir que o arquivo seja liberado
            time.sleep(1.0)
            
            return True
        except Exception as e:
            print(f"Erro ao fechar conexões: {e}")
            return False

    def reset_database(self):
        """Reseta o banco de dados para o estado inicial"""
        import time
        import gc
        
        try:
            print("Iniciando reset do banco de dados...")
            
            # 1. Fechar a conexão atual
            print("Fechando conexões atuais...")
            for tentativa_fechar in range(1, 4):  # Tenta fechar até 3 vezes
                if self.close_all_connections():
                    print(f"Conexões fechadas com sucesso na tentativa {tentativa_fechar}.")
                    break
                else:
                    print(f"Falha ao fechar conexões. Tentativa {tentativa_fechar} de 3...")
                    gc.collect()
                    time.sleep(tentativa_fechar * 1.5)
            
            # 2. Remover o arquivo do banco de dados
            db_path = str(self.db_path.absolute())
            backup_path = f"{db_path}.backup_{int(time.time())}"
            
            # Tenta fazer backup do banco atual se existir
            if os.path.exists(db_path):
                try:
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    print(f"Backup do banco atual criado em: {backup_path}")
                except Exception as backup_error:
                    print(f"Aviso: não foi possível criar backup do banco: {backup_error}")
            
            print(f"Removendo arquivo do banco: {db_path}")
            
            max_tentativas = 5
            for tentativa in range(1, max_tentativas + 1):
                if os.path.exists(db_path):
                    try:
                        os.remove(db_path)
                        print(f"Arquivo removido com sucesso na tentativa {tentativa}.")
                        break
                    except PermissionError:
                        print(f"Erro de permissão ao remover o arquivo. Tentativa {tentativa} de {max_tentativas}...")
                        if tentativa < max_tentativas:
                            gc.collect()
                            time.sleep(tentativa * 2)
                        else:
                            print("Falha em todas as tentativas de remover o arquivo.")
                            return False
                    except Exception as e:
                        print(f"Erro ao remover arquivo: {e}")
                        if tentativa < max_tentativas:
                            gc.collect()
                            time.sleep(tentativa * 2)
                        else:
                            return False
                else:
                    print("Arquivo do banco de dados não existe ou já foi removido.")
                    break
            
            # 3. Criar uma nova conexão
            print("Criando nova conexão...")
            time.sleep(2.0)
            
            try:
                self.db_path = Path(db_path)
                self.conn = self._create_connection()
                cursor = self.conn.cursor()
                
                # Configurações iniciais do banco
                cursor.execute("PRAGMA journal_mode = WAL")
                cursor.execute("PRAGMA synchronous = NORMAL")
                cursor.execute("PRAGMA foreign_keys = ON")
                self.conn.commit()
                
            except sqlite3.Error as conn_error:
                print(f"Erro ao criar nova conexão: {conn_error}")
                return False
            
            # 4. Criar o esquema do banco de dados
            print("Criando esquema do banco de dados...")
            
            try:
                # Tabela de usuários primeiro
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        usuario TEXT NOT NULL UNIQUE,
                        senha TEXT NOT NULL,
                        nivel INTEGER NOT NULL DEFAULT 1,
                        ativo INTEGER NOT NULL DEFAULT 1,
                        is_admin INTEGER NOT NULL DEFAULT 0,
                        salario REAL DEFAULT 0,
                        pode_abastecer INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela de categorias
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categorias (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE,
                        descricao TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela de fornecedores
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fornecedores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        telefone TEXT,
                        email TEXT,
                        endereco TEXT,
                        cnpj TEXT,
                        ativo INTEGER NOT NULL DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela de produtos (antes de itens de compra que referenciam produtos)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS produtos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT NOT NULL UNIQUE,
                        nome TEXT NOT NULL,
                        descricao TEXT,
                        preco_custo REAL NOT NULL,
                        preco_venda REAL NOT NULL,
                        estoque REAL NOT NULL DEFAULT 0,
                        estoque_minimo REAL NOT NULL DEFAULT 0,
                        ativo INTEGER NOT NULL DEFAULT 1,
                        venda_por_peso INTEGER DEFAULT 0,
                        unidade_medida TEXT DEFAULT 'un',
                        categoria_id INTEGER,
                        fornecedor_id INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                        FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
                    )
                ''')
                
                # Tabela de compras
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compras (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fornecedor TEXT NOT NULL,
                        valor_total REAL NOT NULL,
                        usuario_id INTEGER NOT NULL,
                        observacoes TEXT,
                        data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                    )
                ''')
                
                # Tabela de itens de compra
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    usuario TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    nivel INTEGER NOT NULL DEFAULT 1,
                    ativo INTEGER NOT NULL DEFAULT 1,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    salario REAL DEFAULT 0,
                    pode_abastecer INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de categorias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    descricao TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de fornecedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fornecedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT,
                    email TEXT,
                    endereco TEXT,
                    cnpj TEXT,
                    ativo INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de produtos (antes de itens de compra que referenciam produtos)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL UNIQUE,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    preco_custo REAL NOT NULL,
                    preco_venda REAL NOT NULL,
                    estoque REAL NOT NULL DEFAULT 0,
                    estoque_minimo REAL NOT NULL DEFAULT 0,
                    ativo INTEGER NOT NULL DEFAULT 1,
                    venda_por_peso INTEGER DEFAULT 0,
                    unidade_medida TEXT DEFAULT 'un',
                    categoria_id INTEGER,
                    fornecedor_id INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
                )
            ''')

            # Tabela de compras
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fornecedor TEXT NOT NULL,
                    valor_total REAL NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    observacoes TEXT,
                    data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            ''')

            # Tabela de itens de compra
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
                )
            ''')

            # Tabela de vendas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    cliente_id INTEGER,
                    data_venda TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    total REAL NOT NULL,
                    forma_pagamento TEXT NOT NULL,
                    valor_recebido REAL,
                    troco REAL,
                    status TEXT DEFAULT 'Concluída',
                    observacoes TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE SET NULL
                )
            ''')

            # Tabela de itens de venda
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS itens_venda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venda_id INTEGER NOT NULL,
                    produto_id INTEGER,
                    produto_nome TEXT NOT NULL,
                    quantidade REAL NOT NULL,
                    preco_unitario REAL NOT NULL,
                    preco_custo_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    peso_kg REAL DEFAULT 0,
                    status TEXT,
                    motivo_alteracao TEXT,
                    alterado_por INTEGER REFERENCES usuarios(id),
                    data_alteracao TIMESTAMP,
                    FOREIGN KEY (venda_id) REFERENCES vendas (id) ON DELETE CASCADE,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                );
                
                CREATE TABLE IF NOT EXISTS contas_pagar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_vencimento DATE NOT NULL,
                    data_pagamento DATE,
                    categoria TEXT NOT NULL,
                    tipo TEXT NOT NULL,  -- 'Compra' ou 'Despesa'
                    status TEXT NOT NULL DEFAULT 'Pendente',  -- 'Pendente' ou 'Pago'
                    observacao TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                );

                CREATE TABLE IF NOT EXISTS movimentacao_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_movimento DATETIME NOT NULL,
                    tipo TEXT NOT NULL,  -- 'Entrada' ou 'Saída'
                    valor REAL NOT NULL,
                    descricao TEXT NOT NULL,
                    categoria TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                );

                CREATE TABLE IF NOT EXISTS categorias_despesa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                );
                
                CREATE TABLE IF NOT EXISTS retiradas_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_retirada DATETIME NOT NULL,
                    valor REAL NOT NULL,
                    descricao TEXT,
                    usuario_id INTEGER,
                    origem TEXT NOT NULL DEFAULT 'vendas',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                );
                
                PRAGMA foreign_keys = ON;
            """)
            
            # 5. Criar o usuário admin
            print("Criando usuário admin...")
            from werkzeug.security import generate_password_hash
            
            # Inserir o usuário admin com as credenciais corretas
            senha_hash = generate_password_hash("842384")
            try:
                cursor.execute("""
                    INSERT INTO usuarios (id, nome, usuario, senha, is_admin, ativo, nivel, salario)
                    VALUES (1, ?, ?, ?, 1, 1, 2, 0)
                    ON CONFLICT(id) DO UPDATE SET
                        nome = excluded.nome,
                        usuario = excluded.usuario,
                        senha = excluded.senha,
                        is_admin = 1,
                        ativo = 1,
                        nivel = 2
                """, ("Administrador", "admin", senha_hash))
                
                # Verificar se o usuário foi criado corretamente
                cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
                admin_user = cursor.fetchone()
                if not admin_user:
                    print("ERRO: Falha ao criar usuário admin")
                    return False
                print(f"Usuário admin criado com sucesso! ID: {admin_user['id']}")
                
            except Exception as e:
                print(f"ERRO ao criar usuário admin: {e}")
                return False
            
            # 6. Inserir fornecedor padrão
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO fornecedores (id, nome, ativo)
                    VALUES (1, 'Fornecedor Padrão', 1)
                ''')
                self.conn.commit()
                print("Fornecedor padrão criado com sucesso!")
            except Exception as e:
                print(f"ERRO ao criar fornecedor padrão: {e}")
                return False
            
            # 7. Criar trigger para updated_at na tabela retiradas_caixa
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS retiradas_caixa_updated_at 
                AFTER UPDATE ON retiradas_caixa
                BEGIN
                    UPDATE retiradas_caixa 
                    SET updated_at = datetime('now', 'localtime') 
                    WHERE id = NEW.id;
                END
            ''')
            
            # 8. Commitar as alterações
            self.conn.commit()
            print("Banco de dados resetado com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao resetar banco de dados: {e}")
            if hasattr(self, 'conn') and self.conn:
                try:
                    self.conn.rollback()
                except:
                    pass
            return False

    def verificar_login(self, usuario, senha):
        """Verifica as credenciais do usuário"""
        try:
            from werkzeug.security import check_password_hash
            
            # Buscar usuário
            result = self.fetchone("""
                SELECT id, nome, usuario, senha, is_admin, ativo, nivel, pode_abastecer
                FROM usuarios 
                WHERE usuario = ? AND ativo = 1
            """, (usuario,))
            
            if result and check_password_hash(result[3], senha):
                return {
                    'id': result[0],
                    'nome': result[1],
                    'usuario': result[2],
                    'is_admin': bool(result[4]),
                    'ativo': bool(result[5]),
                    'nivel': result[6] if len(result) > 6 else 1,
                    'pode_abastecer': bool(result[7]) if len(result) > 7 else False
                }
            return None
            
        except Exception as e:
            print(f"Erro ao verificar login: {str(e)}")
            return None
        
    def migrar_despesas_existentes(self):
        """Migra despesas pagas existentes para a movimentacao_caixa"""
        try:
            self.execute("""
                INSERT INTO movimentacao_caixa (
                    data_movimento,
                    tipo,
                    valor,
                    descricao,
                    categoria
                )
                SELECT 
                    data_vencimento,
                    'Saída',
                    valor,
                    descricao,
                    categoria
                FROM despesas_recorrentes
                WHERE status = 'Pago'
                AND NOT EXISTS (
                    SELECT 1 
                    FROM movimentacao_caixa 
                    WHERE data_movimento = despesas_recorrentes.data_vencimento
                    AND descricao = despesas_recorrentes.descricao
                    AND valor = despesas_recorrentes.valor
                )
            """)
            self.conn.commit()
            return True
        except Exception as e:
            return False

    def get_printer_config(self):
        """Retorna as configurações da impressora"""
        try:
            cursor = self.conn.cursor()
            
            # Usar row_factory para retornar dicionário
            cursor.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
            
            # Buscar a configuração mais recente
            cursor.execute("""
                SELECT * FROM printer_config 
                ORDER BY updated_at DESC, id DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            # Log para debug
            print("Configuração recuperada do banco:", result)
            
            return result
        except Exception as e:
            print(f"Erro ao buscar configurações da impressora: {e}")
            return None

    def save_printer_config(self, config_data):
        """Salva ou atualiza as configurações da impressora"""
        try:
            cursor = self.conn.cursor()
            
            # Garante que todos os campos necessários existam
            required_fields = ['empresa', 'endereco', 'telefone', 'nuit', 'rodape', 'impressora_padrao', 'imprimir_automatico']
            for field in required_fields:
                if field not in config_data:
                    print(f"Campo obrigatório ausente: {field}")
                    return False

            # Converte valores None para string vazia
            for key in config_data:
                if config_data[key] is None:
                    config_data[key] = ''

            # Deletar todas as configurações existentes
            cursor.execute("DELETE FROM printer_config")
            
            # Inserir nova configuração
            try:
                cursor.execute("""
                    INSERT INTO printer_config (
                        empresa,
                        endereco,
                        telefone,
                        nuit,
                        rodape,
                        impressora_padrao,
                        imprimir_automatico,
                        created_at,
                        updated_at
                    ) VALUES (
                        :empresa,
                        :endereco,
                        :telefone,
                        :nuit,
                        :rodape,
                        :impressora_padrao,
                        :imprimir_automatico,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    )
                """, config_data)
                
                # Log para debug
                print(f"Nova configuração inserida com sucesso. ID: {cursor.lastrowid}")
            except Exception as e:
                print(f"Erro ao inserir nova configuração: {str(e)}")
                raise
            
            self.conn.commit()
            print("Configurações salvas com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao salvar configurações da impressora: {str(e)}")
            self.conn.rollback()
            return False

    def update_printer_status(self, printer_name, is_connected):
        """Atualiza o status da impressora padrão"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE printer_config 
                SET impressora_padrao = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id FROM printer_config 
                    ORDER BY id DESC LIMIT 1
                )
            """, (printer_name if is_connected else None,))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False

    def get_auto_print_setting(self):
        """Retorna a configuração de impressão automática"""
        try:
            cursor = self.conn.cursor()
            result = cursor.execute("""
                SELECT imprimir_automatico 
                FROM printer_config 
                ORDER BY id DESC LIMIT 1
            """).fetchone()
            
            return bool(result[0]) if result else False
        except Exception as e:
            return False

    def __dict_factory(self, cursor, row):
        """Converte resultado em dicionário"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def __del__(self):
        try:
            if hasattr(self, 'conn'):
                self.conn.commit()  # Garante que as últimas alterações sejam salvas
                self.conn.close()
        except:
            pass

    def insert_venda(self, venda_data):
        """Insere uma nova venda e retorna seu ID"""
        try:
            cursor = self.conn.cursor()
            from datetime import datetime
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO vendas (
                    usuario_id,
                    total,
                    forma_pagamento,
                    valor_recebido,
                    troco,
                    data_venda
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                venda_data['usuario_id'],
                venda_data['total'],
                venda_data['forma_pagamento'],
                venda_data['valor_recebido'],
                venda_data['troco'],
                data_atual
            ))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            self.conn.rollback()
            raise

    def insert_item_venda(self, item_data):
        """Insere um item de venda"""
        try:
            # Buscar preço de custo do produto
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT preco_custo 
                FROM produtos 
                WHERE id = ?
            """, (item_data['produto_id'],))
            
            produto = cursor.fetchone()
            preco_custo = produto['preco_custo'] if produto else 0
            
            # Inserir item
            cursor.execute("""
                INSERT INTO itens_venda (
                    venda_id,
                    produto_id,
                    quantidade,
                    preco_unitario,
                    preco_custo_unitario,
                    subtotal
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item_data['venda_id'],
                item_data['produto_id'],
                item_data['quantidade'],
                item_data['preco_unitario'],
                preco_custo,
                item_data['subtotal']
            ))
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            raise

    def criar_tabelas(self):
        try:
            self.execute("""
                CREATE TABLE IF NOT EXISTS contas_pagar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_vencimento DATE NOT NULL,
                    data_pagamento DATE,
                    categoria TEXT NOT NULL,
                    tipo TEXT NOT NULL,  -- 'Compra' ou 'Despesa'
                    status TEXT NOT NULL DEFAULT 'Pendente',  -- 'Pendente' ou 'Pago'
                    observacao TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            """)

            self.execute("""
                CREATE TABLE IF NOT EXISTS movimentacao_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_movimento DATETIME NOT NULL,
                    tipo TEXT NOT NULL,  -- 'Entrada' ou 'Saída'
                    valor REAL NOT NULL,
                    descricao TEXT NOT NULL,
                    categoria TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            """)

            # Inserir algumas categorias padrão para contas a pagar
            categorias = [
                ('Fornecedores',),
                ('Aluguel',),
                ('Energia',),
                ('Água',),
                ('Internet',),
                ('Salários',),
                ('Impostos',),
                ('Manutenção',),
                ('Marketing',),
                ('Outros',)
            ]
            
            self.execute("""
                CREATE TABLE IF NOT EXISTS categorias_despesa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                )
            """)

            # Inserir categorias apenas se não existirem
            for categoria in categorias:
                try:
                    self.execute("""
                        INSERT INTO categorias_despesa (nome)
                        VALUES (?)
                    """, categoria)
                except:
                    pass  # Ignora se a categoria já existe

            # Trigger para atualizar movimentação de caixa quando uma venda é inserida
            self.execute("""
                CREATE TRIGGER IF NOT EXISTS after_venda_insert 
                AFTER INSERT ON vendas
                BEGIN
                    INSERT INTO movimentacao_caixa (
                        data_movimento,
                        tipo,
                        valor,
                        descricao,
                        usuario_id
                    )
                    VALUES (
                        NEW.data_venda,
                        'Entrada',
                        NEW.total,
                        'Venda #' || NEW.id,
                        NEW.usuario_id
                    );
                END
            """)

            # Trigger para atualizar movimentação de caixa quando uma conta é paga
            self.execute("""
                CREATE TRIGGER IF NOT EXISTS after_conta_pagar_update 
                AFTER UPDATE OF status ON contas_pagar
                WHEN NEW.status = 'Pago' AND OLD.status = 'Pendente'
                BEGIN
                    INSERT INTO movimentacao_caixa (
                        data_movimento,
                        tipo,
                        valor,
                        descricao,
                        usuario_id
                    )
                    VALUES (
                        NEW.data_pagamento,
                        'Saída',
                        NEW.valor,
                        'Pagamento: ' || NEW.descricao,
                        NEW.usuario_id
                    );
                END
            """)

            self.commit()

        except Exception as e:
            self.rollback()

    def get_formas_pagamento(self):
        """Retorna todas as formas de pagamento ativas"""
        try:
            return self.fetchall("""
                SELECT nome 
                FROM formas_pagamento 
                WHERE ativo = 1
                ORDER BY nome
            """)
        except Exception as e:
            return []

    def get_vendas_periodo(self, data_inicio, data_fim):
        """Retorna vendas de um período específico"""
        try:
            return self.fetchall("""
                SELECT 
                    v.*,
                    u.nome as vendedor
                FROM vendas v
                JOIN usuarios u ON v.usuario_id = u.id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                    AND (v.status IS NULL OR v.status = 'Ativa')
                ORDER BY v.data_venda DESC
            """, (data_inicio, data_fim))
        except Exception as e:
            return []

    def get_total_vendas_hoje(self):
        """Retorna o total de vendas do dia, subtraindo descontos de vendas"""
        try:
            print("\n=== CALCULANDO TOTAL DE VENDAS HOJE ===")
            # Primeiro, pega o total de vendas do dia
            query_vendas = """
                SELECT 
                    COALESCE(SUM(
                        CASE 
                            WHEN status = 'Anulada' THEN 0 
                            ELSE total 
                        END
                    ), 0) as total_vendas,
                    COUNT(*) as total_registros,
                    SUM(CASE WHEN status = 'Anulada' THEN 1 ELSE 0 END) as total_anuladas
                FROM vendas
                WHERE DATE(data_venda) = DATE('now')
            """
            
            # Depois, pega o total de descontos em vendas do dia
            query_descontos = """
                SELECT COALESCE(SUM(valor), 0) as total_descontos
                FROM descontos
                WHERE tipo = 'vendas' 
                AND DATE(data_desconto) = DATE('now')
            """
            
            print(f"Executando query de vendas: {query_vendas}")
            result_vendas = self.fetchone(query_vendas)
            
            print(f"Executando query de descontos: {query_descontos}")
            result_descontos = self.fetchone(query_descontos)
            
            total_vendas = result_vendas['total_vendas'] if result_vendas else 0
            total_descontos = result_descontos['total_descontos'] if result_descontos else 0
            
            # Subtrai os descontos do total de vendas
            total_final = max(0, total_vendas - total_descontos)
            
            print(f"Vendas brutas: MT {total_vendas:.2f}, Descontos: MT {total_descontos:.2f}, Total líquido: MT {total_final:.2f}")
            
            if result_vendas:
                print(f"Detalhes: registros={result_vendas['total_registros']}, anuladas={result_vendas['total_anuladas']}")
            
            return total_final
                
        except Exception as e:
            print(f"Erro ao buscar total de vendas hoje: {e}")
            import traceback
            print(traceback.format_exc())
            return 0

    def get_total_vendas_mes(self):
        """Retorna o total de vendas do mês atual"""
        try:
            query = """
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE total 
                    END
                ), 0) as total
                FROM vendas
                WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
            """
            
            result = self.fetchone(query)
            return result['total'] if result['total'] else 0
        except Exception as e:
            print(f"Erro ao buscar total de vendas do mês: {e}")
            return 0

    def get_vendas_disponiveis_mes(self):
        """Retorna o total de vendas do mês atual MENOS os saques realizados"""
        try:
            # Total de vendas do mês
            query = """
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE total 
                    END
                ), 0) as total
                FROM vendas
                WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
            """
            result = self.fetchone(query)
            return result['total'] if result and 'total' in result else 0
        except Exception as e:
            print(f"Erro ao calcular vendas disponíveis do mês: {e}")
            return 0

    def get_lucro_total(self):
        """Retorna o lucro total (vendas - custo)"""
        try:
            # Verificar se a coluna status existe
            colunas = self.fetchall("PRAGMA table_info(vendas)")
            tem_status = any(col['name'] == 'status' for col in colunas)
            
            # Ajustar a query baseado na existência da coluna status
            where_status = "AND (v.status IS NULL OR v.status = 'Ativa')" if tem_status else ""
            
            result = self.fetchone(f"""
                SELECT 
                    COALESCE(SUM(iv.subtotal - (iv.preco_custo_unitario * iv.quantidade)), 0) as lucro
                FROM vendas v
                JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE 1=1 {where_status}
            """)
            return result['lucro'] if result else 0
        except Exception as e:
            return 0

    def get_lucro_mes(self):
        """Retorna o lucro do mês atual"""
        try:
            query = """
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN v.status = 'Anulada' THEN 0 
                        ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                    END
                ), 0) as lucro
                FROM vendas v
                JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE strftime('%Y-%m', v.data_venda) = strftime('%Y-%m', 'now')
            """
            
            result = self.fetchone(query)
            return result['lucro'] if result['lucro'] else 0
        except Exception as e:
            print(f"Erro ao calcular lucro do mês: {e}")
            return 0

    def get_lucro_disponivel_mes(self):
        """Retorna o lucro do mês atual MENOS os saques de lucro realizados"""
        try:
            # Calcular lucro bruto do mês
            query_lucro = """
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN v.status = 'Anulada' THEN 0 
                        ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                    END
                ), 0) as lucro
                FROM vendas v
                JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE strftime('%Y-%m', v.data_venda) = strftime('%Y-%m', 'now')
            """
            lucro_result = self.fetchone(query_lucro)
            lucro_bruto = float(lucro_result[0]) if lucro_result and lucro_result[0] is not None else 0.0
            
            # Buscar saques do mês
            mes_atual = datetime.now().strftime('%Y-%m')
            query_saques = """
                SELECT COALESCE(SUM(valor), 0) as total_saques
                FROM retiradas_caixa
                WHERE strftime('%Y-%m', data_retirada) = ?
                AND tipo = 'Saque de Lucro'
            """
            saques_result = self.fetchone(query_saques, (mes_atual,))
            total_saques = float(saques_result[0]) if saques_result and saques_result[0] is not None else 0.0
            
            # Calcular lucro disponível
            lucro_disponivel = max(0, lucro_bruto - total_saques)
            
            print(f"[DEBUG] Lucro bruto do mês: MT {lucro_bruto:.2f}")
            print(f"[DEBUG] Saques de lucro do mês: MT {total_saques:.2f}")
            print(f"[DEBUG] Lucro disponível: MT {lucro_disponivel:.2f}")
            
            return lucro_disponivel
        except Exception as e:
            print(f"Erro ao calcular lucro disponível do mês: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def get_descontos_hoje(self, data=None):
        """Retorna os descontos do dia atual ou da data fornecida"""
        try:
            from datetime import datetime
            
            # Usar a data fornecida ou a data atual
            data_consulta = data if data else datetime.now().strftime('%Y-%m-%d')
            
            query = """
                SELECT 
                    COALESCE(SUM(CASE WHEN tipo = 'lucro' THEN valor ELSE 0 END), 0) as descontos_lucro,
                    COALESCE(SUM(CASE WHEN tipo = 'vendas' THEN valor ELSE 0 END), 0) as descontos_vendas,
                    COUNT(*) as total_descontos
                FROM descontos
                WHERE DATE(data_desconto) = ?
            """
            
            result = self.fetchone(query, (data_consulta,))
            
            if result:
                return {
                    'descontos_lucro': float(result['descontos_lucro'] or 0),
                    'descontos_vendas': float(result['descontos_vendas'] or 0),
                    'total_descontos': result['total_descontos']
                }
            return {'descontos_lucro': 0, 'descontos_vendas': 0, 'total_descontos': 0}
            
        except Exception as e:
            print(f"Erro ao buscar descontos: {e}")
            return {'descontos_lucro': 0, 'descontos_vendas': 0, 'total_descontos': 0}

    def get_lucro_dia(self, data=None):
        """Retorna o lucro do dia atual ou da data fornecida"""
        try:
            print("\n=== INÍCIO CÁLCULO LUCRO DIA ===")
            
            # Usar a data fornecida ou a data atual
            from datetime import datetime
            data_atual = data if data else datetime.now().strftime('%Y-%m-%d')
            
            # Buscar descontos do dia
            descontos = self.get_descontos_hoje(data_atual)
            print(f"[DEBUG] Descontos do dia: {descontos}")
            
            # Verificar se há vendas hoje
            query_vendas_hoje = f"""
                SELECT 
                    COUNT(*) as total,
                    COALESCE(SUM(total), 0) as valor_total,
                    SUM(CASE WHEN status = 'Anulada' THEN 1 ELSE 0 END) as total_anuladas
                FROM vendas 
                WHERE DATE(data_venda) = '{data_atual}'
            """
            vendas_hoje = self.fetchone(query_vendas_hoje)
            print(f"[DEBUG] Consulta vendas hoje: {query_vendas_hoje}")
            print(f"[DEBUG] Resultado vendas hoje: {dict(vendas_hoje) if vendas_hoje else 'Nenhuma venda'}")
            
            # Se houver descontos em vendas, ajustar o valor total
            if descontos['descontos_vendas'] > 0:
                print(f"[DEBUG] Aplicando desconto de vendas: MT {descontos['descontos_vendas']:.2f}")
                if vendas_hoje and 'valor_total' in vendas_hoje:
                    vendas_hoje['valor_total'] = max(0, vendas_hoje['valor_total'] - descontos['descontos_vendas'])
                    print(f"[DEBUG] Valor total após desconto de vendas: MT {vendas_hoje['valor_total']:.2f}")
            
            # Query detalhada para depuração
            query_detalhada = f"""
                SELECT 
                    v.id as venda_id,
                    v.data_venda,
                    v.total as total_venda,
                    v.status,
                    COUNT(iv.id) as total_itens,
                    SUM(iv.subtotal) as subtotal_itens,
                    SUM(iv.preco_custo_unitario * iv.quantidade) as custo_total,
                    SUM(iv.subtotal - (iv.preco_custo_unitario * iv.quantidade)) as lucro_venda
                FROM vendas v
                LEFT JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) = '{data_atual}'
                GROUP BY v.id
                ORDER BY v.data_venda DESC
            """
            vendas_detalhadas = self.fetchall(query_detalhada)
            print(f"\n[DEBUG] Detalhes das vendas de hoje (primeiras 5):")
            if not vendas_detalhadas:
                print("  [AVISO] Nenhuma venda encontrada com itens para a data atual")
                # Verificar se há vendas sem itens
                query_vendas_sem_itens = f"""
                    SELECT id, data_venda, total, status 
                    FROM vendas 
                    WHERE DATE(data_venda) = '{data_atual}'
                    AND id NOT IN (SELECT DISTINCT venda_id FROM itens_venda)
                """
                vendas_sem_itens = self.fetchall(query_vendas_sem_itens)
                if vendas_sem_itens:
                    print(f"  [AVISO] Encontradas {len(vendas_sem_itens)} vendas sem itens:")
                    for v in vendas_sem_itens[:5]:
                        print(f"    - Venda ID: {v['id']}, Total: {v['total']}, Status: {v['status']}")
            else:
                for i, venda in enumerate(vendas_detalhadas[:5]):
                    print(f"  Venda {i+1}: {dict(venda)}")
            
            # Query para calcular o lucro do dia - versão simplificada
            query = f"""
                WITH vendas_do_dia AS (
                    SELECT v.*, 
                           COUNT(iv.id) as qtd_itens
                    FROM vendas v
                    LEFT JOIN itens_venda iv ON v.id = iv.venda_id
                    WHERE DATE(v.data_venda) = '{data_atual}'
                    AND (v.status IS NULL OR v.status != 'Anulada')
                    GROUP BY v.id
                )
                SELECT 
                    -- Lucro total (soma dos lucros de todos os itens)
                    COALESCE(SUM(
                        (SELECT COALESCE(SUM(iv2.subtotal - (iv2.preco_custo_unitario * iv2.quantidade)), 0)
                         FROM itens_venda iv2 
                         WHERE iv2.venda_id = v.id)
                    ), 0) as lucro,
                    
                    -- Total de vendas
                    COUNT(DISTINCT v.id) as total_vendas,
                    
                    -- Vendas anuladas
                    SUM(CASE WHEN v.status = 'Anulada' THEN 1 ELSE 0 END) as vendas_anuladas,
                    
                    -- Total de itens
                    (SELECT COUNT(*) FROM itens_venda iv 
                     JOIN vendas v2 ON iv.venda_id = v2.id 
                     WHERE DATE(v2.data_venda) = '{data_atual}') as total_itens,
                    
                    -- Soma dos totais para verificação
                    SUM(v.total) as soma_totais_vendas,
                    
                    -- Verificar se há registros
                    (SELECT COUNT(*) FROM vendas_do_dia) as total_vendas_dia,
                    
                    -- Verificar se há vendas sem itens
                    (SELECT COUNT(*) FROM vendas_do_dia WHERE qtd_itens = 0) as vendas_sem_itens
                FROM vendas_do_dia v"""
            
            print(f"\n[DEBUG] Executando query de lucro: {query}")
            
            # Executar a query e obter resultados
            resultado = self.fetchone(query)
            
            if not resultado:
                print("[ERRO] Nenhum resultado retornado pela consulta de lucro")
                return 0.0
                
            # Convert sqlite3.Row to dict with default values
            resultado_dict = dict(resultado)
            lucro = resultado_dict.get('lucro', 0) or 0
            total_vendas = resultado_dict.get('total_vendas', 0) or 0
            vendas_anuladas = resultado_dict.get('vendas_anuladas', 0) or 0
            total_itens = resultado_dict.get('total_itens', 0) or 0
            vendas_sem_itens = resultado_dict.get('vendas_sem_itens', 0) or 0
            
            # Log detalhado
            print("\n[DEBUG] === RESUMO DO CÁLCULO DE LUCRO ===")
            print(f"[DEBUG] Total de vendas no dia: {total_vendas}")
            print(f"[DEBUG] Vendas anuladas: {vendas_anuladas}")
            print(f"[DEBUG] Vendas sem itens: {vendas_sem_itens}")
            print(f"[DEBUG] Total de itens vendidos: {total_itens}")
            print(f"[DEBUG] Lucro calculado: MT {lucro:.2f}")
            
            # Se houver vendas mas o lucro for zero, verificar possíveis problemas
            if total_vendas > 0 and lucro == 0:
                print("\n[AVISO] Lucro zerado detectado com vendas existentes. Verificando possíveis problemas...")
                
                # Verificar se há itens com custo zerado
                query_custo_zerado = f"""
                    SELECT COUNT(*) as total
                    FROM itens_venda iv
                    JOIN vendas v ON iv.venda_id = v.id
                    WHERE DATE(v.data_venda) = '{data_atual}'
                    AND (iv.preco_custo_unitario IS NULL OR iv.preco_custo_unitario = 0)
                """
                custo_zerado = self.fetchone(query_custo_zerado)
                if custo_zerado and custo_zerado[0] > 0:
                    print(f"  - Encontrados {custo_zerado[0]} itens com custo zerado/nulo")
                
                # Verificar se há itens sem preço de venda
                query_sem_preco = f"""
                    SELECT COUNT(*) as total
                    FROM itens_venda iv
                    JOIN vendas v ON iv.venda_id = v.id
                    WHERE DATE(v.data_venda) = '{data_atual}'
                    AND (iv.subtotal IS NULL OR iv.subtotal = 0)
                """
                sem_preco = self.fetchone(query_sem_preco)
                if sem_preco and sem_preco[0] > 0:
                    print(f"  - Encontrados {sem_preco[0]} itens sem preço de venda")
            
            print("[DEBUG] =================================\n")
            
            # Aplicar descontos de lucro
            if descontos['descontos_lucro'] > 0:
                print(f"[DEBUG] Aplicando desconto de lucro: MT {descontos['descontos_lucro']:.2f}")
                lucro_antes_desconto = lucro
                lucro = max(0, lucro - descontos['descontos_lucro'])
                print(f"[DEBUG] Lucro antes do desconto: MT {lucro_antes_desconto:.2f}")
                print(f"[DEBUG] Lucro após desconto: MT {lucro:.2f}")
            
            # Verificar se há saques hoje que afetam o lucro
            query_saques = """
                SELECT 
                    SUM(valor) as total_saques,
                    COUNT(*) as qtd_saques
                FROM retiradas_caixa
                WHERE DATE(data_retirada) = ?
            """
            saques_hoje = self.fetchone(query_saques, (data_atual,))
            print(f"[DEBUG] Saques de hoje: {dict(saques_hoje) if saques_hoje else 'Nenhum saque'}")
            
            # Ajustar lucro considerando saques
            if saques_hoje and saques_hoje['total_saques']:
                total_saques = float(saques_hoje['total_saques'] or 0)
                print(f"[INFO] Encontrados {saques_hoje['qtd_saques']} saques hoje totalizando MT {total_saques:.2f}")
                lucro_antes_saques = lucro
                lucro = max(0, lucro - total_saques)
                print(f"[INFO] Lucro antes de considerar saques: MT {lucro_antes_saques:.2f}")
                print(f"[INFO] Lucro após saques: MT {lucro:.2f}")
            
            # Verificar se há vendas com status inesperado
            query_status = """
                SELECT status, COUNT(*) as total
                FROM vendas 
                WHERE DATE(data_venda) = ?
                GROUP BY status
            """
            status_vendas = self.fetchall(query_status, (data_atual,))
            print(f"[DEBUG] Contagem de vendas por status: {dict(status_vendas) if status_vendas else 'Nenhuma venda'}")
            
            # Log resumido dos descontos
            if descontos['total_descontos'] > 0:
                print("\n=== RESUMO DE DESCONTOS ===")
                print(f"Total de descontos: {descontos['total_descontos']}")
                print(f"- Descontos em vendas: MT {descontos['descontos_vendas']:.2f}")
                print(f"- Descontos em lucro: MT {descontos['descontos_lucro']:.2f}")
            
            print(f"\n=== FIM CÁLCULO LUCRO DIA ===")
            print(f"Lucro bruto: MT {lucro + descontos['descontos_lucro'] + (float(saques_hoje['total_saques']) if saques_hoje and saques_hoje['total_saques'] else 0):.2f}")
            if descontos['descontos_lucro'] > 0:
                print(f"(-) Descontos em lucro: MT {descontos['descontos_lucro']:.2f}")
            if saques_hoje and saques_hoje['total_saques']:
                print(f"(-) Saques: MT {float(saques_hoje['total_saques']):.2f}")
            print(f"Lucro líquido final: MT {lucro:.2f}\n")
            
            return lucro
            
        except Exception as e:
            print(f"[ERRO] Erro ao calcular lucro do dia: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0.0

    def get_vendas_nao_fechadas(self, usuario_id):
        """Retorna vendas não incluídas em nenhum fechamento"""
        try:
            return self.fetchall("""
                SELECT 
                    forma_pagamento,
                    COUNT(*) as quantidade,
                    SUM(total) as total
                FROM vendas 
                WHERE usuario_id = ?
                AND DATE(data_venda) = DATE('now')
                AND id NOT IN (
                    SELECT venda_id FROM vendas_fechamentos
                    WHERE venda_id IS NOT NULL
                )
                GROUP BY forma_pagamento
            """, (usuario_id,))
        except Exception as e:
            print(f"Erro ao buscar vendas não fechadas: {e}")
            return []

    def get_fechamentos_usuario(self, usuario_id):
        """Retorna os fechamentos de caixa do usuário"""
        try:
            return self.fetchall("""
                SELECT 
                    f.*,
                    u.nome as usuario_nome,
                    (
                        SELECT COUNT(*)
                        FROM vendas_fechamentos vf
                        WHERE vf.fechamento_id = f.id
                    ) as total_vendas
                FROM fechamentos_caixa f
                JOIN usuarios u ON f.usuario_id = u.id
                WHERE f.usuario_id = ?
                ORDER BY f.data_fechamento DESC
            """, (usuario_id,))
        except Exception as e:
            print(f"Erro ao buscar fechamentos: {e}")
            return []

    def get_detalhes_fechamento(self, fechamento_id):
        """Retorna os detalhes de um fechamento específico"""
        try:
            return {
                'fechamento': self.fetchone("""
                    SELECT 
                        f.*,
                        u.nome as usuario_nome
                    FROM fechamentos_caixa f
                    JOIN usuarios u ON f.usuario_id = u.id
                    WHERE f.id = ?
                """, (fechamento_id,)),
                
                'formas_pagamento': self.fetchall("""
                    SELECT *
                    FROM fechamentos_formas_pagamento
                    WHERE fechamento_id = ?
                """, (fechamento_id,)),
                
                'vendas': self.fetchall("""
                    SELECT 
                        v.*,
                        GROUP_CONCAT(
                            p.nome || ' (' || iv.quantidade || 'x - MT ' || 
                            printf('%.2f', iv.preco_unitario) || ')'
                        ) as itens
                    FROM vendas v
                    JOIN vendas_fechamentos vf ON v.id = vf.venda_id
                    JOIN itens_venda iv ON v.id = iv.venda_id
                    JOIN produtos p ON iv.produto_id = p.id
                    WHERE vf.fechamento_id = ?
                    GROUP BY v.id
                """, (fechamento_id,))
            }
        except Exception as e:
            print(f"Erro ao buscar detalhes do fechamento: {e}")
            return None

    def get_total_vendas_congelador_hoje(self):
        """Retorna o total de vendas do congelador para hoje"""
        try:
            result = self.fetchone("""
                SELECT COALESCE(SUM(v.total), 0) as total
                FROM vendas v
                JOIN itens_venda iv ON v.id = iv.venda_id
                JOIN produtos p ON iv.produto_id = p.id
                WHERE DATE(v.data_venda) = '{data_atual}'
                AND p.venda_por_peso = 1
                AND (v.status IS NULL OR v.status != 'Anulada')
            """)
            return result['total'] if result else 0
        except Exception as e:
            print(f"Erro ao calcular vendas do congelador: {e}")
            return 0

    def get_valor_potencial_vendas(self):
        """Retorna o valor potencial total se todo o estoque for vendido"""
        try:
            result = self.fetchone("""
                SELECT COALESCE(SUM(estoque * preco_venda), 0) as total
                FROM produtos
                WHERE ativo = 1
            """)
            return result['total'] if result else 0
        except Exception as e:
            print(f"Erro ao calcular valor potencial de vendas: {e}")
            return 0

    def corrigir_estoque_vendas_anuladas(self):
        """Corrige o estoque de vendas anuladas que têm origem 'divida_quitada'"""
        try:
            print("=== Iniciando correção de estoque ===")
            
            # Buscar vendas anuladas com origem 'divida_quitada'
            vendas_anuladas = self.fetchall("""
                SELECT id FROM vendas 
                WHERE status = 'Anulada' AND origem = 'divida_quitada'
            """)
            
            print(f"Encontradas {len(vendas_anuladas)} vendas anuladas de dívidas quitadas")
            
            for venda in vendas_anuladas:
                # Buscar itens da venda
                itens = self.fetchall("""
                    SELECT produto_id, quantidade 
                    FROM itens_venda 
                    WHERE venda_id = ?
                """, (venda['id'],))
                
                print(f"Venda {venda['id']}: {len(itens)} itens")
                
                # Devolver estoque para cada item
                for item in itens:
                    self.execute("""
                        UPDATE produtos 
                        SET estoque = estoque + ? 
                        WHERE id = ?
                    """, (item['quantidade'], item['produto_id']))
                    
                    print(f"  - Produto {item['produto_id']}: +{item['quantidade']} unidades")
            
            self.conn.commit()
            print("=== Correção de estoque concluída ===")
            return True
            
        except Exception as e:
            print(f"Erro ao corrigir estoque: {e}")
            self.conn.rollback()
            return False

    def recreate_database(self):
        """Recria o banco de dados do zero"""
        try:
            print("\n=== Recriando banco de dados ===")
            
            # Fechar conexão existente
            if self.conn:
                self.conn.close()
            
            # Remover arquivo do banco
            import os
            if os.path.exists(str(self.db_path)):
                os.remove(str(self.db_path))
                print("Arquivo do banco removido")
            
            # Recriar conexão e inicializar banco
            self.conn = self._create_connection()
            self._init_database()
            print("Banco de dados recriado com sucesso!")
            print("=== Fim da recriação do banco ===\n")
            
        except Exception as error:
            print(f"Erro ao recriar banco: {error}")
            raise error

    def run_schema_migrations(self):
        """Executa novamente as migrações/garante o esquema completo.

        Use após restaurar um backup antigo para garantir que todas as
        tabelas, colunas e triggers estejam presentes.
        """
        try:
            self._init_database()
            return True
        except Exception:
            return False

    def ensure_abastecimento_schema(self):
        """Garante as estruturas mínimas usadas pelo Abastecimento.

        - Tabela fornecedores (com registro padrão)
        - Coluna produtos.fornecedor_id
        - Tabelas compras e compra_itens
        """
        try:
            cursor = self.conn.cursor()

            # Fornecedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fornecedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT,
                    email TEXT,
                    endereco TEXT,
                    cnpj TEXT,
                    ativo INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                INSERT OR IGNORE INTO fornecedores (id, nome, ativo)
                VALUES (1, 'Fornecedor Padrão', 1)
            ''')

            # Coluna fornecedor_id em produtos
            cursor.execute("PRAGMA table_info(produtos)")
            cols = [c[1] for c in cursor.fetchall()]
            if 'fornecedor_id' not in cols:
                try:
                    cursor.execute('''
                        ALTER TABLE produtos
                        ADD COLUMN fornecedor_id INTEGER DEFAULT 1 REFERENCES fornecedores(id)
                    ''')
                except Exception:
                    pass

            # Tabela compras
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fornecedor TEXT NOT NULL,
                    valor_total REAL NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    observacoes TEXT,
                    data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            ''')

            # Tabela compra_itens
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
                )
            ''')

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao garantir schema de abastecimento: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return False

    def get_vendas_hoje(self):
        """Retorna todas as vendas do dia atual para depuração"""
        try:
            query = """
                SELECT 
                    v.id as venda_id,
                    v.data_venda,
                    v.status,
                    v.total,
                    v.forma_pagamento,
                    iv.id as item_id,
                    iv.produto_id,
                    iv.quantidade,
                    iv.preco_unitario,
                    iv.subtotal,
                    iv.preco_custo_unitario,
                    (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade)) as lucro_item
                FROM vendas v
                LEFT JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE DATE(v.data_venda) = '{data_atual}'
                ORDER BY v.data_venda DESC
            """
            
            vendas = self.fetchall(query, dictionary=True)
            print("\n=== VENDAS DE HOJE ===")
            print(f"Total de registros: {len(vendas)}")
            
            for venda in vendas[:5]:  # Mostra apenas as 5 primeiras para não poluir o log
                print(f"\nVenda ID: {venda['venda_id']}")
                print(f"Data: {venda['data_venda']}")
                print(f"Status: {venda['status']}")
                print(f"Total: {venda['total']}")
                print(f"Forma de Pagamento: {venda['forma_pagamento']}")
                print(f"Item ID: {venda['item_id']}")
                print(f"Produto ID: {venda['produto_id']}")
                print(f"Quantidade: {venda['quantidade']}")
                print(f"Preço Unitário: {venda['preco_unitario']}")
                print(f"Subtotal: {venda['subtotal']}")
                print(f"Custo Unitário: {venda['preco_custo_unitario']}")
                print(f"Lucro do Item: {venda['lucro_item']}")
            
            if len(vendas) > 5:
                print(f"\n... e mais {len(vendas) - 5} registros")
            
            return vendas
            
        except Exception as e:
            print(f"Erro ao buscar vendas de hoje: {e}")
            import traceback
            traceback.print_exc()
            return []

    def verificar_estrutura_tabelas(self):
        """Verifica a estrutura das tabelas para depuração"""
        try:
            print("\n=== Verificando estrutura das tabelas ===")
            
            # Verificar estrutura da tabela vendas
            print("Estrutura da tabela vendas:")
            result = self.fetchall("PRAGMA table_info(vendas)")
            for col in result:
                print(f"  - {col['name']}: {col['type']}")
            
            # Verificar estrutura da tabela itens_venda
            print("\nEstrutura da tabela itens_venda:")
            result = self.fetchall("PRAGMA table_info(itens_venda)")
            for col in result:
                print(f"  - {col['name']}: {col['type']}")
            
            # Verificar estrutura da tabela produtos
            print("\nEstrutura da tabela produtos:")
            result = self.fetchall("PRAGMA table_info(produtos)")
            for col in result:
                print(f"  - {col['name']}: {col['type']}")
            
            print("\n=== Fim da verificação de estrutura ===")
            
        except Exception as e:
            print(f"Erro ao verificar estrutura das tabelas: {e}")
            import traceback
            traceback.print_exc()

    def verificar_estrutura_retiradas_caixa(self):
        """Verifica a estrutura da tabela retiradas_caixa"""
        try:
            print("\n=== Estrutura da tabela retiradas_caixa ===")
            result = self.fetchall("PRAGMA table_info(retiradas_caixa)")
            
            if not result:
                print("A tabela retiradas_caixa não existe.")
                return False
                
            print("\nColunas da tabela retiradas_caixa:")
            for col in result:
                print(f"  - {col['name']}: {col['type']} {'PRIMARY KEY' if col['pk'] > 0 else ''}")
            
            return True
            
        except Exception as e:
            print(f"Erro ao verificar estrutura da tabela retiradas_caixa: {e}")
            import traceback
            traceback.print_exc()
            return False

    def adicionar_compra(self, fornecedor, itens, usuario_id, observacoes=None):
        """
        Adiciona uma nova compra ao banco de dados
        
        Args:
            fornecedor (str): Nome do fornecedor
            itens (list): Lista de dicionários contendo 'produto_id', 'produto_nome', 'quantidade', 
                         'preco_unitario', 'preco_venda', 'lucro_unitario', 'lucro_total'
            usuario_id (int): ID do usuário que está registrando a compra
            observacoes (str, optional): Observações sobre a compra
            
        Returns:
            int: ID da compra criada ou None em caso de erro
        """
        try:
            cursor = self.conn.cursor()
            
            # Calcular valor total da compra
            valor_total = sum(item['preco_unitario'] * item['quantidade'] for item in itens)
            
            # Inserir a compra
            cursor.execute('''
                INSERT INTO compras (fornecedor, valor_total, usuario_id, observacoes)
                VALUES (?, ?, ?, ?)
            ''', (fornecedor, valor_total, usuario_id, observacoes))
            
            compra_id = cursor.lastrowid
            
            # Inserir os itens da compra
            for item in itens:
                cursor.execute('''
                    INSERT INTO compra_itens 
                    (compra_id, produto_id, produto_nome, quantidade, preco_unitario, preco_venda, lucro_unitario, lucro_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    compra_id,
                    item.get('produto_id'),
                    item['produto_nome'],
                    item['quantidade'],
                    item['preco_unitario'],
                    item['preco_venda'],
                    item['lucro_unitario'],
                    item['lucro_total']
                ))
            
            self.conn.commit()
            return compra_id
            
        except Exception as e:
            print(f"Erro ao adicionar compra: {e}")
            self.conn.rollback()
            return None
    
    def obter_compras_por_data(self, data_inicio, data_fim=None):
        """
        Obtém as compras dentro de um período
        
        Args:
            data_inicio (str): Data de início no formato 'YYYY-MM-DD'
            data_fim (str, optional): Data de fim no formato 'YYYY-MM-DD'. Se não informado, usa a data atual
            
        Returns:
            list: Lista de dicionários com as compras encontradas
        """
        try:
            cursor = self.conn.cursor()
            
            if data_fim is None:
                data_fim = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT c.*, u.nome as responsavel 
                FROM compras c
                JOIN usuarios u ON c.usuario_id = u.id
                WHERE date(c.data_compra) BETWEEN date(?) AND date(?)
                ORDER BY c.data_compra DESC
            ''', (data_inicio, data_fim))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"Erro ao obter compras: {e}")
            return []
    
    def obter_itens_compra(self, compra_id):
        """
        Obtém os itens de uma compra específica
        
        Args:
            compra_id (int): ID da compra
            
        Returns:
            list: Lista de dicionários com os itens da compra
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT * FROM compra_itens 
                WHERE compra_id = ?
                ORDER BY id
            ''', (compra_id,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"Erro ao obter itens da compra: {e}")
            return []

    def criar_tabela_compra_itens(self):
        """Cria a tabela de itens da compra"""
        try:
            cursor = self.conn.cursor()
            
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
            )
            ''')
            
            self.conn.commit()
            print("Tabela compra_itens criada com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao criar tabela compra_itens: {e}")
            return False

    def obter_categorias(self):
        """
        Retorna todas as categorias cadastradas no sistema
        
        Returns:
            list: Lista de dicionários com as categorias
        """
        return self.fetchall("""
            SELECT id, nome, descricao 
            FROM categorias 
            ORDER BY nome
        """, dictionary=True)

    def buscar_produto_por_codigo_ou_nome(self, termo):
        """
        Busca um produto por código ou nome
        
        Args:
            termo (str): Código ou nome do produto a ser buscado
            
        Returns:
            dict or None: Dicionário com os dados do produto ou None se não encontrado
        """
        if not termo:
            return None
            
        # Remove espaços extras e converte para minúsculas para busca case-insensitive
        termo = f"%{termo.strip().lower()}%"
        
        return self.fetchone("""
            SELECT p.*, c.nome as categoria_nome
            FROM produtos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE (LOWER(p.codigo) LIKE ? OR LOWER(p.nome) LIKE ?) 
            AND p.ativo = 1
            LIMIT 1
        """, (termo, termo), dictionary=True)

    def verificar_consistencia_saques(self):
        """
        Verifica a consistência entre os totais de vendas/lucro e os saques registrados.
        Retorna um dicionário com os resultados da verificação.
        """
        try:
            # Iniciar transação
            self.conn.execute("BEGIN TRANSACTION")
            
            # 1. Verificar consistência de vendas
            vendas_saques = self.fetchone("""
                SELECT 
                    (SELECT COALESCE(SUM(total), 0) 
                     FROM vendas 
                     WHERE status = 'Concluída' 
                     AND DATE(data_venda) = DATE('now')) as total_vendas,
                    
                    (SELECT COALESCE(SUM(valor), 0) 
                     FROM retiradas_caixa 
                     WHERE origem = 'vendas' 
                     AND DATE(data_retirada) = DATE('now')) as total_saques_vendas
            """)
            
            # 2. Verificar consistência de lucro
            lucro_saques = self.fetchone("""
                SELECT 
                    (SELECT COALESCE(SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                        END
                    ), 0)
                    FROM vendas v
                    JOIN itens_venda iv ON v.id = iv.venda_id
                    WHERE DATE(v.data_venda) = '{data_atual}') as total_lucro,
                    
                    (SELECT COALESCE(SUM(valor), 0) 
                     FROM retiradas_caixa 
                     WHERE origem = 'lucro' 
                     AND DATE(data_retirada) = DATE('now')) as total_saques_lucro
            """)
            
            # 3. Verificar saques pendentes
            saques_pendentes = self.fetchone("""
                SELECT COUNT(*) as total, 
                       COALESCE(SUM(valor), 0) as valor_total
                FROM retiradas_caixa
                WHERE status = 'pendente'
                AND DATE(data_retirada) = DATE('now')
            """)
            
            # 4. Calcular saldos disponíveis
            saldo_vendas = vendas_saques['total_vendas'] - vendas_saques['total_saques_vendas']
            saldo_lucro = lucro_saques['total_lucro'] - lucro_saques['total_saques_lucro']
            
            # 5. Verificar se há valores negativos (inconsistência)
            consistente = True
            problemas = []
            
            if saldo_vendas < 0:
                consistente = False
                problemas.append(f"Saldo de vendas negativo: MT {saldo_vendas:,.2f}")
                
            if saldo_lucro < 0:
                consistente = False
                problemas.append(f"Saldo de lucro negativo: MT {saldo_lucro:,.2f}")
            
            # Commit da transação
            self.conn.commit()
            
            return {
                'consistente': consistente,
                'problemas': problemas,
                'vendas': {
                    'total': vendas_saques['total_vendas'],
                    'saques': vendas_saques['total_saques_vendas'],
                    'saldo_disponivel': max(0, saldo_vendas)
                },
                'lucro': {
                    'total': lucro_saques['total_lucro'],
                    'saques': lucro_saques['total_saques_lucro'],
                    'saldo_disponivel': max(0, saldo_lucro)
                },
                'saques_pendentes': {
                    'quantidade': saques_pendentes['total'],
                    'valor_total': saques_pendentes['valor_total']
                },
                'data_verificacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Erro ao verificar consistência: {str(e)}")
            
    def registrar_fechamento(self, dados_fechamento):
        """
        Registra um novo fechamento de caixa no banco de dados.
        
        Args:
            dados_fechamento (dict): Dicionário contendo os dados do fechamento
                - usuario_id (int): ID do usuário que está realizando o fechamento
                - valor_sistema (float): Valor total calculado pelo sistema
                - valor_informado (float): Valor informado pelo usuário
                - diferenca (float): Diferença entre o valor informado e o valor do sistema
                - observacoes (str, optional): Observações sobre o fechamento
                - formas_pagamento (list): Lista de dicionários com os dados por forma de pagamento
                    - forma (str): Nome da forma de pagamento
                    - valor_sistema (float): Valor calculado pelo sistema
                    - valor_informado (float): Valor informado pelo usuário
                    - diferenca (float): Diferença entre os valores
                    - quantidade_vendas (int): Quantidade de vendas com esta forma de pagamento
        
        Returns:
            int: ID do fechamento registrado ou None em caso de erro
        """
        try:
            with self.conn:
                cursor = self.conn.cursor()
                
                # Inserir o fechamento principal
                cursor.execute("""
                    INSERT INTO fechamentos_caixa (
                        usuario_id, 
                        data_fechamento, 
                        valor_sistema, 
                        valor_informado, 
                        diferenca, 
                        observacoes,
                        status
                    ) VALUES (?, datetime('now'), ?, ?, ?, ?, 'Concluído')
                """, (
                    dados_fechamento['usuario_id'],
                    dados_fechamento['valor_sistema'],
                    dados_fechamento['valor_informado'],
                    dados_fechamento['diferenca'],
                    dados_fechamento.get('observacoes', '')
                ))
                
                fechamento_id = cursor.lastrowid
                
                # Inserir os detalhes por forma de pagamento
                for forma_pagamento in dados_fechamento.get('formas_pagamento', []):
                    cursor.execute("""
                        INSERT INTO fechamentos_formas_pagamento (
                            fechamento_id,
                            forma_pagamento,
                            valor_sistema,
                            valor_informado,
                            diferenca
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        fechamento_id,
                        forma_pagamento['forma'],
                        forma_pagamento['valor_sistema'],
                        forma_pagamento['valor_informado'],
                        forma_pagamento['diferenca']
                    ))
                
                return fechamento_id
                
        except Exception as e:
            print(f"Erro ao registrar fechamento: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def inserir_saque(self, valor: float, origem: str, motivo: str, descricao: str, usuario_id: int):
        """Insere um registro de saque em retiradas_caixa e retorna o ID."""
        try:
            # Garante que a tabela exista
            self.garantir_tabela_retiradas_caixa()

            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO retiradas_caixa (
                    usuario_id,
                    valor,
                    motivo,
                    observacao,
                    origem,
                    status,
                    data_retirada,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, 'Completo', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (usuario_id, float(valor), motivo, descricao, origem)
            )
            # Registrar saída na movimentacao_caixa (impacta saldo imediatamente)
            try:
                descricao_mc = f"Saque - {origem}"
                cursor.execute(
                    """
                    INSERT INTO movimentacao_caixa (
                        data_movimento, tipo, valor, descricao, categoria, usuario_id
                    ) VALUES (CURRENT_TIMESTAMP, 'Saída', ?, ?, ?, ?)
                    """,
                    (float(valor), descricao_mc, origem, usuario_id)
                )
            except Exception as mc_err:
                print(f"Aviso: falha ao registrar movimentacao_caixa: {mc_err}")
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao inserir saque: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return None
