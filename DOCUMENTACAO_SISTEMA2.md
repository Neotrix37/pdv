# Documentação Completa do Sistema PDV

## Visão Geral
O Sistema PDV é um sistema de gestão comercial completo que inclui controle de vendas, estoque, clientes, fornecedores, despesas e sincronização com servidor remoto.

## Sistema de Sincronização

### Funcionamento da Sincronização
O sistema utiliza o módulo <mcfile name="sync_manager.py" path="c:\Users\saide\sinc\pdv3\utils\sync_manager.py"></mcfile> para gerenciar a sincronização bidirecional entre o banco local e o servidor remoto.

### Tabelas Sincronizadas
- **Produtos** - Upload e Download
- **Categorias** - Upload e Download  
- **Clientes** - Upload e Download
- **Vendas** - Upload e Download
- **Itens de Venda** - Upload e Download
- **Usuários** - Apenas Download (não sobe dados locais)
- **Fornecedores** - Upload e Download
- **Despesas** - Upload e Download
- **Contas a Pagar** - Upload e Download
- **Contas a Receber** - Upload e Download

### Processo de Sincronização
1. **Busca dados não sincronizados** localmente
2. **Envia para servidor** com retry automático (3 tentativas)
3. **Busca atualizações** do servidor
4. **Atualiza banco local** com dados recebidos
5. **Marca registros** como sincronizados

### Configuração
```env
SYNC_AUTH_TOKEN=seu_token_aqui
```

## Estrutura do Banco de Dados

### Tabelas Principais

#### 1. Usuários (<mcfile name="database.py" path="c:\Users\saide\sinc\pdv3\database\database.py"></mcfile>)
```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    usuario TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    nivel INTEGER NOT NULL DEFAULT 1,
    ativo INTEGER NOT NULL DEFAULT 1,
    is_admin INTEGER NOT NULL DEFAULT 0,
    salario REAL DEFAULT 0,
    pode_abastecer INTEGER NOT NULL DEFAULT 0,
    pode_gerenciar_despesas INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 2. Clientes
```sql
CREATE TABLE clientes (
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
```

#### 3. Categorias
```sql
CREATE TABLE categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    descricao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 4. Fornecedores
```sql
CREATE TABLE fornecedores (
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
```

#### 5. Produtos
```sql
CREATE TABLE produtos (
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
```

#### 6. Vendas
```sql
CREATE TABLE vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    total REAL NOT NULL,
    forma_pagamento TEXT NOT NULL,
    valor_recebido REAL,
    troco REAL,
    data_venda DATETIME NOT NULL,
    status TEXT NOT NULL DEFAULT 'Ativa',
    motivo_alteracao TEXT,
    alterado_por INTEGER REFERENCES usuarios(id),
    data_alteracao TIMESTAMP,
    origem TEXT DEFAULT 'venda_direta',
    valor_original_divida REAL DEFAULT 0,
    desconto_aplicado_divida REAL DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
```

#### 7. Itens de Venda
```sql
CREATE TABLE itens_venda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario REAL NOT NULL,
    preco_custo_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    status TEXT,
    motivo_alteracao TEXT,
    alterado_por INTEGER REFERENCES usuarios(id),
    data_alteracao TIMESTAMP,
    peso_kg REAL DEFAULT 0,
    FOREIGN KEY (venda_id) REFERENCES vendas (id),
    FOREIGN KEY (produto_id) REFERENCES produtos (id)
)
```

#### 8. Dívidas
```sql
CREATE TABLE dividas (
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
```

#### 9. Itens de Dívida
```sql
CREATE TABLE itens_divida (
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
```

#### 10. Pagamentos de Dívida
```sql
CREATE TABLE pagamentos_divida (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    divida_id INTEGER NOT NULL,
    data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valor REAL NOT NULL,
    forma_pagamento TEXT NOT NULL,
    usuario_id INTEGER NOT NULL,
    FOREIGN KEY (divida_id) REFERENCES dividas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
)
```

#### 11. Contas a Pagar
```sql
CREATE TABLE contas_pagar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    categoria TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pendente',
    observacao TEXT,
    usuario_id INTEGER,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
```

#### 12. Movimentação de Caixa
```sql
CREATE TABLE movimentacao_caixa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_movimento DATETIME NOT NULL,
    tipo TEXT NOT NULL,
    valor REAL NOT NULL,
    descricao TEXT NOT NULL,
    categoria TEXT,
    usuario_id INTEGER,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
```

#### 13. Fechamentos de Caixa
```sql
CREATE TABLE fechamentos_caixa (
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
```

#### 14. Fechamentos por Forma de Pagamento
```sql
CREATE TABLE fechamentos_formas_pagamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fechamento_id INTEGER NOT NULL,
    forma_pagamento TEXT NOT NULL,
    valor_sistema REAL NOT NULL,
    valor_informado REAL NOT NULL,
    diferenca REAL NOT NULL,
    FOREIGN KEY (fechamento_id) REFERENCES fechamentos_caixa (id)
)
```

#### 15. Retiradas de Caixa
```sql
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
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (aprovador_id) REFERENCES usuarios(id)
)
```

#### 16. Configurações da Impressora
```sql
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 17. Configurações Gerais
```sql
CREATE TABLE configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT,
    descricao TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 18. Formas de Pagamento
```sql
CREATE TABLE formas_pagamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    ativo INTEGER DEFAULT 1
)
```

#### 19. Despesas Recorrentes
```sql
CREATE TABLE despesas_recorrentes (
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
```

#### 20. Orçamentos
```sql
CREATE TABLE orcamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    tipo TEXT NOT NULL,
    valor_previsto REAL NOT NULL,
    valor_realizado REAL DEFAULT 0,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Colunas de Sincronização
Todas as tabelas principais possuem colunas para controle de sincronização:
- `synced` - BOOLEAN (indica se o registro foi sincronizado)
- `last_updated` - TIMESTAMP (última atualização)

## Triggers Importantes

### 1. Trigger de Vendas
Registra automaticamente vendas na movimentação de caixa:
```sql
CREATE TRIGGER after_venda_insert AFTER INSERT ON vendas
BEGIN
    INSERT INTO movimentacao_caixa (data_movimento, tipo, valor, descricao, usuario_id)
    VALUES (NEW.data_venda, 'Entrada', NEW.total, 'Venda #' || NEW.id, NEW.usuario_id);
END
```

### 2. Trigger de Pagamentos
Registra pagamentos de contas na movimentação de caixa:
```sql
CREATE TRIGGER after_conta_pagar_update AFTER UPDATE OF status ON contas_pagar
WHEN NEW.status = 'Pago' AND OLD.status = 'Pendente'
BEGIN
    INSERT INTO movimentacao_caixa (data_movimento, tipo, valor, descricao, usuario_id)
    VALUES (NEW.data_pagamento, 'Saída', NEW.valor, 'Pagamento: ' || NEW.descricao, NEW.usuario_id);
END
```

### 3. Trigger de Dívidas Quitadas
Registra automaticamente quando uma dívida é quitada:
```sql
CREATE TRIGGER after_divida_quitada AFTER UPDATE ON dividas
WHEN NEW.status = 'Quitado' AND OLD.status = 'Pendente'
BEGIN
    -- Insere na tabela de vendas e itens_venda sem afetar estoque
END
```

## Funcionalidades do Sistema

### 1. Gestão de Produtos
- Cadastro com código único
- Controle de estoque e estoque mínimo
- Venda por peso ou unidade
- Categorização
- Múltiplos fornecedores

### 2. Sistema de Vendas
- Vendas diretas
- Controle de formas de pagamento
- Cálculo automático de troco
- Histórico completo de vendas

### 3. Gestão de Clientes
- Cadastro completo com NUIT
- Clientes especiais com descontos
- Controle de dívidas
- Histórico de compras

### 4. Controle Financeiro
- Contas a pagar e receber
- Movimentação de caixa
- Fechamentos de caixa
- Retiradas controladas
- Orçamentos

### 5. Relatórios
- Relatórios de vendas
- Relatórios financeiros
- Controle de estoque
- Performance de vendedores

### 6. Segurança
- Múltiplos níveis de usuário
- Controle de permissões
- Logs de atividades
- Backup automático

## Estrutura de Diretórios
```
pdv3/
├── database/           # Banco de dados e migrations
├── utils/               # Utilitários (sync_manager, PDF, etc.)
├── views/               # Interfaces gráficas
├── models/              # Modelos de dados
├── backups/             # Backups automáticos
├── relatorios/          # Relatórios em PDF/Excel
└── assets/              # Ícones e recursos
```

## Considerações Técnicas

### Performance
- Índices otimizados para buscas
- Triggers para automatização
- Controle de transações

### Segurança
- Hash de senhas com Werkzeug
- Controle de permissões
- Validação de dados

### Backup
- Backups automáticos regulares
- Sistema de restore
- Migrações automáticas

Esta documentação cobre a estrutura completa do sistema PDV, incluindo todas as tabelas do banco de dados, sistema de sincronização e funcionalidades principais.