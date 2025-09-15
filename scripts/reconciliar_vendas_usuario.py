#!/usr/bin/env python3
"""
Reconciliar vendedor das vendas no servidor a partir do banco local (SQLite).

- Lê do SQLite local: vendas.uuid, vendas.usuario_id (inteiro local) e usuarios.uuid
- Para cada venda com mapeamento disponível (usuario_uuid), envia PUT /api/vendas/{venda_uuid}
  definindo o campo usuario_id como UUID do usuário no servidor.

Uso (Windows PowerShell):
  # Backend local
  $env:BACKEND_URL="http://localhost:8000"
  python pdv3/scripts/reconciliar_vendas_usuario.py --limit 200

  # Backend em produção
  $env:BACKEND_URL="https://seu-backend.exemplo.app"
  python pdv3/scripts/reconciliar_vendas_usuario.py

Parâmetros:
  --backend   URL base do backend (override de BACKEND_URL)
  --limit     Limitar quantidade processada
  --dry-run   Não envia PUT; apenas mostra o que faria
  --timeout   Timeout em segundos para chamadas HTTP (padrão 10)
"""
from __future__ import annotations
import os
import sys
import sqlite3
import argparse
from typing import Optional, List, Tuple
import httpx
import json


def _make_api_base(base_url: str) -> str:
    base = (base_url or "http://localhost:8000").rstrip('/')
    if base.endswith('/api'):
        return base
    return base + '/api'


def _get_db_path() -> str:
    """Obtém o caminho REAL do banco (APPDATA) como o app usa.
    Insere o root do projeto no sys.path para garantir import do Database."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from database.database import Database
        db = Database()
        # Database.db_path pode ser Path; converter para str
        return str(db.db_path)
    except Exception as e:
        print(f"[RECONCILIAR] Aviso: falha ao obter db_path via Database(): {e}")
        # Fallback relativo ao repositório (pode não conter as tabelas reais)
        return os.path.join(project_root, 'database', 'sistema.db')


def _load_mapeamentos(conn: sqlite3.Connection, limit: Optional[int] = None) -> List[Tuple[str, int, Optional[str]]]:
    cur = conn.cursor()
    sql = (
        """
        SELECT v.uuid AS venda_uuid,
               v.usuario_id AS usuario_local_id,
               u.uuid AS usuario_uuid
        FROM vendas v
        LEFT JOIN usuarios u ON u.id = v.usuario_id
        WHERE v.uuid IS NOT NULL
          AND TRIM(v.uuid) <> ''
          AND v.usuario_id IS NOT NULL
        ORDER BY v.id ASC
        """
    )
    if limit:
        sql += " LIMIT ?"
        cur.execute(sql, (int(limit),))
    else:
        cur.execute(sql)
    rows = []
    for venda_uuid, usuario_local_id, usuario_uuid in cur.fetchall():
        rows.append((str(venda_uuid), int(usuario_local_id), (usuario_uuid.strip() if usuario_uuid else None)))
    return rows


def _listar_resumo(conn: sqlite3.Connection, limit: Optional[int] = None) -> None:
    """Lista um resumo dos vendedores com contagem de vendas locais mapeáveis.
    Mostra id/nome/uuid do usuário local e quantidade de vendas com uuid de venda presente.
    """
    cur = conn.cursor()
    # Resumo atual baseado na coluna vendas.usuario_id
    sql = (
        """
        SELECT u.id AS usuario_local_id,
               COALESCE(u.nome, 'DESCONHECIDO') AS nome,
               COALESCE(u.uuid, '') AS usuario_uuid,
               COUNT(1) AS qtd_vendas
        FROM vendas v
        LEFT JOIN usuarios u ON u.id = v.usuario_id
        WHERE v.uuid IS NOT NULL AND TRIM(v.uuid) <> '' AND v.usuario_id IS NOT NULL
        GROUP BY u.id, u.nome, u.uuid
        ORDER BY qtd_vendas DESC
        """
    )
    cur.execute(sql)
    rows = cur.fetchall()
    print("\n[RESUMO VENDEDORES]")
    if not rows:
        print("Nenhum vendedor encontrado para reconciliar.")
    else:
        print(f"Total de vendedores com vendas mapeáveis: {len(rows)}")
        print("id_local | nome | uuid | qtd_vendas")
        print("-" * 80)
        shown = 0
        for usuario_local_id, nome, usuario_uuid, qtd in rows:
            print(f"{usuario_local_id} | {nome} | {usuario_uuid} | {qtd}")
            shown += 1
            if limit and shown >= int(limit):
                break

    # Resumo alternativo com base no change_log (originais)
    try:
        print("\n[RESUMO ORIGINAIS (change_log)]")
        cur.execute(
            """
            SELECT cl.entity_id AS venda_uuid, cl.data_json
            FROM change_log cl
            WHERE cl.entity_type = 'vendas' AND cl.operation IN ('CREATE','UPDATE')
            """
        )
        registros = cur.fetchall()
        # Map venda_uuid -> ultimo usuario_id informado no change_log
        venda_to_user: dict[str, int] = {}
        for venda_uuid, data_json in registros:
            try:
                data = json.loads(data_json) if data_json else {}
                uid = data.get('usuario_id')
                if isinstance(uid, int):
                    venda_to_user[str(venda_uuid)] = uid
            except Exception:
                pass
        if not venda_to_user:
            print("Nenhum dado de vendedor encontrado no change_log.")
            return
        # Agregar por usuario_id original
        resumo: dict[int, int] = {}
        for uid in venda_to_user.values():
            resumo[uid] = resumo.get(uid, 0) + 1
        # Obter nomes/uuids
        usuarios_info: dict[int, Tuple[str,str]] = {}
        cur.execute("SELECT id, nome, COALESCE(uuid,'') FROM usuarios")
        for uid, nome, u_uuid in cur.fetchall():
            usuarios_info[int(uid)] = (nome or 'DESCONHECIDO', u_uuid or '')
        print("id_local | nome | uuid | qtd_vendas_change_log")
        print("-" * 80)
        shown2 = 0
        for uid, qtd in sorted(resumo.items(), key=lambda x: x[1], reverse=True):
            nome, u_uuid = usuarios_info.get(uid, ("DESCONHECIDO",""))
            print(f"{uid} | {nome} | {u_uuid} | {qtd}")
            shown2 += 1
            if limit and shown2 >= int(limit):
                break
    except Exception as e:
        print(f"[AVISO] Falha ao gerar resumo por change_log: {e}")
    print(f"Total de vendedores com vendas mapeáveis: {len(rows)}")
    print("id_local | nome | uuid | qtd_vendas")
    print("-" * 80)
    shown = 0
    for usuario_local_id, nome, usuario_uuid, qtd in rows:
        print(f"{usuario_local_id} | {nome} | {usuario_uuid} | {qtd}")
        shown += 1
        if limit and shown >= int(limit):
            break


def reconciliar(backend_url: str, limit: Optional[int], dry_run: bool, timeout: float, listar: bool = False) -> None:
    db_path = _get_db_path()
    print(f"[RECONCILIAR] Banco local: {db_path}")
    print(f"[RECONCILIAR] Backend: {backend_url}")
    api_base = _make_api_base(backend_url)

    with sqlite3.connect(db_path) as conn:
        if listar:
            _listar_resumo(conn, limit)
            return
        mapeamentos = _load_mapeamentos(conn, limit)

    total = len(mapeamentos)
    sem_usuario_uuid = 0
    atualizados = 0
    not_found = 0
    erros = 0

    if total == 0:
        print("[RECONCILIAR] Nenhuma venda com usuario_id local encontrada para processar.")
        return

    print(f"[RECONCILIAR] Encontradas {total} vendas para reconciliar.")

    client = httpx.Client(timeout=timeout)
    try:
        for idx, (venda_uuid, usuario_local_id, usuario_uuid) in enumerate(mapeamentos, start=1):
            if not usuario_uuid:
                sem_usuario_uuid += 1
                print(f"[{idx}/{total}] PULANDO venda {venda_uuid}: usuário local {usuario_local_id} sem uuid mapeado.")
                continue

            payload = {"usuario_id": usuario_uuid}
            url = f"{api_base}/vendas/{venda_uuid}"

            if dry_run:
                print(f"[{idx}/{total}] DRY-RUN: PUT {url} -> {payload}")
                continue

            try:
                r = client.put(url, json=payload)
                if r.status_code == 200:
                    atualizados += 1
                    print(f"[{idx}/{total}] OK venda {venda_uuid} -> usuario {usuario_uuid}")
                elif r.status_code == 404:
                    not_found += 1
                    print(f"[{idx}/{total}] NAO ENCONTRADA venda {venda_uuid}")
                else:
                    erros += 1
                    print(f"[{idx}/{total}] ERRO {r.status_code} venda {venda_uuid}: {r.text}")
            except Exception as e:
                erros += 1
                print(f"[{idx}/{total}] EXCECAO ao atualizar venda {venda_uuid}: {e}")
    finally:
        client.close()

    print("\n[RECONCILIAR] Resumo:")
    print(f"  Total analisadas:    {total}")
    print(f"  Atualizadas:         {atualizados}")
    print(f"  Não encontradas:     {not_found}")
    print(f"  Sem usuario_uuid:    {sem_usuario_uuid}")
    print(f"  Erros:               {erros}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconciliar vendedor das vendas no servidor")
    parser.add_argument("--backend", type=str, default=os.getenv("BACKEND_URL", "http://localhost:8000"), help="URL do backend")
    parser.add_argument("--limit", type=int, default=None, help="Limitar quantidade de vendas processadas")
    parser.add_argument("--dry-run", action="store_true", help="Não enviar PUT; apenas mostrar o que faria")
    parser.add_argument("--listar", action="store_true", help="Listar resumo dos vendedores antes de aplicar")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout HTTP em segundos")
    args = parser.parse_args()

    reconciliar(args.backend, args.limit, args.dry_run, args.timeout, args.listar)
