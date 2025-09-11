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
            
            print(f"FASE 3: Enviando mudancas pendentes de vendas...")
            print(f"Encontradas {len(mudancas)} mudancas pendentes de vendas")
            
            if len(mudancas) == 0:
                print("Nenhuma sincronizacao necessaria para vendas")
            else:
                async with httpx.AsyncClient() as client:
                    for ch in mudancas:
                        try:
                            op = ch['operation']
                            data = json.loads(ch['data_json']) if ch.get('data_json') else {}
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
                "mudancas_pendentes": len(mudancas)
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
        # TODO: Implementar pull de vendas do servidor se necessário
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
                        
                        venda_data = {
                            "uuid": venda[6],
                            "data_venda": venda[1],
                            "total": float(venda[2]),
                            "desconto": float(venda[3]) if venda[3] else 0.0,
                            "forma_pagamento": venda[4] or "Dinheiro",
                            "status": venda[5],
                            "itens": itens_data
                        }
                        
                        print(f"Enviando venda antiga: {venda[0]} - MT {venda[2]}")
                        
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
                            print(f"Erro ao enviar venda: {response.status_code} - {response.text}")
                            
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
                
            url = f"{self.backend_url}/api/vendas/periodo"
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
                JOIN usuarios u ON v.usuario_id = u.id
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
        """Normaliza dados de venda do servidor para compatibilidade com views locais."""
        data_venda = venda.get('data_venda', '') or venda.get('created_at', '')
        
        # Extrair data e hora
        if 'T' in data_venda:
            data_parte, hora_parte = data_venda.split('T')
            hora_parte = hora_parte.split('.')[0]  # Remove microsegundos se existirem
        elif ' ' in data_venda:
            data_parte, hora_parte = data_venda.split(' ', 1)
        else:
            data_parte = data_venda
            hora_parte = "00:00:00"
        
        # Para vendas do servidor sem usuario_id, usar valor padrão
        usuario_id = venda.get('usuario_id')
        if usuario_id is None:
            # Usar ID 1 como padrão para vendas sem usuário específico
            usuario_id = 1
            vendedor = 'Sistema'
        else:
            vendedor = venda.get('vendedor', f'Usuário {usuario_id}')
        
        return {
            'id': venda.get('id'),
            'data_venda': data_venda,
            'data': data_parte,
            'hora': hora_parte,
            'vendedor': vendedor,
            'total': venda.get('total', 0.0),
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
