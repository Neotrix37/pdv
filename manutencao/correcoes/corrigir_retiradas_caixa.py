#!/usr/bin/env python3
"""
Script para corrigir a tabela retiradas_caixa que está faltando no banco de dados
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database
import sqlite3

def garantir_tabela_retiradas_caixa(db):
    """Garante que a tabela retiradas_caixa exista com a estrutura correta"""
    try:
        cursor = db.conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='retiradas_caixa'
        """)
        
        if not cursor.fetchone():
            print("❌ A tabela retiradas_caixa não existe. Criando...")
            
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
            
            db.conn.commit()
            print("✅ Tabela retiradas_caixa criada com sucesso!")
            return True
        else:
            print("✅ A tabela retiradas_caixa já existe!")
            
            # Verificar estrutura da tabela
            cursor.execute("PRAGMA table_info(retiradas_caixa)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print("Colunas da tabela retiradas_caixa:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Verificar e adicionar colunas ausentes
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
                    print(f"\nAdicionando coluna '{coluna}'...")
                    try:
                        cursor.execute(f"""
                            ALTER TABLE retiradas_caixa
                            ADD COLUMN {coluna} {definicao}
                        """)
                        db.conn.commit()
                        print(f"✅ Coluna '{coluna}' adicionada com sucesso!")
                    except Exception as e:
                        print(f"❌ Erro ao adicionar coluna '{coluna}': {e}")
            
            # Verificar se o trigger existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='trigger' AND name='retiradas_caixa_updated_at'
            """)
            
            if not cursor.fetchone():
                print("\nCriando trigger para updated_at...")
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
                    db.conn.commit()
                    print("✅ Trigger criado com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao criar trigger: {e}")
            else:
                print("✅ Trigger já existe!")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar/criar tabela retiradas_caixa: {e}")
        return False

def main():
    print("=== Script de Correção da Tabela retiradas_caixa ===\n")
    
    try:
        # Conectar ao banco de dados
        db = Database()
        
        # Garantir que a tabela existe
        if not garantir_tabela_retiradas_caixa(db):
            print("❌ Falha ao garantir a existência da tabela retiradas_caixa")
            return
        
        # Testar se a tabela está funcionando
        print("\nTestando funcionalidade da tabela...")
        try:
            # Testar inserção
            cursor = db.conn.cursor()
            cursor.execute("""
                INSERT INTO retiradas_caixa (usuario_id, valor, motivo, origem, status)
                VALUES (1, 0.01, 'Teste de funcionalidade', 'vendas', 'pendente')
            """)
            
            # Testar consulta
            result = db.fetchone("SELECT COUNT(*) as total FROM retiradas_caixa")
            print(f"✅ Tabela funcionando! Total de registros: {result['total']}")
            
            # Remover registro de teste
            cursor.execute("DELETE FROM retiradas_caixa WHERE motivo = 'Teste de funcionalidade'")
            db.conn.commit()
            
        except Exception as e:
            print(f"❌ Erro ao testar tabela: {e}")
            return
        
        print("\n🎉 Correção concluída com sucesso!")
        print("A tabela retiradas_caixa está pronta para uso.")
        
        # Verificar se há backups que precisam ser corrigidos
        print("\nVerificando backups...")
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        if os.path.exists(backup_dir):
            backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
            if backups:
                print(f"Encontrados {len(backups)} backups. Recomenda-se executar este script após restaurar qualquer backup.")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return

if __name__ == "__main__":
    main()
