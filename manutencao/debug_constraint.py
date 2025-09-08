#!/usr/bin/env python3
"""Script para investigar e corrigir constraint NOT NULL na coluna 'total'"""

import sqlite3
import os
from pathlib import Path

def debug_constraint():
    db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar estrutura detalhada da tabela vendas
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = cursor.fetchall()
        print("ESTRUTURA DETALHADA DA TABELA VENDAS:")
        for col in colunas:
            not_null = "NOT NULL" if col[3] else "NULL"
            default = f"DEFAULT {col[4]}" if col[4] else "NO DEFAULT"
            print(f"- {col[1]} ({col[2]}) {not_null} {default}")
        
        print("\n" + "="*60 + "\n")
        
        # Verificar o SQL de criação da tabela
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vendas'")
        result = cursor.fetchone()
        if result:
            print("SQL DE CRIAÇÃO DA TABELA VENDAS:")
            print(result[0])
        
        print("\n" + "="*60 + "\n")
        
        # Verificar se a coluna 'total' tem constraint NOT NULL
        total_col = None
        for col in colunas:
            if col[1] == 'total':
                total_col = col
                break
        
        if total_col:
            print(f"COLUNA 'total': {total_col}")
            if total_col[3]:  # NOT NULL = 1
                print("❌ PROBLEMA: Coluna 'total' tem constraint NOT NULL!")
                print("Isso está causando o erro ao inserir vendas via trigger.")
                
                # Corrigir removendo a constraint NOT NULL
                print("\nCorrigindo constraint...")
                
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
                        status TEXT DEFAULT 'Concluída',
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
                
                # Recriar trigger corrigido
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
                print("✅ Constraint NOT NULL removida da coluna 'total'!")
                print("✅ Trigger atualizado para preencher ambas as colunas!")
                
            else:
                print("✅ Coluna 'total' não tem constraint NOT NULL")
        else:
            print("❌ Coluna 'total' não encontrada!")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_constraint()
