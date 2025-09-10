#!/usr/bin/env python3
"""
Teste rápido de login local usando a mesma lógica do app (Database.verificar_login).
"""
from database.database import Database


def main():
    db = Database()
    print(f"[INFO] DB usado: {db.db_path}")

    # Buscar usuários ativos
    users = db.fetchall(
        """
        SELECT usuario FROM usuarios
        WHERE ativo = 1
        ORDER BY usuario
        """
    ) or []

    candidates = ["123456", "842384"]

    if not users:
        print("[WARN] Nenhum usuário ativo encontrado.")
        return

    total_ok = 0
    for row in users:
        usr = row[0] if isinstance(row, tuple) else (row.get("usuario") if isinstance(row, dict) else row["usuario"])  # suporta dict/tuple/row
        print(f"\n[Teste] Usuario: {usr}")
        ok_any = False
        for pwd in candidates:
            res = db.verificar_login(usr, pwd)
            if res:
                print(f"  [OK] Login com senha '{pwd}'")
                ok_any = True
        if not ok_any:
            print("  [FAIL] Nenhuma senha padrão funcionou (123456/842384)")
        else:
            total_ok += 1

    print(f"\n[RESUMO] {total_ok}/{len(users)} usuários aceitaram pelo menos uma senha padrão.")


if __name__ == "__main__":
    main()
