import sqlite3
import httpx
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import os
import json
from utils.migration_helper import MigrationHelper

class VendaRepository:
    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or self._get_backend_url()
        # Base normalizada da API: garante exatamente um sufixo /api
        self.api_base = self._make_api_base(self.backend_url)
        self.db_path = self._get_database_path()
        self._ensure_migration()
        self._ensure_change_log_table()
        # Acompanhar avisos do último pull
        self._last_missing_products = set()

    def _get_usuario_uuid_by_id(self, local_usuario_id):
        """Busca o UUID de um usuário pelo ID local."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # Espera-se que a tabela usuarios tenha coluna 'uuid'
                cur.execute("SELECT uuid FROM usuarios WHERE id = ?", (int(local_usuario_id),))
                row = cur.fetchone()
                if row:
                    uuid_val = (row[0] or '').strip()
                    if uuid_val:
                        return uuid_val
                return None
        except Exception as e:
            print(f"Erro ao buscar UUID do usuário {local_usuario_id}: {e}")
            return None

    def _buscar_usuario_por_uuid(self, uuid_str):
        """Busca o ID local de um usuário pelo UUID."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT id FROM usuarios WHERE uuid = ?", (uuid_str,))
                row = cur.fetchone()
                if row:
                    return row[0]
                return None
        except Exception as e:
            print(f"Erro ao buscar usuário por UUID {uuid_str}: {e}")
            return None

    def _get_user_uuid(self, local_usuario_id: Optional[int]) -> Optional[str]:
        """Retorna o UUID (string) do usuário no servidor, a partir do id local.
        Se não encontrar, retorna None."""
        return self._get_usuario_uuid_by_id(local_usuario_id)

    def _get_default_usuario_id(self) -> int:
        """Obtém um usuário local padrão para atribuir às vendas vindas do servidor.
        Preferir admin; caso contrário, o primeiro usuário disponível; fallback para 1.
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # Tentar admin
                try:
                    cur.execute("SELECT id FROM usuarios WHERE is_admin = 1 AND ativo = 1 ORDER BY id LIMIT 1")
                    row = cur.fetchone()
                    if row and row[0]:
                        return int(row[0])
                except Exception:
                    pass
                # Qualquer usuário ativo
                cur.execute("SELECT id FROM usuarios WHERE ativo = 1 ORDER BY id LIMIT 1")
                row = cur.fetchone()
                if row and row[0]:
                    return int(row[0])
        except Exception:
            pass
        return 1
    
    def _get_backend_url(self) -> str:
        """Obtém a URL do backend do arquivo de configuração."""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('server_url', 'http://localhost:8000')
        except Exception:
            pass
        return os.getenv("BACKEND_URL", "http://localhost:8000")

    def _make_api_base(self, base_url: str) -> str:
        """Normaliza a base da API para conter exatamente um /api no final."""
        if base_url.endswith('/api'):
            return base_url
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        return base_url + '/api'
    
    def _get_database_path(self) -> Path:
        """Obtém o caminho do banco de dados baseado no sistema operacional."""
        # Usar o caminho central do app para evitar divergências
        try:
            from database.database import Database
            db = Database()
            return Path(db.db_path)
        except Exception:
            return Path(__file__).parent.parent / 'database' / 'sistema.db'
    
    def _is_online(self) -> bool:
        """Verifica se o backend está online (versão síncrona)."""
        try:
            # Usar URL base sem /api para healthcheck
            base_url = self.backend_url.replace('/api', '')
            healthcheck_url = f"{base_url}/healthz"
            response = httpx.get(healthcheck_url, timeout=3.0)
            is_online = response.status_code == 200
            print(f"🔗 Status conexão: {'ONLINE' if is_online else 'OFFLINE'} - {healthcheck_url}")
            return is_online
        except Exception as e:
            print(f"❌ Erro ao verificar conexão: {e}")
            return False
    
    async def is_backend_online(self) -> bool:
        """Versão assíncrona para verificar se o backend está online."""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
                    # Tenta healthz na base informada
                    try:
                        r1 = await client.get(f"{self.backend_url}/healthz")
                        if r1.status_code == 200:
                            return True
                    except Exception:
                        pass

                    # Fallback sem /api quando aplicável
                    if self.backend_url.endswith('/api'):
                        base_url = self.backend_url[:-4]
                        try:
                            r2 = await client.get(f"{base_url}/healthz")
                            if r2.status_code == 200:
                                return True
                        except Exception:
                            pass
            except Exception:
                pass

            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(1)

        return False
    
    def _ensure_migration(self):
        """Garante que as colunas de sincronização existam na tabela vendas."""
        try:
            migration_helper = MigrationHelper()
            if migration_helper.check_migration_needed():
                print("[VENDA_REPO] Executando migração automática...")
                migration_helper.migrate_vendas_table()
        except Exception as e:
            print(f"[VENDA_REPO] Erro durante migração: {e}")
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Obtém todas as vendas (híbrido: servidor primeiro, fallback local)."""
        if self._is_online():
            try:
                response = httpx.get(f"{self.api_base}/vendas/", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Erro ao buscar vendas do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_all_local()
    
    def _get_all_local(self) -> List[Dict[str, Any]]:
        """Obtém todas as vendas do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, usuario_id, total, forma_pagamento, valor_recebido, troco,
                       data_venda, status, motivo_alteracao, alterado_por, data_alteracao,
                       origem, valor_original_divida, desconto_aplicado_divida,
                       COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                FROM vendas 
                ORDER BY data_venda DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_id(self, venda_id: int) -> Optional[Dict[str, Any]]:
        """Obtém venda por ID (híbrido)."""
        if self._is_online():
            try:
                # Buscar UUID da venda local
                venda_local = self._get_local_venda_by_id(venda_id)
                if venda_local and venda_local.get('uuid'):
                    response = httpx.get(
                        f"{self.api_base}/vendas/{venda_local['uuid']}", 
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        return response.json()
            except Exception as e:
                print(f"Erro ao buscar venda do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_local_venda_by_id(venda_id)
    
    def _get_local_venda_by_id(self, venda_id: int) -> Optional[Dict[str, Any]]:
        """Obtém venda por ID do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, usuario_id, total, forma_pagamento, valor_recebido, troco,
                       data_venda, status, motivo_alteracao, alterado_por, data_alteracao,
                       origem, valor_original_divida, desconto_aplicado_divida,
                       COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                FROM vendas 
                WHERE id = ?
            """, (venda_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create(self, venda_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cria nova venda (híbrido)."""
        # Gerar UUID se não existir
        if 'uuid' not in venda_data or not venda_data['uuid']:
            venda_data['uuid'] = str(uuid.uuid4())
        
        # Tentar criar no servidor primeiro
        if self._is_online():
            try:
                # Mapear usuario_id local -> uuid do servidor
                try:
                    local_uid = venda_data.get('usuario_id')
                    mapped_uuid = self._get_user_uuid(local_uid)
                    if mapped_uuid:
                        venda_data['usuario_id'] = mapped_uuid
                    else:
                        # Se não mapeou, enviar None para evitar erro 400
                        venda_data['usuario_id'] = None
                except Exception:
                    venda_data['usuario_id'] = None
                response = httpx.post(
                    f"{self.api_base}/vendas/",
                    json=venda_data,
                    timeout=5.0
                )
                if response.status_code in [200, 201]:
                    venda_data['synced'] = 1
                    server_venda = response.json()
                    venda_data.update(server_venda)
                    print("Venda criada no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao criar venda no servidor: {e}")
        else:
            print("Backend offline, venda sera criada apenas localmente")
        
        # Sempre criar localmente
        venda_criada = self._create_local_venda(venda_data)
        
        # Log para sincronização se não foi sincronizado
        if venda_data.get('synced', 0) == 0:
            self._log_change(venda_data['uuid'], 'CREATE', venda_data)
        
        return venda_criada
    
    def _create_local_venda(self, venda_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria venda no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vendas (usuario_id, total, forma_pagamento, valor_recebido, 
                                  troco, data_venda, status, motivo_alteracao, alterado_por,
                                  data_alteracao, origem, valor_original_divida, 
                                  desconto_aplicado_divida, uuid, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                venda_data.get('usuario_id'),
                venda_data.get('total', 0.0),
                venda_data.get('forma_pagamento', 'dinheiro'),
                venda_data.get('valor_recebido', 0.0),
                venda_data.get('troco', 0.0),
                venda_data.get('data_venda', datetime.now().isoformat()),
                venda_data.get('status', 'concluida'),
                venda_data.get('motivo_alteracao', ''),
                venda_data.get('alterado_por'),
                venda_data.get('data_alteracao'),
                venda_data.get('origem', 'local'),
                venda_data.get('valor_original_divida', 0.0),
                venda_data.get('desconto_aplicado_divida', 0.0),
                venda_data['uuid'],
                venda_data.get('synced', 0)
            ))
            
            venda_id = cursor.lastrowid
            conn.commit()
            
            # Retornar venda criada
            return self._get_local_venda_by_id(venda_id)
    
    def update(self, venda_id: int, venda_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza venda (híbrido)."""
        # Obter UUID da venda local
        venda_local = self._get_local_venda_by_id(venda_id)
        if not venda_local:
            return None
        
        venda_uuid = venda_local['uuid']
        
        # Tentar atualizar no servidor
        if self._is_online():
            try:
                response = httpx.put(
                    f"{self.api_base}/vendas/{venda_uuid}",
                    json=venda_data,
                    timeout=5.0
                )
                if response.status_code == 200:
                    venda_data['synced'] = 1
                    server_venda = response.json()
                    venda_data.update(server_venda)
                    print("Venda atualizada no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao atualizar venda no servidor: {e}")
        else:
            print("Backend offline, venda sera atualizada apenas localmente")
        
        # Sempre atualizar localmente
        venda_atualizada = self._update_local_venda(venda_id, venda_data)
        
        # Log para sincronização se não foi sincronizado
        if venda_data.get('synced', 0) == 0:
            self._log_change(venda_uuid, 'UPDATE', venda_data)
        
        return venda_atualizada
    
    def _update_local_venda(self, venda_id: int, venda_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza venda no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vendas 
                SET usuario_id = ?, total = ?, forma_pagamento = ?, valor_recebido = ?,
                    troco = ?, status = ?, motivo_alteracao = ?, alterado_por = ?,
                    data_alteracao = ?, origem = ?, valor_original_divida = ?,
                    desconto_aplicado_divida = ?, synced = ?
                WHERE id = ?
            """, (
                venda_data.get('usuario_id'),
                venda_data.get('total', 0.0),
                venda_data.get('forma_pagamento', 'dinheiro'),
                venda_data.get('valor_recebido', 0.0),
                venda_data.get('troco', 0.0),
                venda_data.get('status', 'concluida'),
                venda_data.get('motivo_alteracao', ''),
                venda_data.get('alterado_por'),
                datetime.now().isoformat(),
                venda_data.get('origem', 'local'),
                venda_data.get('valor_original_divida', 0.0),
                venda_data.get('desconto_aplicado_divida', 0.0),
                venda_data.get('synced', 0),
                venda_id
            ))
            conn.commit()
            
            # Retornar venda atualizada
            return self._get_local_venda_by_id(venda_id)
    
    def delete(self, venda_id: int) -> bool:
        """Deleta venda (soft delete híbrido)."""
        venda_local = self._get_local_venda_by_id(venda_id)
        if not venda_local:
            return False
        
        venda_uuid = venda_local['uuid']
        
        # Tentar deletar no servidor
        if self._is_online():
            try:
                response = httpx.delete(
                    f"{self.api_base}/vendas/{venda_uuid}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    print("Venda deletada no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao deletar venda no servidor: {e}")
        
        # Soft delete local (marcar como cancelada)
        success = self._soft_delete_local_venda(venda_id)
        
        # Log para sincronização
        if success:
            self._log_change(venda_uuid, 'DELETE', {})
        
        return success

    def cancelar_venda(self, venda_id_local: int, motivo: str = "") -> bool:
        """Anula uma venda: marca como cancelada/Anulada no servidor e local.
        - Servidor: PUT /api/vendas/{uuid} com { cancelada: true }
        - Local: status='Anulada', motivo_alteracao, data_alteracao=now
        - Se offline: apenas local + registra no change_log para envio posterior.
        """
        # Obter UUID da venda local
        venda_local = self._get_local_venda_by_id(venda_id_local)
        if not venda_local:
            return False
        venda_uuid = venda_local.get('uuid')

        # Tentar atualizar no servidor
        updated_remote = False
        if self._is_online() and venda_uuid:
            try:
                resp = httpx.put(
                    f"{self.api_base}/vendas/{venda_uuid}",
                    json={"cancelada": True},
                    timeout=10.0
                )
                updated_remote = resp.status_code == 200
                if not updated_remote:
                    print(f"[VENDAS][CANCELAR] Falha HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[VENDAS][CANCELAR] Erro ao cancelar no servidor: {e}")

        # Atualizar localmente sempre
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE vendas
                SET status = 'Anulada',
                    motivo_alteracao = ?,
                    data_alteracao = ?,
                    synced = CASE WHEN ? THEN 1 ELSE COALESCE(synced,0) END
                WHERE id = ?
                """,
                (
                    motivo or 'Venda anulada',
                    datetime.now().isoformat(),
                    1 if updated_remote else 0,
                    venda_id_local,
                )
            )
            conn.commit()

        # Se não atualizou no servidor, logar para sync posterior
        if not updated_remote and venda_uuid:
            self._log_change(venda_uuid, 'UPDATE', {"cancelada": True, "motivo": motivo})

        return True
    
    def _soft_delete_local_venda(self, venda_id: int) -> bool:
        """Soft delete da venda (marca como cancelada)."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vendas 
                SET status = 'cancelada', 
                    motivo_alteracao = 'Venda cancelada',
                    data_alteracao = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), venda_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
    
    def _log_change(self, entity_id: str, operation: str, data: Dict[Any, Any]):
        """Registra mudança no change_log para sincronização posterior."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO change_log (entity_type, entity_id, operation, data_json, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'vendas',
                entity_id,
                operation,
                json.dumps(data),
                datetime.now().isoformat(),
                'pending'
            ))
            conn.commit()
    
    def _ensure_change_log_table(self):
        """Garante que a tabela change_log existe."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    data_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    status TEXT DEFAULT 'pending'
                )
            """)
            conn.commit()
    
    async def sincronizar_mudancas(self) -> Dict[str, Any]:
        """Sincroniza mudanças bidirecionalmente com o servidor."""
        print("=== INICIANDO SINCRONIZACAO BIDIRECIONAL DE VENDAS ===")
        
        # Verificar conectividade
        if not await self.is_backend_online():
            return {
                "status": "offline",
                "message": "Backend offline - operando localmente",
                "enviadas": 0,
                "recebidas": 0,
                "mudancas_pendentes": 0
            }
        
        try:
            # Heurística PUSH-first: se há vendas locais pendentes, empurra primeiro
            pendentes = 0
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT COUNT(*) FROM vendas 
                        WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND TRIM(uuid) <> ''
                          AND status != 'Anulada'
                    """)
                    pendentes = cur.fetchone()[0]
            except Exception:
                pendentes = 0

            if pendentes > 0:
                vendas_antigas_enviadas = await self._sincronizar_vendas_antigas()
                vendas_recebidas = await self._pull_vendas_do_servidor()
            else:
                vendas_recebidas = await self._pull_vendas_do_servidor()
                vendas_antigas_enviadas = await self._sincronizar_vendas_antigas()
            
            # FASE 3: Push - enviar mudanças pendentes
            mudancas = await self._obter_mudancas_pendentes()
            mudancas_enviadas = 0
            
            print("FASE 3: Enviando mudancas pendentes de vendas...")
            print(f"Encontradas {len(mudancas)} mudancas pendentes de vendas")
            
            if len(mudancas) == 0:
                print("Nenhuma sincronizacao necessaria para vendas")
            else:
                async with httpx.AsyncClient() as client:
                    for ch in mudancas:
                        try:
                            op = ch['operation']
                            data = json.loads(ch['data_json']) if ch.get('data_json') else {}
                            # Mapear usuario_id local -> uuid antes de enviar
                            try:
                                local_uid = data.get('usuario_id')
                                mapped_uuid = self._get_user_uuid(local_uid)
                                data['usuario_id'] = mapped_uuid if mapped_uuid else None
                            except Exception:
                                data['usuario_id'] = None
                            entity_uuid = ch['entity_id']
                            if op == 'CREATE':
                                resp = await client.post(f"{self.api_base}/vendas/", json=data, timeout=10.0)
                                print(f"[VENDAS][CREATE] status: {resp.status_code}")
                                if resp.status_code in (200, 201):
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                elif resp.status_code in (400, 409) or (resp.status_code == 500 and 'duplicate' in (resp.text or '').lower()):
                                    # Já existe no servidor
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                else:
                                    print(f"[VENDAS][CREATE] erro: {resp.text}")
                            elif op == 'UPDATE':
                                resp = await client.put(f"{self.api_base}/vendas/{entity_uuid}", json=data, timeout=10.0)
                                print(f"[VENDAS][UPDATE] status: {resp.status_code}")
                                if resp.status_code == 200:
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                elif resp.status_code == 404:
                                    # Se não existe no servidor, tentar criar
                                    post = await client.post(f"{self.api_base}/vendas/", json=data, timeout=10.0)
                                    print(f"[VENDAS][UPDATE->CREATE] status: {post.status_code}")
                                    if post.status_code in (200, 201, 409):
                                        self._mark_change_synced(ch['id'])
                                        mudancas_enviadas += 1
                                else:
                                    print(f"[VENDAS][UPDATE] erro: {resp.text}")
                            elif op == 'DELETE':
                                resp = await client.delete(f"{self.api_base}/vendas/{entity_uuid}", timeout=10.0)
                                print(f"[VENDAS][DELETE] status: {resp.status_code}")
                                if resp.status_code in (200, 204):
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                            else:
                                print(f"[VENDAS] Operacao nao suportada: {op}")
                        except Exception as e:
                            print(f"[VENDAS] Erro ao processar mudança pendente {ch.get('id')}: {e}")
            
            return {
                "status": "success",
                "message": f"Sincronização de vendas concluída. {vendas_antigas_enviadas} vendas antigas enviadas, {mudancas_enviadas} mudanças enviadas.",
                "enviadas": vendas_antigas_enviadas + mudancas_enviadas,
                "recebidas": vendas_recebidas,
                "mudancas_pendentes": len(mudancas),
                "itens_ignorados_por_produto_nao_mapeado": len(getattr(self, "_last_missing_products", set()))
            }
            
        except Exception as e:
            print(f"Erro na sincronização de vendas: {e}")
            return {
                "status": "error",
                "message": f"Erro na sincronização: {str(e)}",
                "enviadas": 0,
                "recebidas": 0,
                "mudancas_pendentes": 0
            }
    
    async def _pull_vendas_do_servidor(self) -> int:
        """Busca vendas do servidor e atualiza localmente."""
        print("FASE 1: Buscando vendas do servidor...")
        recebidas = 0
        self._last_missing_products = set()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.api_base}/vendas/", timeout=10.0)
                if resp.status_code != 200:
                    print(f"[VENDAS][PULL] Erro HTTP {resp.status_code}: {resp.text}")
                    return 0

                vendas_srv = resp.json() or []
                print(f"[VENDAS][PULL] Encontradas {len(vendas_srv)} vendas no servidor")

                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()

                    # Garantir colunas uuid/synced em vendas
                    try:
                        cur.execute("PRAGMA table_info(vendas)")
                        cols = [c[1] for c in cur.fetchall()]
                        if 'uuid' not in cols:
                            cur.execute("ALTER TABLE vendas ADD COLUMN uuid TEXT")
                        if 'synced' not in cols:
                            cur.execute("ALTER TABLE vendas ADD COLUMN synced INTEGER DEFAULT 0")
                        conn.commit()
                    except Exception as mig_e:
                        print(f"[VENDAS][PULL] Aviso ao garantir colunas: {mig_e}")

                    for v in vendas_srv:
                        try:
                            venda_uuid = (v.get('uuid') or v.get('id') or '').strip()
                            if not venda_uuid:
                                print("[VENDAS][PULL] Venda sem UUID/ID - ignorando")
                                continue

                            # Checar se existe localmente por UUID (sem depender de updated_at)
                            cur.execute("SELECT id FROM vendas WHERE uuid = ?", (venda_uuid,))
                            row = cur.fetchone()

                            # Preparar campos principais (com defaults e normalizações)
                            data_venda = v.get('data_venda') or datetime.now().isoformat()
                            total = float(v.get('total') or 0.0)
                            forma_pagamento = v.get('forma_pagamento') or 'Dinheiro'
                            valor_recebido = float(v.get('valor_recebido') or 0.0)
                            troco = float(v.get('troco') or 0.0)
                            status = v.get('status') or 'concluida'
                            motivo_alteracao = v.get('motivo_alteracao') or ''
                            alterado_por = v.get('alterado_por')
                            data_alteracao = v.get('data_alteracao')
                            origem = v.get('origem') or 'servidor'
                            valor_original_divida = float(v.get('valor_original_divida') or 0.0)
                            desconto_aplicado_divida = float(v.get('desconto', v.get('desconto_aplicado_divida') or 0.0))
                            # Tratar usuario_id que pode vir como UUID string do servidor
                            usuario_id_raw = v.get('usuario_id') or 0
                            if isinstance(usuario_id_raw, str) and len(usuario_id_raw) > 10:
                                # É um UUID string, buscar o ID local correspondente
                                usuario_id_local = self._buscar_usuario_por_uuid(usuario_id_raw) or self._get_default_usuario_id()
                            else:
                                # É um ID numérico ou vazio
                                try:
                                    usuario_id_local = int(usuario_id_raw) or self._get_default_usuario_id()
                                except (ValueError, TypeError):
                                    usuario_id_local = self._get_default_usuario_id()

                            if row is None:
                                # Inserir venda nova
                                cur.execute(
                                    """
                                    INSERT INTO vendas (
                                        usuario_id, total, forma_pagamento, valor_recebido, troco,
                                        data_venda, status, motivo_alteracao, alterado_por, data_alteracao,
                                        origem, valor_original_divida, desconto_aplicado_divida, uuid, synced
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                                    """,
                                    (
                                        usuario_id_local, total, forma_pagamento, valor_recebido, troco,
                                        data_venda, status, motivo_alteracao, alterado_por, data_alteracao,
                                        origem, valor_original_divida, desconto_aplicado_divida, venda_uuid
                                    )
                                )
                                venda_id_local = cur.lastrowid
                                conn.commit()
                                recebidas += 1
                            else:
                                # Atualizar venda existente
                                venda_id_local = row['id']
                                cur.execute(
                                    """
                                    UPDATE vendas SET
                                        usuario_id = ?, total = ?, forma_pagamento = ?, valor_recebido = ?, troco = ?,
                                        status = ?, motivo_alteracao = ?, alterado_por = ?, data_alteracao = ?,
                                        origem = ?, valor_original_divida = ?, desconto_aplicado_divida = ?, synced = 1
                                    WHERE id = ?
                                    """,
                                    (
                                        usuario_id_local, total, forma_pagamento, valor_recebido, troco,
                                        status, motivo_alteracao, alterado_por, data_alteracao,
                                        origem, valor_original_divida, desconto_aplicado_divida, venda_id_local
                                    )
                                )
                                conn.commit()

                            # Itens da venda
                            itens = v.get('itens') or []

                            # Limpar itens antigos e re-inserir (idempotente por uuid)
                            try:
                                cur.execute("DELETE FROM itens_venda WHERE venda_id = ?", (venda_id_local,))
                            except Exception as di_e:
                                print(f"[VENDAS][PULL] Aviso ao limpar itens: {di_e}")

                            for it in itens:
                                try:
                                    prod_uuid = str(it.get('produto_id') or '').strip()
                                    if not prod_uuid:
                                        continue
                                    # Mapear produto UUID -> ID local
                                    cur.execute("SELECT id FROM produtos WHERE uuid = ?", (prod_uuid,))
                                    prod_row = cur.fetchone()
                                    if not prod_row:
                                        # Produto não existe localmente; pular item (ou poderia criar placeholder)
                                        print(f"[VENDAS][PULL] Produto {prod_uuid} não encontrado localmente - pulando item")
                                        try:
                                            self._last_missing_products.add(prod_uuid)
                                        except Exception:
                                            pass
                                        continue
                                    produto_id_local = prod_row['id']

                                    quantidade = int(it.get('quantidade') or 0) or 1
                                    preco_unitario = float(it.get('preco_unitario') or 0.0)
                                    subtotal = float(it.get('subtotal') or 0.0)
                                    peso_kg = float(it.get('peso_kg') or 0.0)

                                    cur.execute(
                                        """
                                        INSERT INTO itens_venda (
                                            venda_id, produto_id, quantidade, preco_unitario, preco_custo_unitario, subtotal, peso_kg
                                        ) VALUES (?, ?, ?, ?, COALESCE((SELECT preco_custo FROM produtos WHERE id = ?), 0), ?, ?)
                                        """,
                                        (
                                            venda_id_local, produto_id_local, quantidade, preco_unitario, produto_id_local, subtotal, peso_kg
                                        )
                                    )
                                except Exception as it_e:
                                    print(f"[VENDAS][PULL] Erro ao inserir item da venda {venda_uuid}: {it_e}")

                            conn.commit()
                        except Exception as v_e:
                            print(f"[VENDAS][PULL] Erro ao processar venda {v.get('uuid', 'N/A')}: {v_e}")

                print(f"[VENDAS][PULL] Concluído. Vendas novas/atualizadas: {recebidas}")
                return recebidas

        except Exception as e:
            print(f"[VENDAS][PULL] Erro: {e}")
            return 0
    
    async def _sincronizar_vendas_antigas(self) -> int:
        """Sincroniza vendas antigas não sincronizadas com o servidor."""
        print("FASE 2: Enviando vendas antigas...")
        print("Verificando vendas antigas nao sincronizadas...")
        
        # Verificar se há vendas locais não sincronizadas (incluindo bulk sync)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Primeiro verificar se há vendas nunca sincronizadas (bulk sync)
            cursor.execute("""
                SELECT COUNT(*) FROM vendas v
                WHERE (v.synced = 0 OR v.synced IS NULL) AND v.uuid IS NOT NULL AND v.uuid != ''
                  AND v.status != 'Anulada'
            """)
            vendas_nao_sync_count = cursor.fetchone()[0]
            
            if vendas_nao_sync_count > 0:
                print(f"Verificando vendas antigas nao sincronizadas...")
                cursor.execute("""
                    SELECT v.id, v.data_venda, v.total, v.desconto_aplicado_divida, v.forma_pagamento, 
                           v.status, v.uuid
                    FROM vendas v
                    WHERE (v.synced = 0 OR v.synced IS NULL) AND v.uuid IS NOT NULL AND v.uuid != ''
                      AND v.status != 'Anulada'
                """)
            else:
                # Todas já sincronizadas
                cursor.execute("SELECT 1 WHERE 0")  # Query vazia
            
            vendas_nao_sync = cursor.fetchall()
            
            if not vendas_nao_sync:
                print("Todas as vendas ja estao sincronizadas")
                return 0
            
            print(f"Encontradas {len(vendas_nao_sync)} vendas nao sincronizadas")
            
            enviados = 0
            async with httpx.AsyncClient() as client:
                for venda in vendas_nao_sync:
                    try:
                        # Buscar itens da venda
                        cursor.execute("""
                            SELECT produto_id, quantidade, preco_unitario, subtotal, COALESCE(peso_kg, 0) as peso_kg
                            FROM itens_venda 
                            WHERE venda_id = ?
                        """, (venda[0],))
                        itens = cursor.fetchall()
                        
                        itens_data = []
                        venda_valida = True
                        
                        for item in itens:
                            # Buscar UUID do produto pelo ID
                            cursor.execute("SELECT uuid, codigo FROM produtos WHERE id = ?", (item[0],))
                            produto_result = cursor.fetchone()
                            
                            if produto_result and produto_result[0]:
                                produto_uuid = produto_result[0]
                                produto_codigo = produto_result[1]
                                
                                # Verificar se produto existe no servidor (por UUID ou código)
                                produto_existe = False
                                try:
                                    # Tentar por UUID
                                    produto_response = await client.get(
                                        f"{self.api_base}/produtos/{produto_uuid}",
                                        timeout=5.0
                                    )
                                    if produto_response.status_code == 200:
                                        produto_existe = True
                                    else:
                                        # Buscar lista e conferir por código
                                        produtos_response = await client.get(
                                            f"{self.api_base}/produtos/",
                                            timeout=5.0
                                        )
                                        if produtos_response.status_code == 200:
                                            for p in produtos_response.json():
                                                if p.get('codigo') == produto_codigo:
                                                    produto_existe = True
                                                    produto_uuid = p.get('id', produto_uuid)
                                                    break
                                except Exception as e:
                                    print(f"Erro ao verificar produto no servidor: {e}")

                                if not produto_existe:
                                    print(f"Produto {produto_codigo} (UUID: {produto_uuid}) não existe no servidor - pulando venda")
                                    venda_valida = False
                                    break
                            else:
                                print(f"Produto ID {item[0]} não tem UUID - pulando venda")
                                venda_valida = False
                                break
                            
                            # Backend espera quantidade inteira; se houver fração, envia em peso_kg
                            qtd_raw = float(item[1])
                            qtd_int = int(qtd_raw)
                            peso_kg = float(item[4]) if len(item) > 4 else 0.0  # Usar peso_kg da tabela
                            if abs(qtd_raw - qtd_int) > 1e-6 and peso_kg == 0.0:
                                peso_kg = round(qtd_raw - qtd_int, 3)

                            # Backend exige quantidade > 0
                            if qtd_int <= 0:
                                qtd_int = 1

                            item_payload = {
                                "produto_id": str(produto_uuid),  # Garantir que é string
                                "quantidade": qtd_int,
                                "preco_unitario": float(item[2]),
                                "subtotal": float(item[3])
                            }
                            # Incluir peso_kg para vendas por peso
                            if peso_kg > 0:
                                item_payload["peso_kg"] = peso_kg

                            itens_data.append(item_payload)
                        
                        if not venda_valida:
                            continue
                        
                        # Montar payload compatível com o backend (VendaCreate)
                        # Campos aceitos: uuid?, cliente_id?, total, desconto, forma_pagamento, observacoes?, itens[], usuario_id (UUID)
                        # Mapear usuario_id local -> uuid do servidor
                        try:
                            # venda local tuple indices: (id, data_venda, total, desconto_aplicado_divida, forma_pagamento, status, uuid)
                            cur_uid = conn.cursor()
                            cur_uid.execute("SELECT usuario_id FROM vendas WHERE id = ?", (venda[0],))
                            row_uid = cur_uid.fetchone()
                            local_usuario_id = int(row_uid[0]) if row_uid and row_uid[0] is not None else None
                        except Exception:
                            local_usuario_id = None

                        usuario_uuid = None
                        try:
                            usuario_uuid = self._get_user_uuid(local_usuario_id)
                        except Exception:
                            usuario_uuid = None

                        venda_data = {
                            "uuid": venda[6],
                            "total": float(venda[2]),
                            "desconto": float(venda[3]) if venda[3] else 0.0,
                            "forma_pagamento": venda[4] or "Dinheiro",
                            "itens": itens_data,
                            "usuario_id": usuario_uuid if usuario_uuid else None,
                        }
                        
                        print(f"Enviando venda antiga: {venda[0]} - MT {venda[2]}")
                        try:
                            # Log resumido do payload para diagnóstico
                            resumo_itens = [
                                {
                                    'produto_id': it['produto_id'][:8] + '...' if isinstance(it.get('produto_id'), str) and len(it['produto_id']) > 8 else it.get('produto_id'),
                                    'qtd': it.get('quantidade'),
                                    'peso_kg': it.get('peso_kg', 0),
                                    'subtotal': it.get('subtotal')
                                } for it in itens_data
                            ]
                            print(f"[DEBUG] Payload venda uuid={venda_data.get('uuid')} total={venda_data['total']} itens={len(itens_data)} -> {resumo_itens}")
                        except Exception:
                            pass
                        
                        # Tentar criar primeiro
                        response = await client.post(
                            f"{self.api_base}/vendas/",
                            json=venda_data,
                            timeout=10.0
                        )
                        
                        if response.status_code in [200, 201]:
                            # Marcar como sincronizado
                            cursor.execute("""
                                UPDATE vendas 
                                SET synced = 1
                                WHERE id = ?
                            """, (venda[0],))
                            conn.commit()
                            enviados += 1
                            print(f"Venda {venda[0]} sincronizada")
                            
                        elif response.status_code == 400 and "já existe" in response.text:
                            # Venda já existe, tentar atualizar
                            print(f"Venda {venda[0]} ja existe, tentando atualizar...")
                            
                            response = await client.put(
                                f"{self.api_base}/vendas/{venda[6]}",
                                json=venda_data,
                                timeout=10.0
                            )
                            
                            if response.status_code == 200:
                                cursor.execute("""
                                    UPDATE vendas 
                                    SET synced = 1
                                    WHERE id = ?
                                """, (venda[0],))
                                conn.commit()
                                enviados += 1
                                print(f"Venda {venda[0]} atualizada no servidor")
                            else:
                                print(f"Erro ao atualizar venda: {response.text}")
                        elif response.status_code == 500 and ("duplicate key" in response.text or "UniqueViolationError" in response.text):
                            # Venda já existe (erro de chave duplicada)
                            print(f"Venda {venda[0]} ja existe no servidor (chave duplicada) - marcando como sincronizada")
                            cursor.execute("""
                                UPDATE vendas 
                                SET synced = 1
                                WHERE id = ?
                            """, (venda[0],))
                            conn.commit()
                            enviados += 1
                        else:
                            # Tentar extrair detalhe do erro para diagnóstico
                            detail_msg = None
                            try:
                                j = response.json()
                                detail_msg = j.get('detail') if isinstance(j, dict) else None
                            except Exception:
                                pass
                            print(f"Erro ao enviar venda: {response.status_code} - {response.text}")
                            if detail_msg:
                                print(f"[DETAIL] {detail_msg}")
                            
                    except Exception as e:
                        print(f"Erro ao processar venda {venda[0]}: {e}")
            
            conn.close()
            print(f"Sincronizacao de vendas antigas concluida: {enviados}/{len(vendas_nao_sync)} enviados")
            return enviados
            
        except Exception as e:
            print(f"Erro na sincronizacao de vendas antigas: {e}")
            return 0
            
            async with httpx.AsyncClient() as client:
                for mudanca in mudancas:
                    try:
                        print(f"Processando mudanca {mudanca['operation']} para venda {mudanca['entity_id']}")
                        
                        if mudanca['operation'] == 'CREATE':
                            data = json.loads(mudanca['data_json'])
                            response = await client.post(
                                f"{self.backend_url}/api/vendas/",
                                json=data,
                                timeout=5.0
                            )
                            if response.status_code in [200, 201]:
                                self._mark_change_synced(mudanca['id'])
                                enviadas += 1
                                print("Mudanca CREATE de venda sincronizada")
                            else:
                                print(f"Erro CREATE: {response.text}")
                        
                        elif mudanca['operation'] == 'UPDATE':
                            data = json.loads(mudanca['data_json'])
                            response = await client.put(
                                f"{self.backend_url}/api/vendas/{mudanca['entity_id']}",
                                json=data,
                                timeout=5.0
                            )
                            if response.status_code == 200:
                                self._mark_change_synced(mudanca['id'])
                                enviadas += 1
                                print("Mudanca UPDATE de venda sincronizada")
                            else:
                                print(f"Erro UPDATE: {response.text}")
                        
                        elif mudanca['operation'] == 'DELETE':
                            response = await client.delete(
                                f"{self.backend_url}/api/vendas/{mudanca['entity_id']}",
                                timeout=5.0
                            )
                            if response.status_code == 200:
                                self._mark_change_synced(mudanca['id'])
                                enviadas += 1
                                print("Mudanca DELETE de venda sincronizada")
                            else:
                                print(f"Erro DELETE: {response.text}")
                                
                    except Exception as e:
                        print(f"Erro ao sincronizar mudanca de venda {mudanca['id']}: {e}")
            
            print(f"Sincronizacao de vendas concluida: {enviadas} mudancas enviadas")
            return {
                "status": "success",
                "enviadas": enviadas,
                "recebidas": 0,
                "message": f"Sincronização de vendas concluída. {enviadas} mudanças enviadas."
            }
            
        except Exception as e:
            print(f"Erro geral na sincronizacao de vendas: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _obter_mudancas_pendentes(self) -> List[Dict[str, Any]]:
        """Obtém mudanças pendentes de vendas."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, entity_type, entity_id, operation, data_json, created_at
                FROM change_log 
                WHERE entity_type = 'vendas' AND status = 'pending'
                ORDER BY created_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def _mark_change_synced(self, change_id: int):
        """Marca mudança como sincronizada."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE change_log 
                SET status = 'synced', updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), change_id))
            conn.commit()
    
    def get_vendas_periodo(self, data_inicio: str, data_fim: str) -> List[Dict[str, Any]]:
        """Obtém vendas por período."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM vendas 
                WHERE DATE(data_venda) BETWEEN ? AND ?
                AND status != 'cancelada'
                ORDER BY data_venda DESC
            """, (data_inicio, data_fim))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_vendas_hoje(self) -> float:
        """Obtém total de vendas do dia atual."""
        hoje = datetime.now().strftime('%Y-%m-%d')
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) as total
                FROM vendas 
                WHERE DATE(data_venda) = ? AND status != 'cancelada'
            """, (hoje,))
            result = cursor.fetchone()
            return result[0] if result else 0.0
    
    def get_vendas_com_detalhes(self, data_inicio: str, data_fim: str, usuario_id: int = None, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtém vendas com detalhes, priorizando dados do servidor se online."""
        print(f"🔍 Buscando vendas de {data_inicio} a {data_fim}, usuário: {usuario_id}")
        
        # Tentar buscar do servidor primeiro se online
        if self._is_online():
            try:
                print("🌐 Sistema online - usando endpoint específico de período...")
                vendas_servidor = self._get_vendas_periodo_servidor(data_inicio, data_fim, usuario_id, limit, offset)
                if vendas_servidor:
                    # Normalizar dados do servidor
                    vendas_normalizadas = []
                    for venda in vendas_servidor:
                        venda_normalizada = self._normalizar_venda_servidor(venda)
                        vendas_normalizadas.append(venda_normalizada)
                        print(f"✅ Venda {venda.get('id', 'N/A')[:8]} normalizada")
                    
                    print(f"🌐 Retornando {len(vendas_normalizadas)} vendas do servidor")
                    return vendas_normalizadas
                else:
                    print("📭 Endpoint específico não retornou vendas - usando dados locais")
            except Exception as e:
                print(f"❌ Erro ao buscar vendas do servidor: {e}")
        else:
            print("📱 Sistema offline - usando dados locais")
        
        # Fallback para dados locais
        vendas_locais = self._get_vendas_locais_com_detalhes(data_inicio, data_fim, usuario_id, limit, offset)
        print(f"💾 Retornando {len(vendas_locais)} vendas locais")
        return vendas_locais
    
    def _get_vendas_periodo_servidor(self, data_inicio: str, data_fim: str, usuario_id: int = None, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Busca vendas do servidor por período usando endpoint específico."""
        try:
            params = {
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'offset': offset
            }
            if usuario_id is not None:
                params['usuario_id'] = usuario_id
            if limit is not None:
                params['limit'] = limit
                
            url = f"{self.api_base}/vendas/periodo"
            print(f"📡 Buscando vendas por período: {url} - {params}")
            response = httpx.get(url, params=params, timeout=10.0)
            if response.status_code == 200:
                vendas = response.json()
                print(f"✅ {len(vendas)} vendas do período recebidas do servidor")
                return vendas
            else:
                print(f"❌ Erro HTTP {response.status_code} ao buscar vendas por período")
                return []
        except Exception as e:
            print(f"❌ Erro ao buscar vendas por período do servidor: {e}")
        return []
    
    def _get_vendas_usuario_servidor(self, usuario_id: int, data_inicio: str = None, data_fim: str = None, status_filter: str = None) -> List[Dict[str, Any]]:
        """Busca vendas de um usuário do servidor usando endpoint específico."""
        try:
            params = {}
            if data_inicio:
                params['data_inicio'] = data_inicio
            if data_fim:
                params['data_fim'] = data_fim
            if status_filter:
                params['status_filter'] = status_filter
                
            url = f"{self.backend_url}/api/vendas/usuario/{usuario_id}"
            print(f"📡 Buscando vendas do usuário {usuario_id}: {url} - {params}")
            response = httpx.get(url, params=params, timeout=10.0)
            if response.status_code == 200:
                vendas = response.json()
                print(f"✅ {len(vendas)} vendas do usuário {usuario_id} recebidas do servidor")
                return vendas
            else:
                print(f"❌ Erro HTTP {response.status_code} ao buscar vendas do usuário")
                return []
        except Exception as e:
            print(f"❌ Erro ao buscar vendas do usuário do servidor: {e}")
        return []
    
    def _get_vendas_locais_com_detalhes(self, data_inicio: str, data_fim: str, usuario_id: int = None, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtém vendas locais com detalhes incluindo informações do usuário."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar se a coluna status existe
            cursor.execute("PRAGMA table_info(vendas)")
            colunas = cursor.fetchall()
            tem_status = any(col[1] == 'status' for col in colunas)
            
            # Construir query base
            if tem_status:
                status_sql = "COALESCE(v.status, 'Ativa') as status"
            else:
                status_sql = "'Ativa' as status"
            
            # Query base - incluir campos data e hora separados para compatibilidade
            query = f"""
                SELECT 
                    v.id,
                    strftime('%Y-%m-%d %H:%M:%S', v.data_venda) as data_venda,
                    DATE(v.data_venda) as data,
                    TIME(v.data_venda) as hora,
                    u.nome as vendedor,
                    v.total,
                    v.forma_pagamento,
                    v.usuario_id,
                    {status_sql},
                    'Sem itens' as itens
                FROM vendas v
                LEFT JOIN usuarios u ON v.usuario_id = u.id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
            """
            
            params = [data_inicio, data_fim]
            
            # Filtrar por usuário se especificado
            if usuario_id is not None:
                query += " AND v.usuario_id = ?"
                params.append(usuario_id)
            
            query += " ORDER BY v.data_venda DESC"
            
            # Aplicar paginação se especificada
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def _normalizar_venda_servidor(self, venda: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza dados de venda do servidor para compatibilidade com views locais.
        - Prefere usuario_nome retornado pelo backend.
        - Converte data/hora do servidor (UTC/offset) para horário local.
        """
        data_venda_raw = venda.get('data_venda', '') or venda.get('created_at', '')

        # Converter para horário local se vier com timezone/UTC
        data_parte = ''
        hora_parte = ''
        try:
            from datetime import datetime, timezone
            dt = None
            # Normalizar sufixo Z
            dv = data_venda_raw.replace('Z', '+00:00') if isinstance(data_venda_raw, str) else ''
            try:
                dt = datetime.fromisoformat(dv)
            except Exception:
                dt = None
            if dt is not None:
                # Converter para timezone local
                local_dt = dt.astimezone()
                data_parte = local_dt.strftime('%Y-%m-%d')
                hora_parte = local_dt.strftime('%H:%M:%S')
            else:
                # Fallback simples
                if 'T' in data_venda_raw:
                    data_parte, hora_parte = data_venda_raw.split('T')
                    hora_parte = hora_parte.split('.')[0]
                elif ' ' in data_venda_raw:
                    data_parte, hora_parte = data_venda_raw.split(' ', 1)
                else:
                    data_parte = data_venda_raw
                    hora_parte = '00:00:00'
        except Exception:
            if isinstance(data_venda_raw, str):
                if 'T' in data_venda_raw:
                    data_parte, hora_parte = data_venda_raw.split('T')
                    hora_parte = hora_parte.split('.')[0]
                elif ' ' in data_venda_raw:
                    data_parte, hora_parte = data_venda_raw.split(' ', 1)
                else:
                    data_parte = data_venda_raw
                    hora_parte = '00:00:00'
            else:
                data_parte = ''
                hora_parte = ''

        # Determinar vendedor
        vendedor = venda.get('usuario_nome') or 'Sistema'
        usuario_id = venda.get('usuario_id')
        if not vendedor and usuario_id:
            # Buscar nome local pelo uuid como fallback
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT nome FROM usuarios WHERE uuid = ?", (str(usuario_id),))
                    user_row = cursor.fetchone()
                    if user_row:
                        vendedor = user_row['nome']
                    else:
                        vendedor = f'Usuário {str(usuario_id)[:8]}'
            except Exception as e:
                print(f"❌ Erro ao buscar usuário {usuario_id}: {e}")
                vendedor = f'Usuário {str(usuario_id)[:8]}'

        return {
            'id': venda.get('id') or venda.get('uuid'),
            'data_venda': data_venda_raw,
            'data': data_parte,
            'hora': hora_parte,
            'vendedor': vendedor or 'Sistema',
            'total': float(venda.get('total', 0.0) or 0.0),
            'forma_pagamento': venda.get('forma_pagamento', 'Não informado'),
            'status': venda.get('status', 'Ativa'),
            'usuario_id': usuario_id,
            'itens': venda.get('itens', 'Sem itens')
        }
    
    def count_vendas_periodo(self, data_inicio: str, data_fim: str, usuario_id: int = None) -> int:
        """Conta total de vendas no período."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(*) as total
                FROM vendas v
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
            """
            params = [data_inicio, data_fim]
            
            if usuario_id is not None:
                query += " AND v.usuario_id = ?"
                params.append(usuario_id)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def get_vendas_usuario_com_itens(self, usuario_id: int, data_inicio: str, data_fim: str, status_filter: str = None) -> List[Dict[str, Any]]:
        """Obtém vendas de um usuário específico com itens, priorizando dados do servidor se online."""
        print(f"🔍 Buscando vendas do usuário {usuario_id} de {data_inicio} a {data_fim}")
        
        # Tentar buscar do servidor primeiro se online
        if self._is_online():
            try:
                print("🌐 Sistema online - usando endpoint específico de usuário...")
                vendas_servidor = self._get_vendas_usuario_servidor(usuario_id, data_inicio, data_fim, status_filter)
                if vendas_servidor:
                    # Normalizar dados do servidor
                    vendas_normalizadas = []
                    for venda in vendas_servidor:
                        venda_normalizada = self._normalizar_venda_servidor(venda)
                        vendas_normalizadas.append(venda_normalizada)
                        print(f"✅ Venda {venda.get('id', 'N/A')[:8]} do usuário {usuario_id} normalizada")
                    
                    print(f"🌐 Retornando {len(vendas_normalizadas)} vendas do usuário {usuario_id} do servidor")
                    return vendas_normalizadas
                else:
                    print("📭 Endpoint específico não retornou vendas - usando dados locais")
            except Exception as e:
                print(f"❌ Erro ao buscar vendas do usuário do servidor: {e}")
        else:
            print("📱 Sistema offline - usando dados locais")
        
        # Fallback para dados locais
        vendas_locais = self._get_vendas_usuario_locais_com_itens(usuario_id, data_inicio, data_fim, status_filter)
        print(f"💾 Retornando {len(vendas_locais)} vendas locais do usuário {usuario_id}")
        return vendas_locais
    
    def _match_status_filter(self, status: str, status_filter: str) -> bool:
        """Verifica se o status da venda corresponde ao filtro."""
        if status_filter == "Não Fechadas":
            return status != 'Fechada'
        elif status_filter == "Fechadas":
            return status == 'Fechada'
        return True
    
    def _get_vendas_usuario_locais_com_itens(self, usuario_id: int, data_inicio: str, data_fim: str, status_filter: str = None) -> List[Dict[str, Any]]:
        """Obtém vendas locais de um usuário com itens."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query para buscar vendas com itens
            query = """
                SELECT 
                    v.id,
                    DATE(v.data_venda) as data,
                    TIME(v.data_venda) as hora,
                    v.total,
                    v.forma_pagamento,
                    COALESCE(v.status, 'Ativa') as status,
                    GROUP_CONCAT(
                        p.nome || ' (' || iv.quantidade || 'x - MT ' || 
                        printf('%.2f', iv.preco_unitario) || ')'
                    ) as itens
                FROM vendas v
                JOIN itens_venda iv ON iv.venda_id = v.id
                JOIN produtos p ON p.id = iv.produto_id
                WHERE v.usuario_id = ?
                AND DATE(v.data_venda) BETWEEN ? AND ?
                AND (v.status IS NULL OR v.status != 'Anulada')
            """
            
            params = [usuario_id, data_inicio, data_fim]
            
            # Aplicar filtro de status
            if status_filter == "Não Fechadas":
                query += " AND (v.status IS NULL OR v.status != 'Fechada')"
            elif status_filter == "Fechadas":
                query += " AND v.status = 'Fechada'"
            
            query += " GROUP BY v.id ORDER BY v.data_venda DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
