#!/usr/bin/env python3
"""Script para corrigir definitivamente a constraint NOT NULL na coluna 'total'"""

import sqlite3
import os
from pathlib import Path

def fix_constraint():
    db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("PROBLEMA IDENTIFICADO: Coluna 'total' tem constraint NOT NULL!")
        print("Corrigindo constraint...")
        
        # Criar nova tabela sem NOT NULL na coluna total
        cursor.execute("""
            CREATE TABLE vendas_temp AS SELECT * FROM vendas
        """)
        
        cursor.execute("DROP TABLE vendas")
        
        # Recriar tabela sem NOT NULL em 'total'
        cursor.execute("""
            CREATE TABLE vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                total REAL,
                forma_pagamento TEXT,
                valor_recebido REAL,
                troco REAL,
                data_venda DATETIME DEFAULT (datetime('now', 'localtime')),
                status TEXT DEFAULT 'Concluida',
                motivo_alteracao TEXT,
                alterado_por INTEGER,
                data_alteracao TIMESTAMP,
                origem TEXT,
                valor_original_divida REAL,
                desconto_aplicado_divida REAL,
                valor_total REAL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                FOREIGN KEY (alterado_por) REFERENCES usuarios (id)
            )
        """)
        
        # Restaurar dados
        cursor.execute("""
            INSERT INTO vendas SELECT * FROM vendas_temp
        """)
        
        cursor.execute("DROP TABLE vendas_temp")
        
        # Recriar trigger corrigido para preencher AMBAS as colunas
        cursor.execute("DROP TRIGGER IF EXISTS after_divida_quitada")
        cursor.execute("""
            CREATE TRIGGER after_divida_quitada
            AFTER UPDATE ON dividas
            WHEN NEW.status = 'Quitado' AND OLD.status = 'Pendente'
            BEGIN
                INSERT INTO vendas ( 
                    usuario_id,
                    valor_total,
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
                    d.valor_total,
                    (SELECT forma_pagamento FROM pagamentos_divida 
                     WHERE divida_id = d.id 
                     ORDER BY data_pagamento DESC LIMIT 1),
                    d.valor_total,
                    0,
                    datetime('now', 'localtime'),
                    'divida_quitada',
                    COALESCE(d.valor_original, d.valor_total),
                    COALESCE(d.desconto_aplicado, 0)
                FROM dividas d
                WHERE d.id = NEW.id;

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
                    COALESCE(id.peso_kg, 0)
                FROM itens_divida id
                WHERE id.divida_id = NEW.id;
            END
        """)
        
        conn.commit()
        print("Constraint NOT NULL removida da coluna 'total'!")
        print("Trigger atualizado para preencher ambas as colunas!")
        print("Problema resolvido - dividas podem ser quitadas sem erro!")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    fix_constraint()
