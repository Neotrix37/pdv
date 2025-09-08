import sqlite3
import os
import sys
from datetime import datetime

def get_database_path():
    # Tenta localizar o banco de dados em diferentes locais
    possible_paths = [
        os.path.join(os.getenv('APPDATA'), 'SistemaGestao', 'database', 'sistema.db'),
        'database/sistema.db',
        'sistema.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print("Erro: Banco de dados não encontrado nos locais padrão.")
    print("Por favor, verifique se o banco de dados existe em um destes locais:")
    for path in possible_paths:
        print(f"- {path}")
    sys.exit(1)

def corrigir_calculo_lucro():
    db_path = get_database_path()
    print(f"\nConectando ao banco de dados em: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== Verificando e corrigindo índices e funções de cálculo de lucro ===")
        
        # 1. Criar índices para melhorar o desempenho das consultas
        print("\nCriando índices para otimização...")
        
        # Índice para consultas de vendas por data
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_vendas_data 
        ON vendas(data_venda)
        """)
        
        # Índice para consultas de itens por venda
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_itens_venda_id 
        ON itens_venda(venda_id)
        """)
        
        # 2. Criar VIEW para cálculo de lucro por venda
        print("Criando VIEW para cálculo de lucro por venda...")
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_lucro_vendas AS
        SELECT 
            v.id as venda_id,
            v.data_venda,
            v.total as valor_total,
            SUM(iv.subtotal) as subtotal_itens,
            SUM(iv.preco_custo_unitario * iv.quantidade) as custo_total,
            SUM(iv.subtotal - (iv.preco_custo_unitario * iv.quantidade)) as lucro_bruto,
            CASE 
                WHEN v.status = 'Anulada' THEN 0 
                ELSE SUM(iv.subtotal - (iv.preco_custo_unitario * iv.quantidade)) 
            END as lucro_liquido
        FROM vendas v
        LEFT JOIN itens_venda iv ON v.id = iv.venda_id
        GROUP BY v.id
        """)
        
        # 3. Criar VIEW para resumo diário de vendas e lucro
        print("Criando VIEW para resumo diário...")
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_resumo_diario AS
        SELECT 
            DATE(data_venda) as data,
            COUNT(DISTINCT id) as total_vendas,
            SUM(total) as valor_total_vendas,
            SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END) as valor_total_liquido,
            (SELECT COALESCE(SUM(lucro_liquido), 0) FROM vw_lucro_vendas WHERE DATE(data_venda) = DATE(v.data_venda)) as lucro_liquido
        FROM vendas
        GROUP BY DATE(data_venda)
        ORDER BY data DESC
        """)
        
        # 4. Criar VIEW para resumo mensal de vendas e lucro
        print("Criando VIEW para resumo mensal...")
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_resumo_mensal AS
        SELECT 
            strftime('%Y-%m', data_venda) as mes_ano,
            COUNT(DISTINCT id) as total_vendas,
            SUM(total) as valor_total_vendas,
            SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END) as valor_total_liquido,
            (SELECT COALESCE(SUM(lucro_liquido), 0) 
             FROM vw_lucro_vendas 
             WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', v.data_venda)) as lucro_liquido
        FROM vendas v
        GROUP BY strftime('%Y-%m', data_venda)
        ORDER BY mes_ano DESC
        """)
        
        # 5. Criar função para calcular lucro em um período
        print("Criando função para cálculo de lucro em período...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracao (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
        """)
        
        # Inserir a função de cálculo de lucro como um valor na tabela de configuração
        cursor.execute("""
        INSERT OR REPLACE INTO configuracao (chave, valor)
        VALUES ('funcao_calculo_lucro', 
                'SELECT COALESCE(SUM(subtotal - (preco_custo_unitario * quantidade)), 0) 
                 FROM itens_venda iv 
                 JOIN vendas v ON iv.venda_id = v.id 
                 WHERE v.status != "Anulada" AND data_venda BETWEEN ? AND ?')
        """)
        
        # 6. Atualizar estatísticas do banco de dados
        print("Atualizando estatísticas do banco de dados...")
        cursor.execute("ANALYZE")
        
        conn.commit()
        print("\n=== Correções aplicadas com sucesso! ===")
        
        # Verificar se as views foram criadas corretamente
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        print("\nViews criadas/atualizadas:")
        for view in views:
            print(f"- {view['name']}")
        
        # Mostrar estatísticas de vendas
        cursor.execute("SELECT COUNT(*) as total FROM vendas")
        total_vendas = cursor.fetchone()['total']
        print(f"\nTotal de vendas no sistema: {total_vendas}")
        
        cursor.execute("SELECT * FROM vw_resumo_mensal ORDER BY mes_ano DESC LIMIT 3")
        print("\nResumo mensal (últimos 3 meses):")
        for row in cursor.fetchall():
            print(f"Mês: {row['mes_ano']} | Vendas: {row['total_vendas']} | "
                  f"Total: MT {float(row['valor_total_liquido'] or 0):.2f} | "
                  f"Lucro: MT {float(row['lucro_liquido'] or 0):.2f}")
        
        cursor.close()
        conn.close()
        
        print("\n=== Processo concluído com sucesso! ===")
        print("Otimizações de desempenho aplicadas ao banco de dados.")
        
    except sqlite3.Error as e:
        print(f"\nErro ao executar as correções: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)

if __name__ == "__main__":
    print("=== CORRIGIR CÁLCULO DE LUCRO E VENDAS ===")
    print("Este script irá otimizar o banco de dados para melhorar o cálculo de lucro e vendas.")
    print("Certifique-se de fazer um backup do banco de dados antes de continuar.")
    
    confirm = input("\nDeseja continuar? (s/n): ").strip().lower()
    if confirm == 's':
        corrigir_calculo_lucro()
    else:
        print("Operação cancelada pelo usuário.")
        sys.exit(0)
