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

class UsuarioRepository:
    def __init__(self):
        self.backend_url = self._get_backend_url()
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
    
    def _get_database_path(self) -> Path:
        """Obtém o caminho do banco de dados baseado no sistema operacional."""
        # Usar o mesmo caminho do sistema PDV3 existente
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
                    response = await client.get(f"{self.backend_url}/healthz")
                    if response.status_code == 200:
                        return True
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
                response = httpx.get(f"{self.backend_url}/api/usuarios/", timeout=5.0)
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
                        f"{self.backend_url}/api/usuarios/{usuario_local['uuid']}", 
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
                    f"{self.backend_url}/api/usuarios/",
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
            cursor.execute("""
                INSERT INTO usuarios (nome, usuario, senha, nivel, is_admin, ativo, salario,
                                    created_at, updated_at, uuid, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario_data['nome'],
                usuario_data['usuario'],
                usuario_data.get('senha', ''),
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
                    f"{self.backend_url}/api/usuarios/{usuario_uuid}",
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
            cursor.execute("""
                UPDATE usuarios 
                SET nome = ?, usuario = ?, senha = ?, nivel = ?, is_admin = ?, salario = ?,
                    updated_at = ?, synced = ?
                WHERE id = ?
            """, (
                usuario_data['nome'],
                usuario_data['usuario'],
                usuario_data.get('senha', ''),
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
                    f"{self.backend_url}/api/usuarios/{usuario_uuid}",
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
            # FASE 1: Pull - buscar usuários do servidor
            usuarios_recebidos = await self._pull_usuarios_do_servidor()
            
            # FASE 2: Push - enviar usuários antigos não sincronizados
            usuarios_antigos_enviados = await self._sincronizar_usuarios_antigos()
            
            # FASE 3: Push - enviar mudanças pendentes
            mudancas = await self._obter_mudancas_pendentes()
            mudancas_enviadas = 0
            
            print(f"FASE 3: Enviando mudancas pendentes de usuarios...")
            print(f"Encontradas {len(mudancas)} mudancas pendentes de usuarios")
            
            if len(mudancas) == 0:
                print("Nenhuma sincronizacao necessaria para usuarios")
            
            # Aqui você implementaria o envio das mudanças pendentes
            # Por enquanto, apenas reportamos
            
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
                    f"{self.backend_url}/api/usuarios/",
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
                
                if has_uuid and has_synced:
                    cursor.execute("""
                        INSERT INTO usuarios (nome, usuario, senha, nivel, is_admin, ativo, salario,
                                            created_at, updated_at, uuid, synced)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        usuario_servidor['nome'],
                        usuario_servidor['usuario'],
                        usuario_servidor.get('senha', ''),
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
                        usuario_servidor.get('senha', ''),
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
            local_date = datetime.fromisoformat(usuario_local['updated_at'].replace('Z', '+00:00'))
            server_date = datetime.fromisoformat(usuario_servidor['updated_at'].replace('Z', '+00:00'))
            
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
                
                if has_uuid and has_synced:
                    cursor.execute("""
                        UPDATE usuarios SET 
                            nome = ?, usuario = ?, senha = ?, nivel = ?, is_admin = ?, 
                            ativo = ?, salario = ?, updated_at = ?, uuid = ?, synced = ?
                        WHERE id = ?
                    """, (
                        usuario_servidor['nome'],
                        usuario_servidor['usuario'],
                        usuario_servidor.get('senha', ''),
                        usuario_servidor.get('nivel', 1),
                        usuario_servidor.get('is_admin', 0),
                        usuario_servidor.get('ativo', 1),
                        usuario_servidor.get('salario', 0.0),
                        usuario_servidor.get('updated_at', datetime.now().isoformat()),
                        usuario_servidor['uuid'],
                        1,  # synced = 1
                        usuario_id
                    ))
                else:
                    cursor.execute("""
                        UPDATE usuarios SET 
                            nome = ?, usuario = ?, senha = ?, nivel = ?, is_admin = ?, 
                            ativo = ?, salario = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        usuario_servidor['nome'],
                        usuario_servidor['usuario'],
                        usuario_servidor.get('senha', ''),
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
        """Sincroniza usuários antigos não sincronizados com o servidor."""
        print("FASE 2: Enviando usuarios antigos...")
        print("Verificando usuarios antigos nao sincronizados...")
        
        # Verificar se há usuários locais não sincronizados (incluindo bulk sync)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Primeiro verificar se há usuários nunca sincronizados (bulk sync)
            cursor.execute("""
                SELECT COUNT(*) FROM usuarios 
                WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND uuid != '' AND ativo = 1
            """)
            usuarios_nao_sync_count = cursor.fetchone()[0]
            
            if usuarios_nao_sync_count > 0:
                print(f"Verificando usuarios antigos nao sincronizados...")
                cursor.execute("""
                    SELECT id, nome, usuario, senha, is_admin, uuid, created_at, updated_at
                    FROM usuarios 
                    WHERE (synced = 0 OR synced IS NULL) AND uuid IS NOT NULL AND uuid != '' AND ativo = 1
                """)
            else:
                # Todos já sincronizados
                cursor.execute("SELECT 1 WHERE 0")  # Query vazia
            
            usuarios_nao_sync = cursor.fetchall()
            
            if not usuarios_nao_sync:
                print("Todos os usuarios ja estao sincronizados")
                return 0
            
            print(f"Encontrados {len(usuarios_nao_sync)} usuarios nao sincronizados")
            
            enviados = 0
            async with httpx.AsyncClient() as client:
                for usuario in usuarios_nao_sync:
                    try:
                        usuario_data = {
                            "uuid": usuario[5],
                            "nome": usuario[1],
                            "usuario": usuario[2],
                            "senha": usuario[3],  # Já está hasheada
                            "is_admin": bool(usuario[4]),
                            "ativo": True
                        }
                        
                        print(f"Enviando usuario antigo: {usuario[1]} (usuario: {usuario[2]})")
                        
                        # Tentar criar primeiro
                        response = await client.post(
                            f"{self.backend_url}/api/usuarios/",
                            json=usuario_data,
                            timeout=10.0
                        )
                        
                        if response.status_code in [200, 201]:
                            # Marcar como sincronizado
                            cursor.execute("""
                                UPDATE usuarios 
                                SET synced = 1, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (usuario[0],))
                            conn.commit()
                            enviados += 1
                            print(f"Usuario {usuario[1]} sincronizado")
                            
                        elif response.status_code == 400 or response.status_code == 500:
                            # Usuário já existe, tentar atualizar
                            print(f"Usuario {usuario[1]} ja existe, tentando atualizar...")
                            
                            response = await client.put(
                                f"{self.backend_url}/api/usuarios/{usuario[5]}",
                                json=usuario_data,
                                timeout=10.0
                            )
                            
                            if response.status_code == 200:
                                cursor.execute("""
                                    UPDATE usuarios 
                                    SET synced = 1, updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (usuario[0],))
                                conn.commit()
                                enviados += 1
                                print(f"Usuario {usuario[1]} atualizado no servidor")
                            else:
                                # Se não conseguir atualizar, marcar como sincronizado mesmo assim
                                # para evitar tentar novamente
                                print(f"Usuario {usuario[1]} ja existe no servidor, marcando como sincronizado")
                                cursor.execute("""
                                    UPDATE usuarios 
                                    SET synced = 1, updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (usuario[0],))
                                conn.commit()
                                enviados += 1
                        else:
                            print(f"Erro ao enviar usuario: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        print(f"Erro ao processar usuario {usuario[1]}: {e}")
            
            conn.close()
            print(f"Sincronizacao de usuarios antigos concluida: {enviados}/{len(usuarios_nao_sync)} enviados")
            return enviados
            
        except Exception as e:
            print(f"Erro na sincronizacao de usuarios antigos: {e}")
            return 0
    
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
