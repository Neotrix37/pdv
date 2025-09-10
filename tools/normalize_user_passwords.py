#!/usr/bin/env python3
"""
Normaliza senhas de usuários no banco local do PDV3 (SQLite):
- Converte senhas em texto puro para hash (PBKDF2 via Werkzeug)
- Para senhas vazias, define uma senha inicial (por padrão 842384)
- Pode atuar em TODOS os usuários ou em apenas um usuário específico

Uso:
  python tools/normalize_user_passwords.py                 # normaliza todos (vazias => 842384)
  python tools/normalize_user_passwords.py --usuario USER  # normaliza apenas USER (vazia => 842384)
  python tools/normalize_user_passwords.py --usuario USER --senha NOVA_SENHA
  python tools/normalize_user_passwords.py --senha NOVA_SENHA  # define esta senha para todos os que estavam inválidos

Observação:
- O script detecta senhas já hasheadas (prefixos pbkdf2: ou $2a$/$2b$/$2y$) e NÃO altera essas.
- Banco alvo é o mesmo utilizado pelo app: %APPDATA%/SistemaGestao/database/sistema.db
"""
from __future__ import annotations
import argparse
import os
import sqlite3
import sys

try:
    from werkzeug.security import generate_password_hash
except Exception:
    print("[ERRO] werkzeug não encontrado. Instale com: pip install werkzeug")
    sys.exit(1)

# Descobrir o caminho do banco do app
try:
    from database.database import Database
    DB_PATH = str(Database().db_path)
except Exception:
    DB_PATH = os.path.expandvars(r"%APPDATA%\SistemaGestao\database\sistema.db")

HASH_PREFIXES = ("pbkdf2:", "$2a$", "$2b$", "$2y$")


def is_hashed(value: str) -> bool:
    v = value or ""
    return v.startswith(HASH_PREFIXES)


def normalize_all(default_password: str | None) -> int:
    """Normaliza todos os usuários com senha vazia/plain.
    Retorna a quantidade atualizada.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute("SELECT id, usuario, senha FROM usuarios").fetchall()
    updated = 0
    for uid, usr, s in rows:
        s = s or ""
        if not is_hashed(s):
            # Se está vazio/plain, define hash da senha atual, ou default_password se vazio
            new_plain = s if s else (default_password or "842384")
            try:
                h = generate_password_hash(new_plain)
                cur.execute("UPDATE usuarios SET senha=?, ativo=1 WHERE id=?", (h, uid))
                updated += 1
                print(f"[OK] Usuario='{usr}' atualizado (hash gerado)")
            except Exception as e:
                print(f"[WARN] Falha ao atualizar usuario='{usr}': {e}")
    conn.commit()
    conn.close()
    return updated


def normalize_single(usuario: str, new_password: str | None) -> int:
    """Normaliza um único usuário. Se new_password for informado, define essa senha.
    Retorna 1 se atualizado, 0 caso contrário.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, usuario, senha FROM usuarios WHERE LOWER(usuario)=LOWER(?)",
        (usuario,),
    ).fetchone()
    if not row:
        print(f"[INFO] Usuario '{usuario}' não encontrado.")
        conn.close()
        return 0

    uid, usr, s = row[0], row[1], row[2] or ""

    # Se já está hasheada e não pediram nova senha, não altera
    if is_hashed(s) and not new_password:
        print(f"[SKIP] Usuario='{usr}' já possui hash válido. Nenhuma alteração.")
        conn.close()
        return 0

    # Determinar senha plain a ser hasheada
    plain = new_password or (s if s and not is_hashed(s) else "842384")

    try:
        h = generate_password_hash(plain)
        cur.execute("UPDATE usuarios SET senha=?, ativo=1 WHERE id=?", (h, uid))
        conn.commit()
        print(f"[DONE] Usuario='{usr}' atualizado com sucesso.")
        return 1
    except Exception as e:
        print(f"[ERRO] Falha ao atualizar usuario='{usr}': {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Normaliza senhas dos usuários (gera hash e corrige vazias)")
    parser.add_argument("--usuario", help="Atua apenas neste usuário (default: todos)")
    parser.add_argument("--senha", help="Define esta senha para o(s) usuário(s) afetado(s)")
    args = parser.parse_args()

    print(f"[INFO] Banco local: {DB_PATH}")

    if args.usuario:
        count = normalize_single(args.usuario, args.senha)
        print(f"[RESUMO] Atualizados: {count}")
        return

    # Sem --usuario: processa todos
    count = normalize_all(args.senha)
    print(f"[RESUMO] Atualizados: {count}")


if __name__ == "__main__":
    main()
