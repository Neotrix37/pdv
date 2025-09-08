#!/usr/bin/env python3
"""
Script para verificar a estrutura da tabela de usuários e testar o login
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import Database
from werkzeug.security import generate_password_hash

def main():
    print("=== Script de Verificação de Usuários ===\n")
    
    try:
        # Conectar ao banco de dados
        db = Database()
        
        # Verificar estrutura da tabela de usuários
        print("Estrutura da tabela de usuários:")
        cursor = db.conn.cursor()
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  - {col[1]}: {col[2]} (NOT NULL: {col[3]}, Default: {col[4]})")
        
        # Verificar se existe o usuário admin
        print("\nVerificando usuário admin:")
        admin = db.fetchone("SELECT * FROM usuarios WHERE usuario = 'admin'")
        
        if admin:
            print(f"  - ID: {admin['id']}")
            print(f"  - Nome: {admin['nome']}")
            print(f"  - Usuário: {admin['usuario']}")
            print(f"  - is_admin: {admin['is_admin']}")
            print(f"  - ativo: {admin['ativo']}")
            if 'nivel' in admin.keys():
                print(f"  - nivel: {admin['nivel']}")
            if 'salario' in admin.keys():
                print(f"  - salario: {admin['salario']}")
        else:
            print("  - Usuário admin não encontrado!")
            
            # Criar usuário admin
            print("\nCriando usuário admin...")
            senha_hash = generate_password_hash("842384")
            
            try:
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
                print("  - Usuário admin criado com sucesso!")
                
                # Verificar se foi criado
                admin = db.fetchone("SELECT * FROM usuarios WHERE usuario = 'admin'")
                if admin:
                    print(f"  - ID: {admin['id']}")
                    print(f"  - Nome: {admin['nome']}")
                    print(f"  - Usuário: {admin['usuario']}")
                    print(f"  - is_admin: {admin['is_admin']}")
                    print(f"  - ativo: {admin['ativo']}")
                else:
                    print("  - Falha ao criar usuário admin!")
            except Exception as e:
                print(f"  - Erro ao criar usuário admin: {e}")
        
        # Testar login
        print("\nTestando login com usuário admin:")
        user = db.verificar_login("admin", "842384")
        
        if user:
            print("  - Login bem-sucedido!")
            print(f"  - Dados do usuário: {user}")
        else:
            print("  - Falha no login!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return

if __name__ == "__main__":
    main()