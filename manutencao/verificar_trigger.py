#!/usr/bin/env python3
"""Script para verificar e corrigir o trigger after_divida_quitada"""

import sqlite3
import os
from pathlib import Path

def verificar_trigger():
    db_path = Path(os.environ['APPDATA']) / 'SistemaGestao' / 'database' / 'sistema.db'
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar trigger atual
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='after_divida_quitada'")
        result = cursor.fetchone()
        
        if result:
            print("TRIGGER ATUAL:")
            print(result[0])
            print("\n" + "="*50 + "\n")
        else:
            print("Trigger 'after_divida_quitada' nao encontrado!")
        
        # Verificar estrutura da tabela vendas
        cursor.execute("PRAGMA table_info(vendas)")
        colunas = cursor.fetchall()
        print("COLUNAS DA TABELA VENDAS:")
        for col in colunas:
            print(f"- {col[1]} ({col[2]})")
        
        # Corrigir trigger se necessário
        print("\nRecriando trigger corrigido...")
        cursor.execute("DROP TRIGGER IF EXISTS after_divida_quitada")
        
        cursor.execute("""
            CREATE TRIGGER after_divida_quitada
            AFTER UPDATE ON dividas
            WHEN NEW.status = 'Quitado' AND OLD.status = 'Pendente'
            BEGIN
                INSERT INTO vendas ( 
                    usuario_id,
                    valor_total,
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
        print("Trigger corrigido com sucesso!")
        
        # Verificar novo trigger
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='after_divida_quitada'")
        result = cursor.fetchone()
        
        if result:
            print("\nNOVO TRIGGER:")
            print(result[0])
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    verificar_trigger()
