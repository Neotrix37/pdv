import sqlite3
from pathlib import Path
import threading
from werkzeug.security import generate_password_hash
import os
import hashlib
from datetime import datetime

class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            # Garante que o diretório database existe no diretório raiz do projeto
            db_dir = Path(os.path.dirname(os.path.dirname(__file__))) / 'database'
            db_dir.mkdir(exist_ok=True)
            
            # Caminho absoluto para o banco de dados
            self.db_path = db_dir / 'sistema.db'
            
            # Conexão com o banco de dados
            self.conn = sqlite3.connect(str(self.db_path.absolute()), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # Inicializa as tabelas
            self._init_database()
            self.initialized = True

    def _init_database(self):
        try:
            cursor = self.conn.cursor()
            
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

            # Criar tabela de produtos
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                descricao TEXT,
                preco_custo REAL NOT NULL,
                preco_venda REAL NOT NULL,
                estoque INTEGER NOT NULL DEFAULT 0,
                estoque_minimo INTEGER NOT NULL DEFAULT 0,
                ativo INTEGER NOT NULL DEFAULT 1,
                venda_por_peso INTEGER DEFAULT 0,
                unidade_medida TEXT DEFAULT 'un',
                categoria_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )
            ''')

            # Verificar se a coluna categoria_id existe
            cursor.execute("PRAGMA table_info(produtos)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            # Se a coluna categoria_id não existir, adiciona
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

            # Create financial reports tables
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
                    -- Log para debug
                    INSERT INTO sqlite_master (type, name, sql) VALUES ('TRIGGER_LOG', 'divida_quitada', 
                        'Dívida ' || NEW.id || ' quitada - criando venda correspondente');
                    
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
                ON produtos(nome, codigo, ativo)
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

            self.conn.commit()
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {e}")
            self.conn.rollback()

    def execute(self, sql, params=()):
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()  # Garante que as alterações sejam salvas
            return cursor

    def fetchone(self, sql, params=None, dictionary=False):
        """Executa uma consulta e retorna uma única linha"""
        try:
            cursor = self.conn.cursor()
            if dictionary:
                cursor.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
            cursor.execute(sql, params or ())
            return cursor.fetchone()
        except Exception as e:
            return None

    def fetchall(self, sql, params=(), dictionary=False):
        """Executa uma consulta e retorna todas as linhas"""
        with self._lock:
            cursor = self.conn.cursor()
            if dictionary:
                cursor.row_factory = lambda c, r: {col[0]: r[idx] for idx, col in enumerate(c.description)}
            cursor.execute(sql, params)
            return cursor.fetchall()

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

    def reset_database(self):
        """Reseta o banco de dados para o estado inicial"""
        try:
            # Conectar diretamente ao banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Deletar todas as tabelas existentes
            cursor.executescript("""
                PRAGMA foreign_keys = OFF;
                
                -- Deletar todas as tabelas existentes
                DROP TABLE IF EXISTS itens_venda;
                DROP TABLE IF EXISTS vendas;
                DROP TABLE IF EXISTS produtos;
                DROP TABLE IF EXISTS usuarios;
                DROP TABLE IF EXISTS printer_config;
                DROP TABLE IF EXISTS contas_pagar;
                DROP TABLE IF EXISTS movimentacao_caixa;
                DROP TABLE IF EXISTS categorias_despesa;
                
                -- Limpar sequências de AUTO_INCREMENT
                DELETE FROM sqlite_sequence;
                
                -- Recriar as tabelas do zero
                CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    usuario TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    is_admin BOOLEAN NOT NULL DEFAULT 0,
                    ativo BOOLEAN NOT NULL DEFAULT 1
                );

                CREATE TABLE produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    preco_custo REAL NOT NULL,
                    preco_venda REAL NOT NULL,
                    estoque INTEGER NOT NULL DEFAULT 0,
                    estoque_minimo INTEGER NOT NULL DEFAULT 1,
                    ativo BOOLEAN NOT NULL DEFAULT 1
                );

                CREATE TABLE vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    data_venda TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    total REAL NOT NULL,
                    forma_pagamento TEXT NOT NULL,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                );

                CREATE TABLE itens_venda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venda_id INTEGER NOT NULL,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL,
                    preco_unitario REAL NOT NULL,
                    preco_custo_unitario REAL NOT NULL,
                    FOREIGN KEY (venda_id) REFERENCES vendas (id),
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                );
                
                CREATE TABLE contas_pagar (
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

                CREATE TABLE movimentacao_caixa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_movimento DATETIME NOT NULL,
                    tipo TEXT NOT NULL,  -- 'Entrada' ou 'Saída'
                    valor REAL NOT NULL,
                    descricao TEXT NOT NULL,
                    categoria TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                );

                CREATE TABLE categorias_despesa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                );
                
                PRAGMA foreign_keys = ON;
            """)
            
            # Criar usuário admin com senha criptografada
            import hashlib
            senha_admin = "admin123"
            senha_hash = hashlib.sha256(senha_admin.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO usuarios (nome, usuario, senha, is_admin, ativo)
                VALUES (?, ?, ?, ?, ?)
            """, ("Administrador", "admin", senha_hash, 1, 1))
            
            # Garantir que as alterações sejam salvas
            conn.commit()
            
            # Verificar se o usuário foi criado
            cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
            admin_user = cursor.fetchone()
            if not admin_user:
                raise Exception("Falha ao criar usuário admin")
                
            conn.close()
            return True
            
        except Exception as e:
            if conn:
                conn.close()
            return False

    def verificar_login(self, usuario, senha):
        """Verifica as credenciais do usuário"""
        try:
            # Criptografar a senha fornecida para comparação
            import hashlib
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            
            # Buscar usuário
            result = self.fetchone("""
                SELECT id, nome, usuario, is_admin, ativo
                FROM usuarios 
                WHERE usuario = ? AND senha = ? AND ativo = 1
            """, (usuario, senha_hash))
            
            if result:
                return {
                    'id': result[0],
                    'nome': result[1],
                    'usuario': result[2],
                    'is_admin': bool(result[3]),
                    'ativo': bool(result[4])
                }
            return None
            
        except Exception as e:
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
            
            # Garante que todos os campos necessários existem
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
        """Retorna o total de vendas do dia"""
        try:
            result = self.fetchone("""
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE total 
                    END
                ), 0) as total
                FROM vendas
                WHERE DATE(data_venda) = DATE('now')
            """)
            return result['total'] if result else 0
        except Exception as e:
            print(f"Erro ao buscar total de vendas hoje: {e}")
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

    def registrar_fechamento(self, dados_fechamento):
        """Registra um novo fechamento de caixa"""
        try:
            cursor = self.conn.cursor()
            
            # Inserir fechamento principal
            cursor.execute("""
                INSERT INTO fechamentos_caixa (
                    usuario_id, data_fechamento,
                    valor_sistema, valor_informado,
                    diferenca, observacoes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                dados_fechamento['usuario_id'],
                dados_fechamento['data_fechamento'],
                dados_fechamento['valor_sistema'],
                dados_fechamento['valor_informado'],
                dados_fechamento['diferenca'],
                dados_fechamento['observacoes'],
                'Pendente'
            ))
            
            fechamento_id = cursor.lastrowid
            
            # Inserir detalhes por forma de pagamento
            for forma in dados_fechamento['formas_pagamento']:
                cursor.execute("""
                    INSERT INTO fechamentos_formas_pagamento (
                        fechamento_id, forma_pagamento,
                        valor_sistema, valor_informado, diferenca
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    fechamento_id,
                    forma['forma'],
                    forma['valor_sistema'],
                    forma['valor_informado'],
                    forma['diferenca']
                ))
            
            # Vincular vendas ao fechamento
            cursor.execute("""
                INSERT INTO vendas_fechamentos (venda_id, fechamento_id)
                SELECT id, ?
                FROM vendas
                WHERE usuario_id = ?
                AND DATE(data_venda) = DATE('now')
                AND id NOT IN (
                    SELECT venda_id FROM vendas_fechamentos
                    WHERE venda_id IS NOT NULL
                )
            """, (fechamento_id, dados_fechamento['usuario_id']))
            
            self.conn.commit()
            return fechamento_id
            
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao registrar fechamento: {e}")
            raise

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
                WHERE DATE(v.data_venda) = DATE('now')
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
            if os.path.exists('database.db'):
                os.remove('database.db')
                print("Arquivo do banco removido")
            
            # Recriar conexão e inicializar banco
            self.conn = self._create_connection()
            self._init_database()
            print("Banco de dados recriado com sucesso!")
            print("=== Fim da recriação do banco ===\n")
            
        except Exception as error:
            print(f"Erro ao recriar banco: {error}")
            raise error
