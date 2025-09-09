#!/usr/bin/env python3
"""
Teste rápido de login local usando a mesma lógica do app (Database.verificar_login).
"""
from database.database import Database

def main():
    db = Database()
    print(f"[INFO] DB usado: {db.db_path}")
    for user, pwd in [("admin", "admin")]:
        u = db.verificar_login(user, pwd)
        if u:
            print(f"[OK] Login funcionou para {user} -> {u}")
        else:
            print(f"[FAIL] Login falhou para {user}")

if __name__ == "__main__":
    main()
