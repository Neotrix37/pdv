import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from repositories.produto_repository import ProdutoRepository
from repositories.usuario_repository import UsuarioRepository
from repositories.cliente_repository import ClienteRepository
from repositories.venda_repository import VendaRepository
from database.backup_recovery import BackupRecoveryManager
import json

class SyncManager:
    """Gerenciador centralizado de sincronização para todas as entidades."""
    
    def __init__(self):
        # Inicializar gerenciador de recuperação de backup
        self.backup_recovery = BackupRecoveryManager()
        
        # Executar verificação automática de backup na inicialização
        self._auto_check_backup_recovery()
        
        self.backend_url = self._get_backend_url()
        self.auto_reconcile_sales = self._get_config_flag('auto_reconcile_sales', default=True)
        self.auto_reconcile_stock = self._get_config_flag('auto_reconcile_stock', default=True)
        self.produto_repo = ProdutoRepository(backend_url=self.backend_url)
        self.usuario_repo = UsuarioRepository(backend_url=self.backend_url)
        self.cliente_repo = ClienteRepository(backend_url=self.backend_url)
        self.venda_repo = VendaRepository(backend_url=self.backend_url)
        
        # Lista de repositórios padrão (não usada para a ordem crítica)
        self.repositories = [
            ('produtos', self.produto_repo),
            ('usuarios', self.usuario_repo),
            ('clientes', self.cliente_repo),
            ('vendas', self.venda_repo)
        ]
    
    def _get_backend_url(self) -> str:
        """Obtém a URL do backend do arquivo de configuração."""
        try:
            candidates = []
            # 1) Caminhos quando empacotado (PyInstaller)
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                candidates.append(os.path.join(exe_dir, 'config.json'))
                candidates.append(os.path.join(exe_dir, '_internal', 'config.json'))

            # 2) Caminho do repositório (dev)
            repo_root = os.path.dirname(os.path.dirname(__file__))
            candidates.append(os.path.join(repo_root, 'config.json'))

            for cfg in candidates:
                try:
                    if os.path.exists(cfg):
                        with open(cfg, 'r', encoding='utf-8') as f:
                            conf = json.load(f)
                            url = conf.get('server_url')
                            if url:
                                return url
                except Exception:
                    continue
        except Exception:
            pass
        return os.getenv("BACKEND_URL", "http://localhost:8000")

    def _get_config_flag(self, key: str, default: bool = False) -> bool:
        """Lê um booleano de config.json (no repo root) com fallback para default."""
        try:
            repo_root = os.path.dirname(os.path.dirname(__file__))
            cfg_path = os.path.join(repo_root, 'config.json')
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    conf = json.load(f)
                    val = conf.get(key)
                    if isinstance(val, bool):
                        return val
        except Exception:
            pass
        return bool(default)

    def _reconciliar_vendas(self):
        """Executa reconciliação de vendas usando o script de utilidade, se existir.
        Melhor esforço: não falha a sincronização caso haja erro aqui.
        """
        try:
            import importlib.util
            import traceback
            # Localizar script: pdv3/scripts/reconcile_sales_with_server.py
            repo_root = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(repo_root, 'scripts', 'reconcile_sales_with_server.py')
            if not os.path.exists(script_path):
                # Tentativa alternativa: subir um nível (quando rodando em contextos diferentes)
                alt_path = os.path.join(os.path.dirname(repo_root), 'pdv3', 'scripts', 'reconcile_sales_with_server.py')
                if os.path.exists(alt_path):
                    script_path = alt_path
            if not os.path.exists(script_path):
                print("[RECON] Script reconcile_sales_with_server.py não encontrado - pulando")
                return
            spec = importlib.util.spec_from_file_location('reconcile_sales_with_server', script_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, 'main') and callable(mod.main):
                print("[RECON] Executando reconciliação de vendas pós-sync...")
                mod.main()
                print("[RECON] Reconciliação de vendas concluída")
            else:
                print("[RECON] Função main() não encontrada no script - pulando")
        except Exception as e:
            print(f"[RECON] Erro ao executar reconciliação de vendas: {e}")
            try:
                traceback.print_exc()
            except Exception:
                pass

    def _reconciliar_estoque(self):
        """Executa reconciliação de estoque usando o script utilitário.
        Sincroniza estoque e preços locais para o servidor quando divergirem.
        """
        try:
            import importlib.util
            import traceback
            repo_root = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(repo_root, 'scripts', 'reconcile_stock_with_server.py')
            if not os.path.exists(script_path):
                alt_path = os.path.join(os.path.dirname(repo_root), 'pdv3', 'scripts', 'reconcile_stock_with_server.py')
                script_path = alt_path if os.path.exists(alt_path) else script_path
            if not os.path.exists(script_path):
                print("[RECON-STOCK] Script reconcile_stock_with_server.py não encontrado - pulando")
                return
            spec = importlib.util.spec_from_file_location('reconcile_stock_with_server', script_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, 'main') and callable(mod.main):
                print("[RECON-STOCK] Executando reconciliação de estoque pós-sync...")
                mod.main()
                print("[RECON-STOCK] Reconciliação de estoque concluída")
            else:
                print("[RECON-STOCK] Função main() não encontrada no script - pulando")
        except Exception as e:
            print(f"[RECON-STOCK] Erro ao executar reconciliação de estoque: {e}")
            try:
                traceback.print_exc()
            except Exception:
                pass

    def _auto_check_backup_recovery(self):
        """Verificação automática de recuperação de backup na inicialização."""
        try:
            print("Verificando integridade do banco após possível restauração de backup...")
            # DESABILITADO: Sistema de backup estava restaurando dados antigos e resetando estoque
            # recovery_needed = self.backup_recovery.quick_check_and_fix()
            
            # Apenas detectar problemas sem corrigir automaticamente
            issues = self.backup_recovery.detect_backup_restoration()
            
            if issues['needs_recovery']:
                print("AVISO: Problemas detectados no banco, mas recuperação automática desabilitada")
                print("Execute manualmente se necessário: python database/backup_recovery.py")
            else:
                print("OK: Banco de dados integro")
                
        except Exception as e:
            print(f"AVISO: Erro na verificacao de backup: {e}")
            # Continuar mesmo com erro na verificação
    
    async def is_backend_online(self) -> bool:
        """Verifica se o backend está online usando qualquer repositório."""
        return await self.produto_repo.is_backend_online()
    
    async def sincronizar_todas_entidades(self) -> Dict[str, Any]:
        """Sincroniza todas as entidades com o backend."""
        print("=== INICIANDO SINCRONIZACAO COMPLETA ===")
        inicio = datetime.now()
        
        # Verificar conectividade
        if not await self.is_backend_online():
            print("Backend offline - cancelando sincronizacao")
            return {
                "status": "offline",
                "message": "Backend não está disponível",
                "timestamp": inicio.isoformat()
            }
        
        resultados = {}
        total_enviadas = 0
        total_recebidas = 0
        erros = []

        async def _sync_entity(nome: str, repo):
            nonlocal resultados, total_enviadas, total_recebidas, erros
            try:
                print(f"\n--- Sincronizando {nome} ---")
                print(f"[SYNC] Executando sincronizacao bidirecional de {nome}...")
                resultado = await repo.sincronizar_mudancas()
                resultados[nome] = resultado
                total_enviadas += resultado.get('enviadas', 0)
                total_recebidas += resultado.get('recebidas', 0)
                if resultado.get('status') == 'error':
                    erros.append(f"{nome}: {resultado.get('message')}")
            except Exception as e:
                erro_msg = f"Erro ao processar {nome}: {str(e)}"
                print(erro_msg)
                erros.append(erro_msg)
                resultados[nome] = {
                    "status": "error",
                    "message": str(e),
                    "enviadas": 0,
                    "recebidas": 0,
                    "mudancas_pendentes": 0
                }

        # Ordem crítica: produtos -> vendas, depois demais entidades
        await _sync_entity('produtos', self.produto_repo)
        # Reconciliação de estoque após produtos (antes de vendas) para alinhar valores no servidor
        try:
            if self.auto_reconcile_stock:
                self._reconciliar_estoque()
        except Exception as e:
            print(f"[SYNC] Falha ao reconciliar estoque pós-sync: {e}")
        await _sync_entity('vendas', self.venda_repo)
        # Reconciliação automática de vendas pós-sync (configurável)
        try:
            if self.auto_reconcile_sales:
                self._reconciliar_vendas()
        except Exception as e:
            print(f"[SYNC] Falha ao reconcilicar vendas pós-sync: {e}")
        # Rodar reconciliação de estoque novamente, pois vendas locais podem ter alterado estoque
        try:
            if self.auto_reconcile_stock:
                self._reconciliar_estoque()
        except Exception as e:
            print(f"[SYNC] Falha ao reconciliar estoque pós-vendas: {e}")
        # Sincronizar demais entidades
        await _sync_entity('usuarios', self.usuario_repo)
        await _sync_entity('clientes', self.cliente_repo)
        
        # O bulk sync já é executado automaticamente no sincronizar_mudancas do produto_repo
        print("\n--- Bulk sync de produtos executado automaticamente ---")
        
        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()
        
        # Resultado final
        status_final = "success" if len(erros) == 0 else "partial" if total_enviadas > 0 else "error"
        
        # Recomendações (UI pode usar para atualizar dashboard e alertar mapeamentos ausentes)
        missing_items = 0
        try:
            vr = resultados.get('vendas', {})
            missing_items = int(vr.get('itens_ignorados_por_produto_nao_mapeado', 0))
        except Exception:
            missing_items = 0

        resultado_final = {
            "status": status_final,
            "total_enviadas": total_enviadas,
            "total_recebidas": total_recebidas,
            "duracao_segundos": duracao,
            "timestamp": inicio.isoformat(),
            "resultados_detalhados": resultados,
            "erros": erros,
            "message": self._gerar_mensagem_resumo(status_final, total_enviadas, total_recebidas, erros),
            "recommendations": {
                "rebuild_dashboard": True,
                "missing_product_mappings": missing_items,
                "action_hint": "Sincronize produtos novamente se existirem itens de venda ignorados."
            }
        }
        
        print(f"\n=== SINCRONIZACAO CONCLUIDA ===")
        print(f"Status: {status_final}")
        print(f"Total enviadas: {total_enviadas}")
        print(f"Total recebidas: {total_recebidas}")
        print(f"Duracao: {duracao:.2f}s")
        if erros:
            print(f"Erros: {len(erros)}")
        
        return resultado_final
    
    def _gerar_mensagem_resumo(self, status: str, enviadas: int, recebidas: int, erros: List[str]) -> str:
        """Gera mensagem de resumo da sincronização."""
        if status == "success":
            return f"Sincronização completa! {enviadas} mudanças enviadas, {recebidas} recebidas."
        elif status == "partial":
            return f"Sincronização parcial. {enviadas} mudanças enviadas, {recebidas} recebidas. {len(erros)} erros."
        else:
            return f"Falha na sincronização. {len(erros)} erros encontrados."
    
    async def sincronizar_entidade_especifica(self, entidade: str) -> Dict[str, Any]:
        """Sincroniza uma entidade específica."""
        repo_map = {
            'produtos': self.produto_repo,
            'usuarios': self.usuario_repo,
            'clientes': self.cliente_repo,
            'vendas': self.venda_repo
        }
        
        if entidade not in repo_map:
            return {
                "status": "error",
                "message": f"Entidade '{entidade}' não encontrada. Opções: {list(repo_map.keys())}"
            }
        
        print(f"Sincronizando {entidade}...")
        repo = repo_map[entidade]
        
        try:
            resultado = await repo.sincronizar_mudancas()
            
            # Bulk sync já é executado automaticamente no sincronizar_mudancas
            if entidade == 'produtos':
                print("Bulk sync de produtos executado automaticamente")
            
            return resultado
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao sincronizar {entidade}: {str(e)}",
                "enviadas": 0,
                "recebidas": 0
            }
    
    async def obter_status_sincronizacao(self) -> Dict[str, Any]:
        """Obtém status atual da sincronização (mudanças pendentes)."""
        status = {
            "backend_online": await self.is_backend_online(),
            "timestamp": datetime.now().isoformat(),
            "entidades": {}
        }
        
        for nome, repo in self.repositories:
            try:
                # Contar mudanças pendentes
                mudancas = await repo._obter_mudancas_pendentes()
                status["entidades"][nome] = {
                    "mudancas_pendentes": len(mudancas),
                    "status": "ok"
                }
            except Exception as e:
                status["entidades"][nome] = {
                    "mudancas_pendentes": 0,
                    "status": "error",
                    "erro": str(e)
                }
        
        return status
    
    def get_all_repositories(self) -> Dict[str, Any]:
        """Retorna todos os repositórios para uso direto."""
        return {
            'produtos': self.produto_repo,
            'usuarios': self.usuario_repo,
            'clientes': self.cliente_repo,
            'vendas': self.venda_repo
        }
    
    async def limpar_change_log_sincronizado(self) -> Dict[str, Any]:
        """Remove entradas já sincronizadas do change_log (limpeza)."""
        print("Limpando change_log de entradas sincronizadas...")
        
        import sqlite3
        from pathlib import Path
        
        db_path = Path(__file__).parent.parent / 'database' / 'sistema.db'
        
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                # Contar entradas antes da limpeza
                cursor.execute("SELECT COUNT(*) FROM change_log WHERE status = 'synced'")
                antes = cursor.fetchone()[0]
                
                # Remover entradas sincronizadas mais antigas que 7 dias
                cursor.execute("""
                    DELETE FROM change_log 
                    WHERE status = 'synced' 
                    AND datetime(created_at) < datetime('now', '-7 days')
                """)
                
                removidas = cursor.rowcount
                conn.commit()
                
                # Contar entradas após limpeza
                cursor.execute("SELECT COUNT(*) FROM change_log")
                total_restante = cursor.fetchone()[0]
                
                return {
                    "status": "success",
                    "entradas_antes": antes,
                    "entradas_removidas": removidas,
                    "entradas_restantes": total_restante,
                    "message": f"Limpeza concluída. {removidas} entradas removidas."
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na limpeza: {str(e)}"
            }
    
    async def verificar_recuperacao_backup(self) -> Dict[str, Any]:
        """Verifica se há necessidade de recuperação pós-backup."""
        print("=== VERIFICAÇÃO DE RECUPERAÇÃO DE BACKUP ===")
        
        try:
            issues = self.backup_recovery.detect_backup_restoration()
            
            return {
                "status": "success",
                "needs_recovery": issues['needs_recovery'],
                "issues_found": issues,
                "message": "Verificação concluída" if not issues['needs_recovery'] else "Recuperação necessária"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na verificação: {str(e)}"
            }
    
    async def executar_recuperacao_backup(self) -> Dict[str, Any]:
        """Executa recuperação completa pós-backup."""
        print("=== EXECUTANDO RECUPERAÇÃO DE BACKUP ===")
        
        try:
            recovery_result = self.backup_recovery.perform_full_recovery()
            
            return {
                "status": "success" if recovery_result['success'] else "error",
                "recovery_details": recovery_result,
                "message": "Recuperação concluída" if recovery_result['success'] else "Recuperação falhou"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na recuperação: {str(e)}"
            }
    
    async def obter_status_backup_recovery(self) -> Dict[str, Any]:
        """Obtém status detalhado de todas as tabelas híbridas."""
        try:
            status = self.backup_recovery.get_recovery_status()
            
            return {
                "status": "success",
                "backup_status": status,
                "message": f"Status: {status['overall_health']}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao obter status: {str(e)}"
            }
