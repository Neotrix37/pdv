import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

BACKUP_DIR = Path(__file__).resolve().parents[1] / "backups"

CORE_TABLES = [
    ("produtos", "SELECT COUNT(*) FROM produtos"),
    ("usuarios", "SELECT COUNT(*) FROM usuarios"),
    ("clientes", "SELECT COUNT(*) FROM clientes"),
    ("vendas", "SELECT COUNT(*) FROM vendas"),
]

VENDAS_SUMMARY_SQL = {
    "total_vendas": "SELECT COUNT(*) FROM vendas",
    "min_data": "SELECT MIN(data_venda) FROM vendas",
    "max_data": "SELECT MAX(data_venda) FROM vendas",
    "vendas_hoje": "SELECT COUNT(*) FROM vendas WHERE DATE(data_venda) = DATE('now')",
    "total_valor": "SELECT COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) FROM vendas",
}


def list_backups() -> List[Tuple[str, Path, float, datetime]]:
    """Return list of backups: (filename, path, size_mb, mtime)."""
    if not BACKUP_DIR.exists():
        return []
    backups = []
    for f in BACKUP_DIR.iterdir():
        if f.is_file() and f.suffix.lower() == ".db":
            try:
                stat = f.stat()
                size_mb = stat.st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(stat.st_mtime)
                backups.append((f.name, f, size_mb, mtime))
            except Exception:
                pass
    backups.sort(key=lambda x: x[3], reverse=True)
    return backups


def print_backups(backups: List[Tuple[str, Path, float, datetime]]):
    if not backups:
        print("Nenhum backup encontrado em:", BACKUP_DIR)
        return
    print(f"Backups em {BACKUP_DIR} (mais recentes primeiro):\n")
    for idx, (name, path, size_mb, mtime) in enumerate(backups, start=1):
        print(f"[{idx:02d}] {name}  |  {size_mb:.2f} MB  |  {mtime.strftime('%Y-%m-%d %H:%M:%S')}")


def inspect_backup(backup_path: Path):
    if not backup_path.exists():
        print(f"Arquivo não encontrado: {backup_path}")
        sys.exit(1)
    size = backup_path.stat().st_size
    print(f"\nInspecionando: {backup_path}")
    print(f"Tamanho: {size} bytes ({size/(1024*1024):.2f} MB)")
    if size < 1024 * 200:  # < 200 KB
        print("AVISO: Este backup é muito pequeno. Pode estar vazio/corrompido.")
    try:
        conn = sqlite3.connect(str(backup_path))
        cur = conn.cursor()
        # Listar tabelas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        print("\nTabelas encontradas:")
        if not tables:
            print("  - (nenhuma)")
        else:
            for t in tables:
                print(f"  - {t}")
        # Core tables counts
        print("\nResumo de tabelas principais:")
        for label, sql in CORE_TABLES:
            try:
                cur.execute(sql)
                cnt = cur.fetchone()[0]
                print(f"  {label:10s}: {cnt}")
            except Exception as e:
                print(f"  {label:10s}: erro ({e})")
        # Vendas summary
        print("\nResumo de vendas:")
        for label, sql in VENDAS_SUMMARY_SQL.items():
            try:
                cur.execute(sql)
                val = cur.fetchone()[0]
                print(f"  {label:12s}: {val}")
            except Exception as e:
                print(f"  {label:12s}: erro ({e})")
        # Amostra de 5 vendas mais recentes
        try:
            print("\nAmostra de 5 vendas mais recentes:")
            cur.execute(
                """
                SELECT id, data_venda, total, forma_pagamento, status
                FROM vendas
                ORDER BY data_venda DESC
                LIMIT 5
                """
            )
            rows = cur.fetchall()
            if not rows:
                print("  (sem registros)")
            else:
                for r in rows:
                    print(f"  id={r[0]} | data={r[1]} | total={r[2]} | pgto={r[3]} | status={r[4]}")
        except Exception as e:
            print(f"  erro ao listar amostra de vendas: {e}")
    except Exception as e:
        print(f"Erro ao abrir o backup: {e}")
        sys.exit(1)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Listar e inspecionar backups do PDV3")
    parser.add_argument("--list", action="store_true", help="Apenas listar backups e sair")
    parser.add_argument("--file", type=str, help="Caminho completo de um backup .db para inspecionar")
    args = parser.parse_args()

    backups = list_backups()
    if args.list:
        print_backups(backups)
        return

    if args.file:
        inspect_backup(Path(args.file))
        return

    if not backups:
        print("Nenhum backup encontrado.")
        return

    print_backups(backups)
    # Prompt interativo
    while True:
        try:
            sel = input("\nDigite o número do backup para inspecionar (ou ENTER para sair): ").strip()
            if sel == "":
                print("Saindo.")
                return
            idx = int(sel)
            if 1 <= idx <= len(backups):
                _, path, _, _ = backups[idx - 1]
                inspect_backup(path)
                return
            else:
                print("Número inválido. Tente novamente.")
        except ValueError:
            print("Entrada inválida. Digite um número válido.")


if __name__ == "__main__":
    main()
