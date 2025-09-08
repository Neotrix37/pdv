# Documentação do Sistema de PDV

## Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
4. [Tabelas do Banco de Dados](#tabelas-do-banco-de-dados)
5. [Fluxos Principais](#fluxos-principais)
6. [Módulos do Sistema](#módulos-do-sistema)
7. [Configuração e Instalação](#configuração-e-instalação)
8. [Manutenção e Backup](#manutenção-e-backup)

## Visão Geral

O Sistema de Ponto de Venda (PDV) é uma solução completa para gestão de vendas, estoque e relacionamento com clientes. Desenvolvido em Python com interface Flet, o sistema oferece uma experiência intuitiva para operações do dia a dia, desde o registro de vendas até a geração de relatórios gerenciais.

## Arquitetura do Sistema

```
pdv3/
├── database/           # Módulo de banco de dados
├── models/            # Modelos de dados
├── utils/             # Utilitários e funções auxiliares
├── views/             # Telas da aplicação
├── relatorios/        # Geração de relatórios
├── manutencao/        # Scripts de manutenção
└── main.py            # Ponto de entrada da aplicação
```

## Estrutura do Banco de Dados

O banco de dados SQLite é armazenado em:
- `%APPDATA%\SistemaGestao\database\sistema.db` (produção)
- `caminho_do_projeto\database\sistema.db` (desenvolvimento)

## Tabelas do Banco de Dados

### 1. produtos
Armazena informações dos produtos disponíveis para venda.

| Coluna | Tipo | Descrição |
|--------|------|------------|
| id | INTEGER | Chave primária |
| codigo | TEXT | Código de barras/identificação |
| nome | TEXT | Nome do produto |
| descricao | TEXT | Descrição detalhada |
| preco_custo | REAL | Preço de custo |
| preco_venda | REAL | Preço de venda |
| estoque | REAL | Quantidade em estoque |
| categoria_id | INTEGER | FK para categorias |
| fornecedor_id | INTEGER | FK para fornecedores |
| venda_por_peso | INTEGER | 1 para venda por peso, 0 para unidade |
| ativo | INTEGER | 1 para ativo, 0 para inativo |
| data_cadastro | DATETIME | Data de cadastro |
| estoque_minimo | REAL | Estoque mínimo para alertas |

### 2. vendas
Registra as transações de venda.

| Coluna | Tipo | Descrição |
|--------|------|------------|
| id | INTEGER | Chave primária |
| usuario_id | INTEGER | FK para usuário que realizou a venda |
| total | REAL | Valor total da venda |
| forma_pagamento | TEXT | Forma de pagamento (dinheiro, cartão, etc.) |
| valor_recebido | REAL | Valor recebido do cliente |
| troco | REAL | Troco para o cliente |
| data_venda | DATETIME | Data e hora da venda |
| status | TEXT | Status da venda (Concluída, Cancelada, etc.) |
| cliente_id | INTEGER | FK para cliente (opcional) |
| desconto | REAL | Valor do desconto aplicado |
| observacoes | TEXT | Observações sobre a venda |

### 3. itens_venda
Itens incluídos em cada venda.

| Coluna | Tipo | Descrição |
|--------|------|------------|
| id | INTEGER | Chave primária |
| venda_id | INTEGER | FK para venda |
| produto_id | INTEGER | FK para produto |
| quantidade | REAL | Quantidade vendida |
| preco_unitario | REAL | Preço unitário no momento da venda |
| subtotal | REAL | Quantidade * Preço unitário |
| desconto | REAL | Desconto aplicado no item |

### 4. clientes
Cadastro de clientes.

| Coluna | Tipo | Descrição |
|--------|------|------------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome completo |
| telefone | TEXT | Telefone de contato |
| email | TEXT | E-mail (opcional) |
| endereco | TEXT | Endereço completo |
| data_cadastro | DATETIME | Data de cadastro |
| ativo | INTEGER | 1 para ativo, 0 para inativo |
| limite_credito | REAL | Limite de crédito (se aplicável) |
| divida_atual | REAL | Valor atual em dívida |

### 5. usuarios
Usuários do sistema.

| Coluna | Tipo | Descrição |
|--------|------|------------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome do usuário |
| email | TEXT | E-mail de acesso |
| senha | TEXT | Senha criptografada |
| nivel_acesso | TEXT | Nível de acesso (admin, gerente, vendedor) |
| ativo | INTEGER | 1 para ativo, 0 para inativo |
| data_cadastro | DATETIME | Data de cadastro |
| ultimo_acesso | DATETIME | Último acesso ao sistema |
| pode_abastecer | INTEGER | Permissão para abastecer estoque |
| pode_gerenciar_despesas | INTEGER | Permissão para gerenciar despesas |

### 6. categorias
Categorias de produtos.

| Coluna | Tipo | Descrição |
|--------|------|------------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome da categoria |
| descricao | TEXT | Descrição da categoria |
| ativo | INTEGER | 1 para ativo, 0 para inativo |

### 7. fornecedores
Fornecedores de produtos.

| Coluna | Tipo | Descrição |
|--------|------|------------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome do fornecedor |
| contato | TEXT | Nome do contato |
| telefone | TEXT | Telefone de contato |
| email | TEXT | E-mail de contato |
| endereco | TEXT | Endereço completo |
| ativo | INTEGER | 1 para ativo, 0 para inativo |

### 8. retiradas_caixa
Registro de saídas de caixa.

| Coluna | Tipo | Descrição |
|--------|------|------------|
| id | INTEGER | Chave primária |
| valor | REAL | Valor da retirada |
| motivo | TEXT | Motivo/descrição |
| data_retirada | DATETIME | Data e hora da retirada |
| usuario_id | INTEGER | FK para usuário que realizou a retirada |
| status | TEXT | Status da retirada (Completo, Pendente, etc.) |
| origem | TEXT | Origem do valor (vendas, lucro, etc.) |

## Fluxos Principais

### 1. Processo de Venda
1. O usuário faz login no sistema
2. Acessa a tela de PDV
3. Busca produtos por código ou descrição
4. Adiciona itens ao carrinho
5. Define forma de pagamento e valor recebido
6. Confirma a venda
7. O sistema:
   - Atualiza o estoque
   - Registra a venda
   - Emite comprovante
   - Atualiza os totais do caixa

### 2. Gestão de Estoque
1. Acessa o módulo de produtos
2. Cadastra novos produtos ou edita existentes
3. Define categorias e fornecedores
4. Realiza entrada de estoque
5. Monitora níveis de estoque
6. Recebe alertas de estoque mínimo

### 3. Geração de Relatórios
1. Acessa o módulo de relatórios
2. Seleciona o tipo de relatório
3. Define período e filtros
4. Gera relatório em PDF ou Excel
5. Visualiza ou imprime o relatório

## Módulos do Sistema

### 1. Autenticação
- Login/logout de usuários
- Controle de acesso baseado em funções
- Gerenciamento de sessões

### 2. PDV
- Interface de venda rápida
- Gerenciamento de carrinho
- Cálculo de totais e troco
- Cancelamento de vendas

### 3. Gestão de Produtos
- Cadastro e edição de produtos
- Controle de estoque
- Categorização
- Preços e descontos

### 4. Clientes
- Cadastro e histórico
- Controle de dívidas
- Fichas de clientes

### 5. Relatórios
- Vendas por período
- Produtos mais vendidos
- Fluxo de caixa
- Estoque atual

### 6. Configurações
- Parâmetros do sistema
- Backup e restauração
- Usuários e permissões

## Configuração e Instalação

### Requisitos
- Python 3.8 ou superior
- Bibliotecas listadas em requirements.txt
- Acesso a disco para armazenamento
- Resolução mínima: 1024x768

### Instalação
1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute o sistema:
   ```
   python main.py
   ```

## Manutenção e Backup

### Backup Automático
O sistema realiza backup automático do banco de dados:
- Diariamente para a pasta de backups
- Antes de atualizações importantes
- Antes de operações críticas

### Manutenção do Banco de Dados
O sistema inclui rotinas para:
- Verificação de integridade
- Otimização de índices
- Reparo de possíveis corrupções
- Limpeza de registros temporários

### Atualizações
1. Fazer backup do banco de dados
2. Atualizar os arquivos do sistema
3. Executar scripts de migração (se aplicável)
4. Reiniciar a aplicação

## Considerações Finais

Este sistema foi desenvolvido para ser robusto, seguro e de fácil manutenção. A arquitetura modular permite a adição de novos recursos sem afetar o funcionamento existente. Para suporte ou dúvidas, entre em contato com a equipe de desenvolvimento.
