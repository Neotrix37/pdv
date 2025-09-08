#!/usr/bin/env python3
"""
Script para corrigir o usuário admin após reset do banco de dados
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database
from werkzeug.security import generate_password_hash

def main():
    print("=== Script de Correção do Usuário Admin ===\n")
    
    try:
        # Conectar ao banco de dados
        db = Database()
        cursor = db.conn.cursor()
        
        # Verificar estrutura da tabela de usuários
        print("Verificando estrutura da tabela de usuários...")
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Verificar se a coluna nivel existe
        if 'nivel' not in column_names:
            print("Adicionando coluna 'nivel' à tabela usuarios...")
            try:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN nivel INTEGER NOT NULL DEFAULT 1")
                db.conn.commit()
                print("Coluna 'nivel' adicionada com sucesso!")
            except Exception as e:
                print(f"Erro ao adicionar coluna 'nivel': {e}")
        
        # Atualizar o usuário admin
        print("\nAtualizando usuário admin...")
        senha_hash = generate_password_hash("842384")
        
        try:
            cursor.execute("""
                UPDATE usuarios 
                SET senha = ?, is_admin = 1, ativo = 1, nivel = 2 
                WHERE usuario = 'admin'
            """, (senha_hash,))
            
            # Se não atualizou nenhum registro, criar o usuário
            if cursor.rowcount == 0:
                print("Usuário admin não encontrado. Criando...")
                cursor.execute("""
                    INSERT INTO usuarios (nome, usuario, senha, is_admin, ativo, nivel, salario)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    'Administrador',
                    'admin',
                    senha_hash,
                    1,  # is_admin = True
                    1,  # ativo = True
                    2,  # nivel = 2 (admin)
                    0.0  # salario inicial
                ))
            
            db.conn.commit()
            print("Usuário admin atualizado/criado com sucesso!")
            
            # Verificar usuário
            admin = db.fetchone("SELECT * FROM usuarios WHERE usuario = 'admin'")
            if admin:
                print(f"  - ID: {admin['id']}")
                print(f"  - Nome: {admin['nome']}")
                print(f"  - Usuário: {admin['usuario']}")
                print(f"  - is_admin: {admin['is_admin']}")
                print(f"  - ativo: {admin['ativo']}")
                print(f"  - nivel: {admin['nivel']}")
            else:
                print("Falha ao encontrar usuário admin após atualização!")
            
            # Testar login
            print("\nTestando login com usuário admin:")
            user = db.verificar_login("admin", "842384")
            
            if user:
                print("  - Login bem-sucedido!")
                print(f"  - Dados do usuário: {user}")
            else:
                print("  - Falha no login!")
                
        except Exception as e:
            print(f"Erro ao atualizar usuário admin: {e}")
            db.conn.rollback()
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return

if __name__ == "__main__":
    main()