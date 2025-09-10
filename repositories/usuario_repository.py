import sqlite3
import httpx
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import os
import json
import platform
from utils.migration_helper import MigrationHelper
from werkzeug.security import generate_password_hash

class UsuarioRepository:
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
        # Usar o mesmo caminho central do app (evita mismatch de DB)
        try:
            from database.database import Database
            db = Database()
            return Path(db.db_path)
        except Exception:
            # Fallback antigo
            return Path(__file__).parent.parent / 'database' / 'sistema.db'
    
    def _is_online(self) -> bool:
        """Verifica se o backend está online (versão síncrona)."""
        try:
            response = httpx.get(f"{self.backend_url}/healthz", timeout=3.0)
            return response.status_code == 200
        except:
            return False
    
    async def is_backend_online(self) -> bool:
        """Versão assíncrona para verificar se o backend está online."""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
                    url1 = f"{self.backend_url}/healthz"
                    try:
                        resp1 = await client.get(url1)
                        if resp1.status_code == 200:
                            return True
                    except Exception:
                        pass

                    # Fallback sem /api quando aplicável
                    if self.backend_url.endswith('/api'):
                        base_url = self.backend_url[:-4]
                        url2 = f"{base_url}/healthz"
                        try:
                            resp2 = await client.get(url2)
                            if resp2.status_code == 200:
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
        """Garante que as colunas de sincronização existam na tabela usuarios."""
        try:
            migration_helper = MigrationHelper()
            if migration_helper.check_migration_needed():
                print("[USUARIO_REPO] Executando migração automática...")
                migration_helper.migrate_usuarios_table()
        except Exception as e:
            print(f"[USUARIO_REPO] Erro durante migração: {e}")
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Obtém todos os usuários (híbrido: servidor primeiro, fallback local)."""
        if self._is_online():
            try:
                response = httpx.get(f"{self.api_base}/usuarios/", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Erro ao buscar usuarios do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_all_local()
    
    def _get_all_local(self) -> List[Dict[str, Any]]:
        """Obtém todos os usuários do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar se as colunas uuid e synced existem
            cursor.execute("PRAGMA table_info(usuarios)")
            columns = [col[1] for col in cursor.fetchall()]
            has_uuid = 'uuid' in columns
            has_synced = 'synced' in columns
            
            if has_uuid and has_synced:
                cursor.execute("""
                    SELECT id, nome, usuario, senha, nivel, is_admin, ativo, salario,
                           created_at, updated_at, 
                           COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                    FROM usuarios 
                    WHERE ativo = 1
                    ORDER BY nome
                """)
            else:
                cursor.execute("""
                    SELECT id, nome, usuario, senha, nivel, is_admin, ativo, salario,
                           created_at, updated_at
                    FROM usuarios 
                    WHERE ativo = 1
                    ORDER BY nome
                """)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if not has_uuid:
                    result['uuid'] = ''
                if not has_synced:
                    result['synced'] = 0
                results.append(result)
            
            return results
    
    def get_by_id(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """Obtém usuário por ID (híbrido)."""
        if self._is_online():
            try:
                # Buscar UUID do usuário local
                usuario_local = self._get_local_usuario_by_id(usuario_id)
                if usuario_local and usuario_local.get('uuid'):
                    response = httpx.get(
                        f"{self.api_base}/usuarios/{usuario_local['uuid']}", 
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        return response.json()
            except Exception as e:
                print(f"Erro ao buscar usuario do servidor: {e}")
        
        # Fallback para dados locais
        return self._get_local_usuario_by_id(usuario_id)
    
    def _get_local_usuario_by_id(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar se a coluna uuid existe
            cursor.execute("PRAGMA table_info(usuarios)")
            columns = [col[1] for col in cursor.fetchall()]
            has_uuid = 'uuid' in columns
            has_synced = 'synced' in columns
            
            if has_uuid and has_synced:
                cursor.execute("""
                    SELECT id, nome, usuario, senha, nivel, is_admin, ativo, salario,
                           created_at, updated_at, 
                           COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                    FROM usuarios 
                    WHERE id = ? AND ativo = 1
                """, (usuario_id,))
            else:
                cursor.execute("""
                    SELECT id, nome, usuario, senha, nivel, is_admin, ativo, salario,
                           created_at, updated_at
                    FROM usuarios 
                    WHERE id = ? AND ativo = 1
                """, (usuario_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if not has_uuid:
                    result['uuid'] = ''
                if not has_synced:
                    result['synced'] = 0
                return result
            return None
    
    def get_by_uuid(self, usuario_uuid: str) -> Optional[Dict[str, Any]]:
        """Obtém usuário por UUID do banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar se a coluna uuid existe
            cursor.execute("PRAGMA table_info(usuarios)")
            columns = [col[1] for col in cursor.fetchall()]
            has_uuid = 'uuid' in columns
            has_synced = 'synced' in columns
            
            if has_uuid:
                if has_synced:
                    cursor.execute("""
                        SELECT id, nome, usuario, senha, nivel, is_admin, ativo, salario,
                               created_at, updated_at, 
                               COALESCE(uuid, '') as uuid, COALESCE(synced, 0) as synced
                        FROM usuarios 
                        WHERE uuid = ? AND ativo = 1
                    """, (usuario_uuid,))
                else:
                    cursor.execute("""
                        SELECT id, nome, usuario, senha, nivel, is_admin, ativo, salario,
                               created_at, updated_at, uuid
                        FROM usuarios 
                        WHERE uuid = ? AND ativo = 1
                    """, (usuario_uuid,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    if not has_synced:
                        result['synced'] = 0
                    return result
            
            return None
    
    def create(self, usuario_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cria novo usuário (híbrido)."""
        # Gerar UUID se não existir
        if 'uuid' not in usuario_data or not usuario_data['uuid']:
            usuario_data['uuid'] = str(uuid.uuid4())
        
        # Tentar criar no servidor primeiro
        if self._is_online():
            try:
                response = httpx.post(
                    f"{self.api_base}/usuarios/",
                    json=usuario_data,
                    timeout=5.0
                )
                if response.status_code in [200, 201]:
                    usuario_data['synced'] = 1
                    server_usuario = response.json()
                    usuario_data.update(server_usuario)
                    print("Usuario criado no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao criar usuario no servidor: {e}")
        else:
            print("Backend offline, usuario sera criado apenas localmente")
        
        # Sempre criar localmente
        usuario_criado = self._create_local_usuario(usuario_data)
        
        # Log para sincronização se não foi sincronizado
        if usuario_data.get('synced', 0) == 0:
            self._log_change(usuario_data['uuid'], 'CREATE', usuario_data)
        
        return usuario_criado
    
    def _create_local_usuario(self, usuario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria usuário no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            # Normalizar senha: se vier em texto puro, transformar em hash; se vazia, manter vazio
            raw = usuario_data.get('senha', '')
            senha_to_store = raw
            try:
                if raw and not (str(raw).startswith('pbkdf2:') or str(raw).startswith('$2a$') or str(raw).startswith('$2b$') or str(raw).startswith('$2y$')):
                    senha_to_store = generate_password_hash(str(raw))
            except Exception:
                # Em último caso, armazena como veio
                senha_to_store = raw
            cursor.execute("""
                INSERT INTO usuarios (nome, usuario, senha, nivel, is_admin, ativo, salario,
                                    created_at, updated_at, uuid, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario_data['nome'],
                usuario_data['usuario'],
                senha_to_store,
                usuario_data.get('nivel', 1),
                usuario_data.get('is_admin', 0),
                usuario_data.get('ativo', 1),
                usuario_data.get('salario', 0.0),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                usuario_data['uuid'],
                usuario_data.get('synced', 0)
            ))
            
            usuario_id = cursor.lastrowid
            conn.commit()
            
            # Retornar usuário criado
            return self._get_local_usuario_by_id(usuario_id)
    
    async def _obter_mudancas_pendentes(self) -> List[Dict[str, Any]]:
        """Obtém mudanças pendentes de usuários."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, entity_type, entity_id, operation, data_json, created_at
                    FROM change_log 
                    WHERE entity_type = 'usuarios' AND status = 'pending'
                    ORDER BY datetime(created_at) ASC
                    """
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[USUARIOS] Erro ao obter mudancas pendentes: {e}")
            return []
    
    def update(self, usuario_id: int, usuario_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza usuário (híbrido)."""
        # Obter UUID do usuário local
        usuario_local = self._get_local_usuario_by_id(usuario_id)
        if not usuario_local:
            return None
        
        usuario_uuid = usuario_local['uuid']
        
        # Tentar atualizar no servidor
        if self._is_online():
            try:
                response = httpx.put(
                    f"{self.api_base}/usuarios/{usuario_uuid}",
                    json=usuario_data,
                    timeout=5.0
                )
                if response.status_code == 200:
                    usuario_data['synced'] = 1
                    server_usuario = response.json()
                    usuario_data.update(server_usuario)
                    print("Usuario atualizado no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao atualizar usuario no servidor: {e}")
        else:
            print("Backend offline, usuario sera atualizado apenas localmente")
        
        # Sempre atualizar localmente
        usuario_atualizado = self._update_local_usuario(usuario_id, usuario_data)
        
        # Log para sincronização se não foi sincronizado
        if usuario_data.get('synced', 0) == 0:
            self._log_change(usuario_uuid, 'UPDATE', usuario_data)
        
        return usuario_atualizado
    
    def _update_local_usuario(self, usuario_id: int, usuario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza usuário no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            # Buscar hash atual para preservar se senha não for enviada
            try:
                cursor.execute("SELECT senha FROM usuarios WHERE id = ?", (usuario_id,))
                row = cursor.fetchone()
                current_hash = row[0] if row else ''
            except Exception:
                current_hash = ''

            # Normalizar senha: se vier em texto puro, gerar hash; se não vier, manter a atual
            raw = usuario_data.get('senha', None)
            if raw is None or raw == '':
                senha_to_store = current_hash
            else:
                s = str(raw)
                if s.startswith('pbkdf2:') or s.startswith('$2a$') or s.startswith('$2b$') or s.startswith('$2y$'):
                    senha_to_store = s
                else:
                    try:
                        senha_to_store = generate_password_hash(s)
                    except Exception:
                        senha_to_store = s
            cursor.execute("""
                UPDATE usuarios 
                SET nome = ?, usuario = ?, senha = ?, nivel = ?, is_admin = ?, salario = ?,
                    updated_at = ?, synced = ?
                WHERE id = ?
            """, (
                usuario_data['nome'],
                usuario_data['usuario'],
                senha_to_store,
                usuario_data.get('nivel', 1),
                usuario_data.get('is_admin', 0),
                usuario_data.get('salario', 0.0),
                datetime.now().isoformat(),
                usuario_data.get('synced', 0),
                usuario_id
            ))
            conn.commit()
            
            # Retornar usuário atualizado
            return self._get_local_usuario_by_id(usuario_id)
    
    def delete(self, usuario_id: int) -> bool:
        """Deleta usuário (soft delete híbrido)."""
        usuario_local = self._get_local_usuario_by_id(usuario_id)
        if not usuario_local:
            return False
        
        usuario_uuid = usuario_local['uuid']
        
        # Tentar deletar no servidor
        if self._is_online():
            try:
                response = httpx.delete(
                    f"{self.api_base}/usuarios/{usuario_uuid}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    print("Usuario deletado no servidor com sucesso")
                else:
                    print(f"Erro HTTP {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Erro ao deletar usuario no servidor: {e}")
        
        # Sempre fazer soft delete localmente
        success = self._soft_delete_local_usuario(usuario_id)
        
        # Log para sincronização
        if success:
            self._log_change(usuario_uuid, 'DELETE', {})
        
        return success
    
    def _soft_delete_local_usuario(self, usuario_id: int) -> bool:
        """Faz soft delete do usuário no banco local."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios 
                SET ativo = 0, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), usuario_id))
            
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
                'usuarios',
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
        print("=== INICIANDO SINCRONIZACAO BIDIRECIONAL DE USUARIOS ===")
        
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
            # Heurística de primeira sincronização: se houver usuários locais pendentes, priorizar PUSH primeiro
            usuarios_recebidos = 0
            usuarios_antigos_enviados = 0
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT COUNT(*) FROM usuarios 
                        WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND TRIM(uuid) <> '' AND ativo = 1
                    """)
                    pendentes = cur.fetchone()[0]
            except Exception:
                pendentes = 0

            if pendentes > 0:
                # PUSH primeiro
                usuarios_antigos_enviados = await self._sincronizar_usuarios_antigos()
                # Depois PULL para convergir
                usuarios_recebidos = await self._pull_usuarios_do_servidor()
            else:
                # Ordem normal
                usuarios_recebidos = await self._pull_usuarios_do_servidor()
                usuarios_antigos_enviados = await self._sincronizar_usuarios_antigos()
            
            # FASE 3: Push - enviar mudanças pendentes
            mudancas = await self._obter_mudancas_pendentes()
            mudancas_enviadas = 0

            print(f"FASE 3: Enviando mudancas pendentes de usuarios...")
            print(f"Encontradas {len(mudancas)} mudancas pendentes de usuarios")

            if len(mudancas) == 0:
                print("Nenhuma sincronizacao necessaria para usuarios")
            else:
                async with httpx.AsyncClient() as client:
                    for ch in mudancas:
                        try:
                            op = ch['operation']
                            data = json.loads(ch['data_json']) if ch.get('data_json') else {}
                            entity_uuid = ch['entity_id']
                            if op == 'CREATE':
                                resp = await client.post(f"{self.api_base}/usuarios/", json=data, timeout=8.0)
                                print(f"[USUARIOS][CREATE] status: {resp.status_code}")
                                if resp.status_code in (200, 201):
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                elif resp.status_code == 409 or (resp.status_code == 500 and 'duplicate key value' in (resp.text or '').lower()):
                                    # Já existe no servidor: marcar como sincronizada
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                    # Marcar local como sincronizado
                                    try:
                                        local = self.get_by_uuid(entity_uuid)
                                        if local and 'id' in local:
                                            with sqlite3.connect(str(self.db_path)) as conn:
                                                cur2 = conn.cursor()
                                                cur2.execute("UPDATE usuarios SET synced = 1, updated_at = ? WHERE id = ?", (datetime.now().isoformat(), local['id']))
                                                conn.commit()
                                    except Exception as mi:
                                        print(f"[WARN] Falha ao marcar usuario local como sincronizado: {mi}")
                                else:
                                    print(f"[USUARIOS][CREATE] erro: {resp.text}")
                            elif op == 'UPDATE':
                                resp = await client.put(f"{self.api_base}/usuarios/{entity_uuid}", json=data, timeout=8.0)
                                print(f"[USUARIOS][UPDATE] status: {resp.status_code}")
                                if resp.status_code == 200:
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                                elif resp.status_code == 404:
                                    # Tentar CREATE se não existir no servidor
                                    post = await client.post(f"{self.api_base}/usuarios/", json=data, timeout=8.0)
                                    print(f"[USUARIOS][UPDATE->CREATE] status: {post.status_code}")
                                    if post.status_code in (200, 201):
                                        self._mark_change_synced(ch['id'])
                                        mudancas_enviadas += 1
                                elif resp.status_code == 500 and 'keywords must be strings' in (resp.text or '').lower():
                                    # Reenviar com payload mínimo válido
                                    min_payload = {
                                        'nome': data.get('nome'),
                                        'usuario': data.get('usuario'),
                                        'is_admin': bool(data.get('is_admin', False)),
                                        'ativo': bool(data.get('ativo', True)),
                                    }
                                    if 'senha' in data and data.get('senha'):
                                        min_payload['senha'] = data['senha']
                                    retry = await client.put(f"{self.api_base}/usuarios/{entity_uuid}", json=min_payload, timeout=8.0)
                                    print(f"[USUARIOS][UPDATE][RETRY-MIN] status: {retry.status_code}")
                                    if retry.status_code == 200:
                                        self._mark_change_synced(ch['id'])
                                        mudancas_enviadas += 1
                                else:
                                    print(f"[USUARIOS][UPDATE] erro: {resp.text}")
                            elif op == 'DELETE':
                                resp = await client.delete(f"{self.api_base}/usuarios/{entity_uuid}", timeout=8.0)
                                print(f"[USUARIOS][DELETE] status: {resp.status_code}")
                                if resp.status_code in (200, 204):
                                    self._mark_change_synced(ch['id'])
                                    mudancas_enviadas += 1
                            else:
                                print(f"[USUARIOS] Operacao nao suportada: {op}")
                        except Exception as e:
                            print(f"[USUARIOS] Erro ao processar mudança pendente {ch.get('id')}: {e}")
            
            return {
                "status": "success",
                "message": f"Sincronização de usuários concluída. {usuarios_antigos_enviados} usuários antigos enviados, {mudancas_enviadas} mudanças enviadas.",
                "enviadas": usuarios_antigos_enviados + mudancas_enviadas,
                "recebidas": usuarios_recebidos,
                "mudancas_pendentes": len(mudancas)
            }
            
        except Exception as e:
            print(f"Erro na sincronização de usuários: {e}")
            return {
                "status": "error",
                "message": f"Erro na sincronização: {str(e)}",
                "enviadas": 0,
                "recebidas": 0,
                "mudancas_pendentes": 0
            }
    
    async def _pull_usuarios_do_servidor(self) -> int:
        """Busca usuários novos/atualizados do servidor e os integra localmente."""
        try:
            async with httpx.AsyncClient() as client:
                # Buscar todos os usuários do servidor
                response = await client.get(
                    f"{self.api_base}/usuarios/",
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    print(f"Erro ao buscar usuarios do servidor: {response.status_code}")
                    return 0
                
                usuarios_servidor = response.json()
                print(f"Encontrados {len(usuarios_servidor)} usuarios no servidor")
                
                usuarios_recebidos = 0
                usuarios_atualizados = 0
                
                for usuario_servidor in usuarios_servidor:
                    try:
                        # Se usuário não tem UUID, pular
                        if 'uuid' not in usuario_servidor or not usuario_servidor['uuid']:
                            print(f"Usuario {usuario_servidor['nome']} sem UUID - pulando")
                            continue
                            
                        # Verificar se usuário já existe localmente pelo UUID
                        usuario_local = self.get_by_uuid(usuario_servidor['uuid'])
                        
                        if usuario_local is None:
                            # Usuário novo - inserir localmente
                            if self._inserir_usuario_do_servidor(usuario_servidor):
                                usuarios_recebidos += 1
                                print(f"Usuario novo inserido: {usuario_servidor['nome']}")
                        else:
                            # Usuário existe - verificar se precisa atualizar
                            if self._usuario_servidor_mais_recente(usuario_local, usuario_servidor):
                                if self._atualizar_usuario_do_servidor(usuario_local['id'], usuario_servidor):
                                    usuarios_atualizados += 1
                                    print(f"Usuario atualizado: {usuario_servidor['nome']}")
                    
                    except Exception as e:
                        print(f"Erro ao processar usuario {usuario_servidor.get('nome', 'N/A')}: {e}")
                
                total_recebidos = usuarios_recebidos + usuarios_atualizados
                print(f"Pull de usuarios concluído: {usuarios_recebidos} novos, {usuarios_atualizados} atualizados")
                return total_recebidos
        except Exception as e:
            print(f"Erro geral na sincronizacao de usuarios: {e}")
            return 0
    
    def _inserir_usuario_do_servidor(self, usuario_servidor: Dict[str, Any]) -> bool:
        """Insere usuário do servidor no banco local."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Verificar se as colunas uuid e synced existem
                cursor.execute("PRAGMA table_info(usuarios)")
                columns = [col[1] for col in cursor.fetchall()]
                has_uuid = 'uuid' in columns
                has_synced = 'synced' in columns
                
                # Determinar senha: usar a enviada pelo servidor, se houver; caso contrário
                # tentar reutilizar uma senha local de um usuário com mesmo 'usuario'
                senha_inserir = usuario_servidor.get('senha')
                if not senha_inserir:
                    try:
                        cursor.execute("SELECT senha FROM usuarios WHERE LOWER(usuario) = LOWER(?) LIMIT 1", (usuario_servidor['usuario'],))
                        row = cursor.fetchone()
                        if row and row[0]:
                            senha_inserir = row[0]
                    except Exception:
                        pass
                if not senha_inserir:
                    # Definir uma senha inicial padrão para permitir primeiro login local
                    try:
                        senha_inserir = generate_password_hash('842384')
                    except Exception:
                        senha_inserir = ''

                if has_uuid and has_synced:
                    cursor.execute("""
                        INSERT INTO usuarios (nome, usuario, senha, nivel, is_admin, ativo, salario,
                                              created_at, updated_at, uuid, synced)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        usuario_servidor['nome'],
                        usuario_servidor['usuario'],
                        senha_inserir,
                        usuario_servidor.get('nivel', 1),
                        usuario_servidor.get('is_admin', 0),
                        usuario_servidor.get('ativo', 1),
                        usuario_servidor.get('salario', 0.0),
                        usuario_servidor.get('created_at', datetime.now().isoformat()),
                        usuario_servidor.get('updated_at', datetime.now().isoformat()),
                        usuario_servidor['uuid'],
                        1  # synced = 1 (já sincronizado)
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO usuarios (nome, usuario, senha, nivel, is_admin, ativo, salario,
                                              created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        usuario_servidor['nome'],
                        usuario_servidor['usuario'],
                        senha_inserir,
                        usuario_servidor.get('nivel', 1),
                        usuario_servidor.get('is_admin', 0),
                        usuario_servidor.get('ativo', 1),
                        usuario_servidor.get('salario', 0.0),
                        usuario_servidor.get('created_at', datetime.now().isoformat()),
                        usuario_servidor.get('updated_at', datetime.now().isoformat())
                    ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao inserir usuario do servidor: {e}")
            return False
    
    def _usuario_servidor_mais_recente(self, usuario_local: Dict[str, Any], usuario_servidor: Dict[str, Any]) -> bool:
        """Verifica se o usuário do servidor é mais recente que o local."""
        try:
            # Se não há updated_at local, considerar servidor mais recente
            if 'updated_at' not in usuario_local or not usuario_local['updated_at']:
                return True
            
            # Se não há updated_at no servidor, manter local
            if 'updated_at' not in usuario_servidor or not usuario_servidor['updated_at']:
                return False
            
            # Comparar datas
            def _to_dt(val: str):
                v = (val or '').replace('Z', '+00:00')
                dt = datetime.fromisoformat(v)
                # Normalizar para naive em UTC se tiver tzinfo
                if dt.tzinfo is not None:
                    return dt.astimezone(tz=None).replace(tzinfo=None)
                return dt
            local_date = _to_dt(usuario_local['updated_at'])
            server_date = _to_dt(usuario_servidor['updated_at'])
            
            return server_date > local_date
        except Exception as e:
            print(f"Erro ao comparar datas de usuario: {e}")
            return True  # Em caso de erro, atualizar
    
    def _atualizar_usuario_do_servidor(self, usuario_id: int, usuario_servidor: Dict[str, Any]) -> bool:
        """Atualiza usuário local com dados do servidor."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Verificar se as colunas uuid e synced existem
                cursor.execute("PRAGMA table_info(usuarios)")
                columns = [col[1] for col in cursor.fetchall()]
                has_uuid = 'uuid' in columns
                has_synced = 'synced' in columns
                
                # Buscar senha atual para preservar quando o servidor não enviar
                try:
                    cursor.execute("SELECT senha FROM usuarios WHERE id = ?", (usuario_id,))
                    row = cursor.fetchone()
                    senha_atual = row[0] if row else ''
                except Exception:
                    senha_atual = ''

                # Determinar senha a gravar: somente substitui se o servidor enviar um valor não vazio
                senha_nova = usuario_servidor.get('senha')
                if not senha_nova:
                    senha_nova = senha_atual

                if has_uuid and has_synced:
                    cursor.execute("""
                        UPDATE usuarios 
                        SET nome = ?, usuario = ?, senha = ?, nivel = ?, is_admin = ?, ativo = ?, salario = ?,
                            updated_at = ?, uuid = ?, synced = 1
                        WHERE id = ?
                    """, (
                        usuario_servidor['nome'],
                        usuario_servidor['usuario'],
                        senha_nova,
                        usuario_servidor.get('nivel', 1),
                        usuario_servidor.get('is_admin', 0),
                        usuario_servidor.get('ativo', 1),
                        usuario_servidor.get('salario', 0.0),
                        usuario_servidor.get('updated_at', datetime.now().isoformat()),
                        usuario_servidor['uuid'],
                        usuario_id
                    ))
                else:
                    cursor.execute("""
                        UPDATE usuarios 
                        SET nome = ?, usuario = ?, senha = ?, nivel = ?, is_admin = ?, ativo = ?, salario = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (
                        usuario_servidor['nome'],
                        usuario_servidor['usuario'],
                        senha_nova,
                        usuario_servidor.get('nivel', 1),
                        usuario_servidor.get('is_admin', 0),
                        usuario_servidor.get('ativo', 1),
                        usuario_servidor.get('salario', 0.0),
                        usuario_servidor.get('updated_at', datetime.now().isoformat()),
                        usuario_id
                    ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao atualizar usuario do servidor: {e}")
            return False
    
    async def _sincronizar_usuarios_antigos(self) -> int:
        """Sincroniza usuários antigos não sincronizados com o servidor.
        Se o servidor estiver vazio, envia TODOS os usuários locais com UUID (ativo=1),
        independentemente do flag synced local."""
        print("FASE 2: Enviando usuarios antigos...")
        print("Verificando usuarios antigos nao sincronizados...")

        # 1) Detectar se o servidor está vazio
        servidor_vazio = False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.api_base}/usuarios/", timeout=8.0)
                if resp.status_code == 200:
                    usuarios_srv = resp.json()
                    servidor_vazio = len(usuarios_srv) == 0
        except Exception:
            servidor_vazio = False

        # 2) Selecionar usuários locais
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if servidor_vazio:
                print("Servidor vazio - sincronizando TODOS os usuarios locais...")
                cursor.execute(
                    """
                    SELECT id, nome, usuario, senha, nivel, is_admin, ativo, salario,
                           created_at, updated_at, uuid, COALESCE(synced,0) as synced
                    FROM usuarios
                    WHERE uuid IS NOT NULL AND TRIM(uuid) <> '' AND ativo = 1
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT id, nome, usuario, senha, nivel, is_admin, ativo, salario,
                           created_at, updated_at, uuid, COALESCE(synced,0) as synced
                    FROM usuarios
                    WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND TRIM(uuid) <> ''
                    """
                )
            usuarios_local = cursor.fetchall()
        except Exception as e:
            print(f"Erro ao consultar usuarios antigos: {e}")
            return 0

        print(f"Encontrados {len(usuarios_local)} usuarios para sincronizar")

        # 3) Enviar para o servidor
        enviados = 0
        async with httpx.AsyncClient() as client:
            for u in usuarios_local:
                try:
                    uid, nome, usuario_login, senha_hash, nivel, is_admin, ativo, salario, created_at, updated_at, uuid_val, synced_val = u
                    data = {
                        "uuid": uuid_val,
                        "nome": nome,
                        "usuario": usuario_login,
                        "is_admin": bool(is_admin),
                        "ativo": True
                    }
                    # Campo 'senha' é obrigatório no backend.
                    # Se não houver hash local, envia uma senha padrão para permitir criação no servidor.
                    default_plain_password = "842384"
                    if isinstance(senha_hash, str) and senha_hash.strip():
                        data["senha"] = senha_hash
                    else:
                        data["senha"] = default_plain_password

                    print(f"Enviando usuario antigo: {nome} (usuario: {usuario_login})")

                    # Tentar criar
                    r = await client.post(f"{self.api_base}/usuarios/", json=data, timeout=10.0)
                    if r.status_code in (200, 201):
                        cursor.execute("UPDATE usuarios SET synced = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (uid,))
                        conn.commit()
                        enviados += 1
                        continue

                    # Se já existe (409/400/500 duplicate), tentar atualizar
                    if r.status_code in (400, 409) or (r.status_code == 500 and 'duplicate' in (r.text or '').lower()):
                        pr = await client.put(f"{self.api_base}/usuarios/{uuid_val}", json=data, timeout=10.0)
                        if pr.status_code == 200:
                            cursor.execute("UPDATE usuarios SET synced = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (uid,))
                            conn.commit()
                            enviados += 1
                            continue
                        # Se o servidor disser que não encontrou, criar novamente
                        if pr.status_code == 404:
                            cr = await client.post(f"{self.api_base}/usuarios/", json=data, timeout=10.0)
                            if cr.status_code in (200, 201, 409):
                                cursor.execute("UPDATE usuarios SET synced = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (uid,))
                                conn.commit()
                                enviados += 1
                                continue

                    print(f"[WARN] Falha ao enviar usuario {nome}: {r.status_code} - {r.text}")
                except Exception as e:
                    print(f"Erro ao processar usuario {u[1]}: {e}")

        try:
            conn.close()
        except Exception:
            pass

        print(f"Sincronizacao de usuarios antigos concluida: {enviados}/{len(usuarios_local)} enviados")
        return enviados
    
    async def _obter_mudancas_pendentes(self) -> List[Dict[str, Any]]:
        """Obtém mudanças pendentes de usuários."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, entity_type, entity_id, operation, data_json, created_at
                FROM change_log 
                WHERE entity_type = 'usuarios' AND status = 'pending'
                ORDER BY created_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def listar_todos(self) -> List[Dict[str, Any]]:
        """Lista todos os usuários."""
        from database.database import Database
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome, usuario, is_admin, pode_abastecer, 
                       pode_gerenciar_despesas, ativo, salario, uuid, synced
                FROM usuarios 
                ORDER BY nome
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def buscar_por_nome_ou_usuario(self, termo: str) -> List[Dict[str, Any]]:
        """Busca usuários por nome ou nome de usuário."""
        from database.database import Database
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome, usuario, is_admin, pode_abastecer, 
                       pode_gerenciar_despesas, ativo, salario, uuid, synced
                FROM usuarios 
                WHERE LOWER(nome) LIKE ? OR LOWER(usuario) LIKE ?
                ORDER BY nome
            """, (f"%{termo.lower()}%", f"%{termo.lower()}%"))
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
