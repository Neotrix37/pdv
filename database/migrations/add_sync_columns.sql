-- Script para adicionar colunas de sincronização em todas as tabelas

-- Tabela de produtos
ALTER TABLE produtos ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE produtos ADD COLUMN synced BOOLEAN DEFAULT FALSE;

-- Tabela de vendas
ALTER TABLE vendas ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE vendas ADD COLUMN synced BOOLEAN DEFAULT FALSE;

-- Tabela de itens_venda
ALTER TABLE itens_venda ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE itens_venda ADD COLUMN synced BOOLEAN DEFAULT FALSE;

-- Tabela de clientes
ALTER TABLE clientes ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE clientes ADD COLUMN synced BOOLEAN DEFAULT FALSE;

-- Tabela de usuários
ALTER TABLE usuarios ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE usuarios ADD COLUMN synced BOOLEAN DEFAULT FALSE;

-- Tabela de categorias
ALTER TABLE categorias ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE categorias ADD COLUMN synced BOOLEAN DEFAULT FALSE;

-- Tabela de fornecedores
ALTER TABLE fornecedores ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE fornecedores ADD COLUMN synced BOOLEAN DEFAULT FALSE;

-- Tabela de retiradas_caixa
ALTER TABLE retiradas_caixa ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE retiradas_caixa ADD COLUMN synced BOOLEAN DEFAULT FALSE;

-- Criar tabela para logs de sincronização
CREATE TABLE IF NOT EXISTS sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    records_synced INTEGER DEFAULT 0,
    error_message TEXT,
    details TEXT
);
