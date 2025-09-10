#!/usr/bin/env python3
"""
Utilitário para redefinir/criar usuário admin no banco local do PDV3 (SQLite).

- Descobre automaticamente o caminho do banco via database.Database
- Por padrão, usa usuario=admin e senha=admin
- Pode receber parâmetros via linha de comando:
    --usuario <nome_usuario>
    --senha <senha>

Exemplos:
    python tools/reset_local_admin_password.py
    python tools/reset_local_admin_password.py --usuario admin --senha 123456
"""
from __future__ import annotations
import argparse
import datetime
import sqlite3
import uuid
import sys

try:
    from werkzeug.security import generate_password_hash
except Exception as e:
    print("[ERRO] werkzeug não encontrado. Instale com: pip install werkzeug")
    sys.exit(1)

# Descobrir o caminho do banco do app
try:
    from database.database import Database
    DB_PATH = Database().db_path
except Exception:
    # Fallback comum (Windows)
    import os
    DB_PATH = os.path.expandvars(r"%APPDATA%\SistemaGestao\database\sistema.db")


def reset_admin(usuario: str = "admin", senha: str = "842384") -> None:
    print(f"[INFO] Banco local: {DB_PATH}")
    print(f"[INFO] Definindo/atualizando usuario='{usuario}' (admin) com senha fornecida...")
    # Usar PBKDF2 (padrão do Werkzeug) para padronização com o restante do sistema
    h = generate_password_hash(senha)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    now = datetime.datetime.now().isoformat()

    # Verifica se existe um usuário com esse nome de usuário
    cur.execute("""
        SELECT id, nome, usuario, is_admin, ativo FROM usuarios
        WHERE LOWER(usuario) = LOWER(?)
    """, (usuario,))
    row = cur.fetchone()

    affected = 0
    if row:
        # Atualiza o usuário existente
        cur.execute(
            """
            UPDATE usuarios
               SET senha = ?, is_admin = 1, ativo = 1, updated_at = ?
             WHERE LOWER(usuario) = LOWER(?)
            """,
            (h, now, usuario)
        )
        affected = cur.rowcount
        print(f"[OK] Usuário existente atualizado: {usuario}")
    else:
        # Caso não exista, cria um novo
        cur.execute(
            """
            INSERT INTO usuarios (nome, usuario, senha, nivel, is_admin, ativo, salario,
                                  created_at, updated_at, uuid, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("Administrador", usuario, h, 1, 1, 1, 0.0,
             now, now, str(uuid.uuid4()), 0)
        )
        affected = 1
        print(f"[OK] Usuário admin criado: {usuario}")

    conn.commit()

    # Mostra um resumo dos admins
    print("\n[INFO] Usuários admin ativos:")
    cur.execute(
        """
        SELECT id, nome, usuario, is_admin, ativo
          FROM usuarios
         WHERE is_admin = 1 AND ativo = 1
         ORDER BY usuario
        """
    )
    for r in cur.fetchall():
        print(r)

    conn.close()
    print(f"\n[SUCESSO] Registros afetados: {affected}. Usuario '{usuario}' pronto para login.")


def main():
    parser = argparse.ArgumentParser(description="Redefine/Cria usuário admin no banco local do PDV3")
    parser.add_argument("--usuario", default="admin", help="Nome de usuário (default: admin)")
    parser.add_argument("--senha", default="842384", help="Senha (default: 842384 - padrão do database.py)")
    args = parser.parse_args()

    reset_admin(usuario=args.usuario, senha=args.senha)


if __name__ == "__main__":
    main()
