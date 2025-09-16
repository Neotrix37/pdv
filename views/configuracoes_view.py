import flet as ft
import sqlite3
import os
import shutil
from datetime import datetime
from database.database import Database
import json
from utils.translations import get_text
from utils.translation_mixin import TranslationMixin

class ConfiguracoesView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        
        # Diretório para backups
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
        # Campos de configuração
        self.nome_empresa = ft.TextField(
            label=self.t("company_name"),
            hint_text=self.t("enter_company_name"),
            width=400,
            height=50,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        self.idioma = ft.Dropdown(
            label=self.t("language"),
            width=200,
            options=[
                ft.dropdown.Option("pt", "Português"),
                ft.dropdown.Option("en", "English")
            ],
            value="pt",
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Carregar configurações atuais
        self.carregar_configuracoes()
        
        # Carregar configurações existentes
        self.config = self.carregar_configuracoes()

    def fechar_dialogo(self, dlg):
        dlg.open = False
        self.page.update()

    def carregar_configuracoes(self):
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return {}

    def salvar_configuracoes(self, e):
        try:
            config = {
                'nome_empresa': self.nome_empresa.value,
                'idioma': self.idioma.value
            }
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            # Atualizar idioma na página
            self.page.data["language"] = self.idioma.value
            
            # Mostrar mensagem de sucesso
            snack = ft.SnackBar(
                content=ft.Text(get_text("settings_saved", self.idioma.value)),
                bgcolor=ft.colors.GREEN
            )
            if self.page and hasattr(self.page, "show_snack_bar"):
                    self.page.show_snack_bar(snack)
            self.page.update()
            
            # Recarregar a página para aplicar o novo idioma
            self.page.go("/dashboard")
            
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            try:
                snack = ft.SnackBar(
                    content=ft.Text(get_text("settings_error", self.idioma.value)),
                    bgcolor=ft.colors.RED
                )
                if self.page and hasattr(self.page, "show_snack_bar"):
                    self.page.show_snack_bar(snack)
                self.page.update()
            except:
                print("Erro ao mostrar mensagem de erro")

    def fazer_backup(self, e):
        """Abre diálogo para criar backup com nome personalizado"""
        
        # Campo para nome do backup
        nome_backup_field = ft.TextField(
            label="Nome do Backup",
            hint_text="Ex: backup_antes_atualizacao, backup_final_mes, etc.",
            width=400,
            height=50,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            value=""  # Vazio por padrão para nome personalizado
        )
        
        # Checkbox para usar timestamp automático
        usar_timestamp = ft.Checkbox(
            label="Adicionar data/hora automaticamente",
            value=True,
            check_color=ft.colors.BLUE
        )
        
        def executar_backup(e):
            try:
                # Obter nome do backup
                nome_personalizado = nome_backup_field.value.strip()
                
                # Gerar timestamp se solicitado
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if nome_personalizado:
                    # Nome personalizado
                    if usar_timestamp.value:
                        nome_arquivo = f"{nome_personalizado}_{timestamp}.db"
                    else:
                        nome_arquivo = f"{nome_personalizado}.db"
                else:
                    # Nome padrão com timestamp
                    nome_arquivo = f"backup_{timestamp}.db"
                
                # Verificar se arquivo já existe
                backup_file = os.path.join(self.backup_dir, nome_arquivo)
                if os.path.exists(backup_file):
                    # Adicionar sufixo numérico se arquivo existir
                    contador = 1
                    nome_base = nome_arquivo.replace('.db', '')
                    while os.path.exists(os.path.join(self.backup_dir, f"{nome_base}_{contador}.db")):
                        contador += 1
                    backup_file = os.path.join(self.backup_dir, f"{nome_base}_{contador}.db")
                    nome_arquivo = f"{nome_base}_{contador}.db"
                
                # Copiar banco de dados
                shutil.copy2(self.db.db_path, backup_file)
                
                # Fechar diálogo
                dlg_backup.open = False
                self.page.update()
                
                # Mostrar sucesso com nome do arquivo criado
                snack = ft.SnackBar(
                    content=ft.Text(f"✅ Backup criado: {nome_arquivo}"),
                    bgcolor=ft.colors.GREEN,
                    duration=4000
                )
                self.page.show_snack_bar(snack)
                
            except Exception as error:
                print(f"Erro ao fazer backup: {error}")
                
                # Fechar diálogo em caso de erro
                dlg_backup.open = False
                self.page.update()
                
                snack = ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao criar backup: {str(error)}"),
                    bgcolor=ft.colors.RED,
                    duration=5000
                )
                self.page.show_snack_bar(snack)
        
        def fechar_dialogo(e):
            dlg_backup.open = False
            self.page.update()
        
        # Diálogo para criar backup
        dlg_backup = ft.AlertDialog(
            modal=True,
            title=ft.Text("🗃️ Criar Backup", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text(
                    "Personalize o nome do seu backup:",
                    size=16,
                    color=ft.colors.GREY_700
                ),
                ft.Container(height=10),  # Espaçamento
                nome_backup_field,
                ft.Container(height=10),  # Espaçamento
                usar_timestamp,
                ft.Container(height=10),  # Espaçamento
                ft.Text(
                    "💡 Dica: Use nomes descritivos como 'antes_atualizacao', 'final_mes', etc.",
                    size=12,
                    color=ft.colors.BLUE_700,
                    italic=True
                )
            ], tight=True, spacing=5),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    icon=ft.icons.CANCEL,
                    on_click=fechar_dialogo
                ),
                ft.ElevatedButton(
                    "Criar Backup",
                    icon=ft.icons.BACKUP,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                    on_click=executar_backup
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dlg_backup
        dlg_backup.open = True
        self.page.update()

    def restaurar_backup(self, e):
        try:
            # Listar backups disponíveis
            backups = []
            for f in os.listdir(self.backup_dir):
                if f.endswith('.db'):
                    backup_path = os.path.join(self.backup_dir, f)
                    stat = os.stat(backup_path)
                    data = datetime.fromtimestamp(stat.st_mtime)
                    tamanho = stat.st_size / (1024 * 1024)
                    
                    agora = datetime.now()
                    diff = agora - data
                    
                    if diff.days > 0:
                        tempo_decorrido = f"há {diff.days} {'dia' if diff.days == 1 else 'dias'}"
                    elif diff.seconds >= 3600:
                        horas = diff.seconds // 3600
                        tempo_decorrido = f"há {horas} {'hora' if horas == 1 else 'horas'}"
                    elif diff.seconds >= 60:
                        minutos = diff.seconds // 60
                        tempo_decorrido = f"há {minutos} {'minuto' if minutos == 1 else 'minutos'}"
                    else:
                        tempo_decorrido = f"há {diff.seconds} {'segundo' if diff.seconds == 1 else 'segundos'}"
                    
                    backups.append({
                        'arquivo': f,
                        'data': data,
                        'tamanho': tamanho,
                        'path': backup_path,
                        'tempo_decorrido': tempo_decorrido
                    })
            
            if not backups:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(get_text("no_backups", self.idioma.value)),
                        bgcolor=ft.colors.RED
                    )
                )
                return
            
            backups.sort(key=lambda x: x['data'], reverse=True)
            
            # Criar lista de backups formatada
            backup_list = ft.ListView(
                expand=True,  # Faz a lista ocupar todo o espaço disponível
                spacing=10,
                padding=20,
            )
            
            # Variável para controlar o item selecionado
            self.selected_backup = None
            
            def select_backup(e):
                # Atualiza a aparência de todos os containers
                for container in backup_list.controls:
                    if container == e.control:
                        container.bgcolor = ft.colors.BLUE_100
                        container.border = ft.border.all(2, ft.colors.BLUE)
                        self.selected_backup = container.data
                    else:
                        container.bgcolor = ft.colors.BLUE_50
                        container.border = ft.border.all(1, ft.colors.BLUE_200)
                self.page.update()
            
            for backup in backups:
                container = ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"📁 {backup['arquivo']}",
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Row([
                            ft.Text(
                                f"📅 {backup['data'].strftime('%d/%m/%Y às %H:%M:%S')}",
                                size=14
                            ),
                            ft.Text(
                                f"⏱️ {backup['tempo_decorrido']}",
                                size=14,
                                color=ft.colors.GREY_700
                            )
                        ]),
                        ft.Text(
                            f"📊 {backup['tamanho']:.2f} MB",
                            size=14
                        )
                    ]),
                    bgcolor=ft.colors.BLUE_50,
                    padding=10,
                    border_radius=5,
                    data=backup['path'],
                    border=ft.border.all(1, ft.colors.BLUE_200),
                    on_click=select_backup,  # Adiciona evento de clique
                    ink=True  # Adiciona efeito de ripple ao clicar
                )
                
                # Adiciona comportamento de hover usando on_hover
                def on_hover_changed(e):
                    e.control.bgcolor = ft.colors.BLUE_100 if e.data == "true" else ft.colors.BLUE_50
                    self.page.update()
                
                container.on_hover = on_hover_changed
                backup_list.controls.append(container)
            
            # Criar diálogo de confirmação
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(get_text("restore_backup", self.idioma.value)),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(get_text("select_backup", self.idioma.value)),
                        backup_list
                    ]),
                    width=600,  # Largura fixa para o diálogo
                    height=400,  # Altura fixa para o diálogo
                ),
                actions=[
                    ft.TextButton(
                        get_text("cancel", self.idioma.value),
                        on_click=lambda x: self.fechar_dialogo(dlg)
                    ),
                    ft.TextButton(
                        get_text("restore", self.idioma.value),
                        on_click=lambda x: self.confirmar_restauracao_simplificada(self.selected_backup) if self.selected_backup else None
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao listar backups: {e}")
            snack = ft.SnackBar(
                content=ft.Text(get_text("backup_error", self.idioma.value)),
                bgcolor=ft.colors.RED
            )
            if self.page and hasattr(self.page, "show_snack_bar"):
                    self.page.show_snack_bar(snack)
            self.page.update()

    def confirmar_restauracao(self, backup_path):
        """Wrapper de compatibilidade: delega para a versão simplificada/robusta."""
        try:
            return self.confirmar_restauracao_simplificada(backup_path)
        except Exception as e:
            print(f"Erro na confirmar_restauracao (wrapper): {e}")
            # Exibe snackbar genérico
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(
                        f"❌ Erro ao restaurar: {str(e)}",
                        color=ft.colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=ft.colors.RED_700,
                    duration=5000
                )
            )
            self.page.update()
            return False

    def confirmar_restauracao_simplificada(self, backup_path):
        """
        Versão simplificada e robusta da restauração de backup.
        Compatível com o sistema de banco único (APPDATA).
        Implementa backup condicional para evitar backups desnecessários.
        
        Args:
            backup_path (str): Caminho para o arquivo de backup a ser restaurado.
        """
        try:
            # Fechar diálogo se estiver aberto
            dlg = getattr(self, 'dialog', None)
            if dlg and dlg.open:
                dlg.open = False
            
            # Mostrar indicador de carregamento
            loading_snackbar = ft.SnackBar(
                content=ft.Row([
                    ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.colors.WHITE),
                    ft.Text(" Restaurando backup...", color=ft.colors.WHITE)
                ]),
                bgcolor=ft.colors.BLUE,
                duration=0
            )
            self.page.show_snack_bar(loading_snackbar)
            self.page.update()
            
            # Verificar se arquivo de backup existe
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_path}")
            
            backup_size = os.path.getsize(backup_path)
            if backup_size < 1000:  # Menos de 1KB é suspeito
                raise ValueError("Arquivo de backup muito pequeno ou corrompido")
            
            print(f"[RESTAURAÇÃO] Iniciando restauração de: {backup_path}")
            print(f"[RESTAURAÇÃO] Tamanho do backup: {backup_size / (1024*1024):.2f} MB")
            
            # Fazer backup de segurança do banco atual (apenas se necessário)
            pre_restore_backup = None
            if os.path.exists(str(self.db.db_path)):
                # Verificar se o banco atual é diferente do backup que será restaurado
                banco_atual_size = os.path.getsize(str(self.db.db_path))
                
                # Comparar tamanhos e checksums para evitar backups desnecessários
                import hashlib
                
                def get_file_hash(filepath):
                    hash_md5 = hashlib.md5()
                    with open(filepath, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                    return hash_md5.hexdigest()
                
                banco_atual_hash = get_file_hash(str(self.db.db_path))
                backup_hash = get_file_hash(backup_path)
                
                if banco_atual_hash != backup_hash:
                    # Bancos são diferentes, criar backup de segurança
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pre_restore_backup = os.path.join(self.backup_dir, f"pre_restore_{timestamp}.db")
                    shutil.copy2(str(self.db.db_path), pre_restore_backup)
                    print(f"[BACKUP] Backup de segurança criado: {pre_restore_backup}")
                    print(f"[BACKUP] Banco atual ({banco_atual_size} bytes) diferente do backup ({backup_size} bytes)")
                else:
                    print(f"[BACKUP] Banco atual idêntico ao backup - backup desnecessário")
                    print(f"[BACKUP] Tamanho: {banco_atual_size} bytes, Hash: {banco_atual_hash[:8]}...")
            
            # Tentar restauração ONLINE via API de backup do SQLite (evita lock de arquivo no Windows)
            online_ok = False
            try:
                print("[RESTAURAÇÃO] Tentando restauração online via SQLite backup API...")
                src = sqlite3.connect(backup_path, timeout=10)
                try:
                    # Desabilitar FKs temporariamente
                    try:
                        self.db.conn.execute("PRAGMA foreign_keys=OFF")
                    except Exception:
                        pass
                    # Transação exclusiva para aplicar backup
                    self.db.conn.isolation_level = None
                    self.db.conn.execute("BEGIN IMMEDIATE")
                    src.backup(self.db.conn)
                    self.db.conn.execute("COMMIT")
                    try:
                        self.db.conn.execute("PRAGMA foreign_keys=ON")
                    except Exception:
                        pass
                    online_ok = True
                    print("[RESTAURAÇÃO] Restauração online concluída com sucesso")
                finally:
                    src.close()
            except Exception as online_e:
                print(f"[RESTAURAÇÃO] Falha na restauração online: {online_e}")

            if not online_ok:
                # Fallback: fechar conexão atual e substituir arquivo com retries
                try:
                    if hasattr(self.db, 'conn') and self.db.conn:
                        try:
                            self.db.conn.close()
                        except Exception:
                            pass
                        print("[RESTAURAÇÃO] Conexão fechada")
                    # Aguardar liberação do arquivo com retries
                    import time
                    attempts = 5
                    for i in range(attempts):
                        try:
                            if os.path.exists(str(self.db.db_path)):
                                os.remove(str(self.db.db_path))
                            break
                        except PermissionError as pe:
                            if i == attempts - 1:
                                raise pe
                            time.sleep(0.6)
                    print("[RESTAURAÇÃO] Banco atual removido")
                    # Copiar backup
                    shutil.copy2(backup_path, str(self.db.db_path))
                    print(f"[RESTAURAÇÃO] Backup copiado para: {self.db.db_path}")
                    if not os.path.exists(str(self.db.db_path)):
                        raise Exception("Falha ao copiar arquivo de backup")
                    # Resetar singleton e recriar conexão
                    from database.database import Database
                    Database._instance = None
                    self.db = Database()
                except Exception as fallback_e:
                    raise Exception(f"Falha na restauração por cópia de arquivo: {fallback_e}")
            
            # Verificar integridade do banco restaurado
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vendas")
            total_vendas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(CASE WHEN status = 'Anulada' THEN 0 ELSE total END), 0) FROM vendas")
            valor_total = cursor.fetchone()[0]
            
            print(f"[SUCESSO] Restauração concluída!")
            print(f"[SUCESSO] Vendas restauradas: {total_vendas}")
            print(f"[SUCESSO] Valor total: MT {valor_total:.2f}")
            
            # Verificar e corrigir esquema
            try:
                self.db.verificar_e_corrigir_esquema_pos_restauracao()
                print("[SUCESSO] Esquema verificado e corrigido")
            except Exception as e:
                print(f"[AVISO] Erro na verificação de esquema: {e}")
            
            # Mostrar mensagem de sucesso com instruções
            success_snackbar = ft.SnackBar(
                content=ft.Text(f"✅ Backup restaurado! {total_vendas} vendas, MT {valor_total:.2f} - Reiniciando sistema..."),
                bgcolor=ft.colors.GREEN,
                duration=3000
            )
            self.page.show_snack_bar(success_snackbar)
            self.page.update()
            
            # Aguardar um pouco para mostrar a mensagem
            import time
            time.sleep(1)
            
            # Forçar reinício completo da aplicação
            self.reiniciar_aplicacao_pos_restauracao()
            
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha na restauração: {e}")
            
            # Tentar restaurar backup de segurança
            if 'pre_restore_backup' in locals() and pre_restore_backup and os.path.exists(pre_restore_backup):
                try:
                    print("[RECUPERAÇÃO] Restaurando backup de segurança...")
                    if os.path.exists(str(self.db.db_path)):
                        os.remove(str(self.db.db_path))
                    shutil.copy2(pre_restore_backup, str(self.db.db_path))
                    
                    # Recriar conexão
                    from database.database import Database
                    Database._instance = None
                    self.db = Database()
                    
                    print("[RECUPERAÇÃO] Backup de segurança restaurado")
                except Exception as recovery_error:
                    print(f"[ERRO] Falha na recuperação: {recovery_error}")
            
            # Mostrar erro ao usuário
            error_snackbar = ft.SnackBar(
                content=ft.Text(f"❌ Erro na restauração: {str(e)}"),
                bgcolor=ft.colors.RED,
                duration=5000
            )
            self.page.show_snack_bar(error_snackbar)
            self.page.update()
            
            return False

    def reiniciar_aplicacao_pos_restauracao(self):
        """
        Reinicia a aplicação após restauração de backup e volta para login.
        """
        try:
            print("[REINÍCIO] Iniciando reinício da aplicação pós-restauração...")
            
            # Guardar referência da page antes de qualquer operação
            page_ref = self.page
            
            if not page_ref:
                print("[AVISO] Page é None, tentando alternativa...")
                # Tentar usar referência global ou parent
                if hasattr(self, 'parent') and hasattr(self.parent, 'page'):
                    page_ref = self.parent.page
                else:
                    print("[INFO] Restauração concluída. Sistema deve ser reiniciado manualmente.")
                    return
            
            # Método mais direto: usar threading para evitar conflitos
            import threading
            import time
            
            def fazer_redirect():
                try:
                    time.sleep(0.2)  # Pequeno delay
                    
                    # Limpar dados da sessão
                    if hasattr(page_ref, 'data'):
                        page_ref.data = {}
                    
                    if hasattr(page_ref, 'session'):
                        page_ref.session.clear()
                    
                    # Limpar views
                    if hasattr(page_ref, 'views'):
                        page_ref.views.clear()
                    
                    # Redirecionar para login
                    print("[REINÍCIO] Redirecionando para login...")
                    page_ref.go("/login")
                    page_ref.update()
                    
                    print("[REINÍCIO] Redirecionamento concluído com sucesso")
                    
                except Exception as thread_error:
                    print(f"[ERRO] Falha no redirecionamento: {thread_error}")
                    # Última tentativa: forçar reload da página inteira
                    try:
                        if hasattr(page_ref, 'window_close'):
                            print("[INFO] Fechando janela para forçar reinício...")
                            # Não fechar, apenas limpar e ir para login
                        page_ref.route = "/login"
                        page_ref.update()
                    except Exception:
                        print("[INFO] Restauração concluída. Reinicie o sistema manualmente.")
            
            # Executar redirecionamento em thread separada
            redirect_thread = threading.Thread(target=fazer_redirect, daemon=True)
            redirect_thread.start()
            
        except Exception as e:
            print(f"[ERRO] Falha no reinício da aplicação: {e}")
            print("[INFO] Restauração concluída com sucesso!")
            
            # Fallback final: tentar redirecionamento simples
            try:
                if self.page:
                    self.page.go("/login")
                    self.page.update()
                    print("[REINÍCIO] Redirecionamento de fallback executado")
            except Exception:
                print("[INFO] Sistema deve ser reiniciado manualmente para ver os dados.")

    def resetar_banco(self, e):
        try:
            # Criar diálogo de confirmação
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(get_text("warning", self.idioma.value)),
                content=ft.Text(get_text("reset_warning", self.idioma.value)),
                actions=[
                    ft.TextButton(
                        get_text("cancel", self.idioma.value),
                        on_click=lambda e: self.fechar_dialogo(dlg)
                    ),
                    ft.TextButton(
                        get_text("reset", self.idioma.value),
                        on_click=lambda e: self.confirmar_reset_banco(dlg),
                        style=ft.ButtonStyle(
                            color=ft.colors.RED
                        )
                    )
                ]
            )
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao mostrar diálogo de reset: {e}")

    def confirmar_reset_banco(self, dlg):
        """Confirma e executa o reset do banco de dados com feedback visual"""
        try:
            # Fecha o diálogo de confirmação
            self.fechar_dialogo(dlg)
            
            # Mostra indicador de carregamento
            loading_snackbar = ft.SnackBar(
                content=ft.Row([
                    ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.colors.WHITE),
                    ft.Text(" Resetando banco de dados...", color=ft.colors.WHITE)
                ]),
                bgcolor=ft.colors.BLUE,
                duration=0  # Fica visível até ser fechado explicitamente
            )
            self.page.show_snack_bar(loading_snackbar)
            self.page.update()
            
            # Tenta resetar o banco de dados
            if self.db.reset_database():
                # Esconde o snackbar de carregamento
                loading_snackbar.open = False
                
                # Mostra mensagem de sucesso
                success_snackbar = ft.SnackBar(
                    content=ft.Text(
                        "✅ Banco de dados resetado com sucesso!",
                        color=ft.colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=ft.colors.GREEN_700,
                    duration=3000
                )
                self.page.show_snack_bar(success_snackbar)
                
                # Fecha a conexão atual
                if hasattr(self.db, 'conn'):
                    try:
                        self.db.conn.close()
                    except:
                        pass
                
                # Força a reinicialização do singleton do Database
                Database._instance = None
                
                # Atualiza a referência do banco de dados
                from database.database import Database as NewDB
                self.db = NewDB()
                
                # Fecha o diálogo de confirmação se ainda estiver aberto
                if dlg and dlg.open:
                    dlg.open = False
                
                # Limpa os dados da sessão
                self.page.session.clear()
                self.page.data.clear()
                
                # Força a atualização da interface
                self.page.update()
                
                # Redireciona para a tela de login
                self.page.go("/login")
                
                # Força um reload completo da página para garantir que todos os dados sejam limpos
                self.page.window_destroy() if self.page and hasattr(self.page, "window_destroy") else None
                self.page.window_reload() if self.page and hasattr(self.page, "window_reload") else None
                
            else:
                # Esconde o snackbar de carregamento
                loading_snackbar.open = False
                
                # Mostra mensagem de erro
                error_snackbar = ft.SnackBar(
                    content=ft.Text(
                        "❌ Falha ao resetar o banco de dados. Verifique os logs para mais detalhes.",
                        color=ft.colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=ft.colors.RED_700,
                    duration=5000
                )
                self.page.show_snack_bar(error_snackbar)
            
        except Exception as e:
            print(f"Erro inesperado ao resetar banco de dados: {e}")
            
            # Tenta esconder o snackbar de carregamento se ainda estiver visível
            if 'loading_snackbar' in locals():
                loading_snackbar.open = False
            
            # Mostra mensagem de erro detalhada
            error_snackbar = ft.SnackBar(
                content=ft.Text(
                    f"❌ Erro inesperado: {str(e)}",
                    color=ft.colors.WHITE,
                    weight=ft.FontWeight.BOLD
                ),
                bgcolor=ft.colors.RED_900,
                duration=0  # Permanece até o usuário fechar
            )
            self.page.show_snack_bar(error_snackbar)
            
            # Tenta recriar a conexão com o banco de dados
            try:
                from database.database import Database as NewDB
                self.db = NewDB()
            except Exception as db_error:
                print(f"Falha ao recriar conexão com o banco: {db_error}")
                
        finally:
            # Garante que a interface seja atualizada
            self.page.update()

    def verificar_atualizar_banco(self, e):
        try:
            # Verificar se há atualizações necessárias no banco
            self.db.verificar_e_corrigir_esquema_pos_restauracao()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Banco de dados verificado e atualizado com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
        except Exception as error:
            print(f"Erro ao verificar/atualizar banco: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao verificar banco: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )
    
    def resetar_dashboard_handler(self, e):
        """Handler para resetar apenas os cards do dashboard (preserva histórico)"""
        self.resetar_dashboard_cards()
    
    def resetar_dashboard_cards(self):
        """Reseta apenas os cards do dashboard, preservando o histórico de vendas"""
        
        # Modal de confirmação
        confirmacao_field = ft.TextField(
            hint_text="Digite CONFIRMO em maiúsculas",
            width=300,
            height=50,
            color=ft.colors.BLACK
        )
        
        def executar_reset_dashboard(e):
            if confirmacao_field.value != "CONFIRMO":
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("❌ Digite 'CONFIRMO' para prosseguir"),
                        bgcolor=ft.colors.RED
                    )
                )
                return
                
            try:
                # Fazer backup antes do reset (por segurança)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(self.backup_dir, f"pre_dashboard_reset_{timestamp}.db")
                shutil.copy2(self.db.db_path, backup_file)
                
                # Para admin: reseta para todos os usuários
                if self.usuario and self.usuario.get('is_admin'):
                    # Reset das tabelas que afetam os cards do dashboard
                    # Mas preserva o histórico completo de vendas
                    
                    # Limpar apenas cache/resumos se existirem
                    # Aqui você pode implementar lógica específica para limpar
                    # apenas dados agregados que alimentam os cards
                    
                    # Por exemplo, se houver tabelas de cache/resumo:
                    # self.db.execute("DELETE FROM dashboard_cache")
                    # self.db.execute("DELETE FROM resumo_vendas_diario") 
                    
                    # Como não temos tabelas específicas de cache, vamos simular
                    # um "reset" que força recálculo dos cards
                    
                    # Criar uma entrada de controle para forçar recálculo
                    self.db.execute("""
                        INSERT OR REPLACE INTO configuracoes (chave, valor) 
                        VALUES ('dashboard_reset_timestamp', ?)
                    """, (timestamp,))
                    self.db.conn.commit()
                    
                    # Definir flag para forçar recálculo no próximo carregamento
                    if hasattr(self.page, 'data') and isinstance(self.page.data, dict):
                        self.page.data['reset_dashboard_values'] = True
                    
                    # Tentar atualizar o dashboard atual se estiver disponível
                    if hasattr(self.page, 'dashboard_view') and self.page.dashboard_view:
                        try:
                            # Usar try/except para evitar falha se o controle não estiver pronto
                            self.page.dashboard_view.atualizar_valores(resetar=True)
                            self.page.update()
                        except Exception as update_error:
                            print(f"Aviso: Não foi possível atualizar o dashboard imediatamente: {update_error}")
                    
                    mensagem = "✅ Dashboard resetado com sucesso!"
                    
                else:
                    # Para usuários comuns: reset apenas para o próprio usuário
                    if hasattr(self.page, 'data') and isinstance(self.page.data, dict):
                        self.page.data['reset_dashboard_values'] = True
                    
                    # Tentar atualizar o dashboard atual se estiver disponível
                    if hasattr(self.page, 'dashboard_view') and self.page.dashboard_view:
                        try:
                            self.page.dashboard_view.atualizar_valores(resetar=True)
                            self.page.update()
                        except Exception as update_error:
                            print(f"Aviso: Não foi possível atualizar o dashboard imediatamente: {update_error}")
                    
                    mensagem = "✅ Seu dashboard foi resetado!"
                
                self.db.conn.commit()
                
                # Fechar modal
                dlg_reset.open = False
                self.page.update()
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"{mensagem} Backup: pre_dashboard_reset_{timestamp}.db"),
                        bgcolor=ft.colors.GREEN,
                        duration=5000
                    )
                )
                
            except Exception as error:
                print(f"Erro ao resetar dashboard: {error}")
                dlg_reset.open = False
                self.page.update()
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"❌ Erro ao resetar dashboard: {str(error)}"),
                        bgcolor=ft.colors.RED,
                        duration=5000
                    )
                )
        
        def fechar_modal(e):
            dlg_reset.open = False
            self.page.update()
        
        # Determinar escopo do reset
        if self.usuario and self.usuario.get('is_admin'):
            titulo = "⚠️ Reset Dashboard (Todos os Usuários)"
            descricao = "Você está prestes a RESETAR os cards do dashboard para TODOS os usuários!"
            cor_titulo = ft.colors.RED
        else:
            titulo = "⚠️ Reset Meu Dashboard"
            descricao = "Você está prestes a RESETAR apenas os seus cards do dashboard!"
            cor_titulo = ft.colors.ORANGE
        
        # Modal de confirmação
        dlg_reset = ft.AlertDialog(
            modal=True,
            title=ft.Text(titulo, size=20, weight=ft.FontWeight.BOLD, color=cor_titulo),
            content=ft.Column([
                ft.Text(
                    descricao,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=cor_titulo
                ),
                ft.Container(height=10),
                ft.Text(
                    "✅ O histórico completo de vendas será PRESERVADO",
                    size=14,
                    color=ft.colors.GREEN,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "📊 Apenas os cards do dashboard serão afetados",
                    size=14,
                    color=ft.colors.BLUE
                ),
                ft.Container(height=10),
                ft.Text(
                    "⚠️ ATENÇÃO: Esta ação NÃO pode ser desfeita!",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.RED
                ),
                ft.Text(
                    "✅ Um backup será criado automaticamente antes do reset.",
                    size=12,
                    color=ft.colors.GREEN
                ),
                ft.Container(height=10),
                ft.Text(
                    "Digite 'CONFIRMO' para prosseguir:",
                    size=14,
                    weight=ft.FontWeight.BOLD
                ),
                confirmacao_field
            ], tight=True, spacing=5),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    icon=ft.icons.CANCEL,
                    on_click=fechar_modal
                ),
                ft.ElevatedButton(
                    "RESETAR DASHBOARD",
                    icon=ft.icons.DASHBOARD,
                    bgcolor=ft.colors.PURPLE,
                    color=ft.colors.WHITE,
                    on_click=executar_reset_dashboard
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dlg_reset
        dlg_reset.open = True
        self.page.update()




    def build(self):
        # Cabeçalho
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/dashboard")
                ),
                ft.Icon(
                    name=ft.icons.SETTINGS,
                    size=30,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    self.t("settings"),
                    size=20,
                    color=ft.colors.WHITE
                )
            ]),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
            ),
            padding=20,
            border_radius=10
        )

        # Lista de controles que serão exibidos
        controls = [header, ft.Container(height=20)]

        # Configurações da Impressora (visível para todos)
        controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.PRINT, size=24, color=ft.colors.BLUE),
                        ft.Text(
                            "Impressora",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREEN
                        )
                    ]),
                    ft.ElevatedButton(
                        "Configurar Impressora",
                        icon=ft.icons.SETTINGS,
                        on_click=lambda _: self.page.go("/printer"),
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE
                    )
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10,
                border=ft.border.all(1, ft.colors.GREY_300)
            )
        )

        # Espaçamento entre seções
        controls.append(ft.Container(height=20))

        # Seção Unificada de Backup/Restauração e Administração
        controls.append(ft.Container(height=20))
        
        # Criar linhas de botões
        linhas_botoes = []
        
        # Primeira linha - Botões comuns a todos os usuários
        linha1 = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Criar Backup",
                    icon=ft.icons.BACKUP,
                    on_click=self.fazer_backup,
                    bgcolor=ft.colors.BLUE,
                    color=ft.colors.WHITE,
                    tooltip="Criar um novo backup do banco de dados",
                    width=200,
                    height=50
                ),
                ft.ElevatedButton(
                    "Restaurar Backup",
                    icon=ft.icons.RESTORE,
                    on_click=self.restaurar_backup,
                    bgcolor=ft.colors.ORANGE,
                    color=ft.colors.WHITE,
                    tooltip="Restaurar banco de dados a partir de um backup",
                    width=200,
                    height=50
                )
            ],
            spacing=10,
            wrap=True,
            scroll=ft.ScrollMode.AUTO
        )
        linhas_botoes.append(linha1)
        
        # Segunda linha - Botões de administrador
        if self.usuario and self.usuario.get('is_admin'):
            linha2 = ft.Row(
                controls=[
                    ft.ElevatedButton(
                        "Gerenciar Backups",
                        icon=ft.icons.DELETE,
                        on_click=self.deletar_backups,
                        bgcolor=ft.colors.RED,
                        color=ft.colors.WHITE,
                        tooltip="Visualizar e gerenciar backups existentes",
                        width=200,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Verificar Banco",
                        icon=ft.icons.STORAGE,
                        on_click=self.verificar_atualizar_banco,
                        bgcolor=ft.colors.TEAL,
                        color=ft.colors.WHITE,
                        tooltip="Verificar e atualizar a estrutura do banco de dados",
                        width=200,
                        height=50
                    )
                ],
                spacing=10,
                wrap=True,
                scroll=ft.ScrollMode.AUTO
            )
            linhas_botoes.append(ft.Container(height=10))  # Espaçamento
            linhas_botoes.append(linha2)
            
            # Terceira linha - Botões de reset
            linha3 = ft.Row(
                controls=[
                    ft.ElevatedButton(
                        "Resetar Dashboard",
                        icon=ft.icons.DASHBOARD,
                        on_click=self.resetar_dashboard_handler,
                        bgcolor=ft.colors.PURPLE,
                        color=ft.colors.WHITE,
                        tooltip="Resetar apenas os cards do dashboard (preserva histórico de vendas)",
                        width=200,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Resetar Banco",
                        icon=ft.icons.WARNING_AMBER,
                        on_click=self.resetar_banco,
                        bgcolor=ft.colors.RED_900,
                        color=ft.colors.WHITE,
                        tooltip="RESETAR TODO O BANCO DE DADOS (CUIDADO!)",
                        width=200,
                        height=50
                    )
                ],
                spacing=10,
                wrap=True,
                scroll=ft.ScrollMode.AUTO
            )
            linhas_botoes.append(ft.Container(height=10))  # Espaçamento
            linhas_botoes.append(linha3)
        
        # Cria o container com todos os botoes organizados
        controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.SETTINGS_APPLICATIONS, size=24, color=ft.colors.BLUE_800),
                        ft.Text(
                            "Ferramentas do Sistema",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLUE_800
                        )
                    ]),
                    ft.Container(height=10),
                    ft.Column(
                        controls=linhas_botoes,
                        spacing=5,
                        scroll=ft.ScrollMode.AUTO
                    )
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10,
                border=ft.border.all(1, ft.colors.GREY_300)
            )
        )

        return ft.Column(controls)

    def deletar_backups(self, e):
        """Abre diálogo para deletar backups"""
        try:
            # Listar backups disponíveis
            backups = []
            for f in os.listdir(self.backup_dir):
                if f.endswith('.db'):
                    backup_path = os.path.join(self.backup_dir, f)
                    stat = os.stat(backup_path)
                    data = datetime.fromtimestamp(stat.st_mtime)
                    tamanho = stat.st_size / (1024 * 1024)
                    
                    backups.append({
                        'arquivo': f,
                        'data': data,
                        'tamanho': tamanho,
                        'path': backup_path
                    })
            
            if not backups:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(self.t("no_backups")),
                        bgcolor=ft.colors.RED
                    )
                )
                return
            
            # Ordenar por data (mais recente primeiro)
            backups.sort(key=lambda x: x['data'], reverse=True)
            
            # Criar lista de backups formatada
            backup_list = ft.ListView(
                expand=True,
                spacing=10,
                padding=20,
            )
            
            # Lista para controlar seleções
            selected_backups = []
            
            def toggle_backup(e, backup_path):
                if backup_path in selected_backups:
                    selected_backups.remove(backup_path)
                    e.control.bgcolor = ft.colors.BLUE_50
                else:
                    selected_backups.append(backup_path)
                    e.control.bgcolor = ft.colors.RED_100
                self.page.update()
            
            for backup in backups:
                container = ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"📁 {backup['arquivo']}",
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Row([
                            ft.Text(
                                f"📅 {backup['data'].strftime('%d/%m/%Y às %H:%M:%S')}",
                                size=14
                            ),
                            ft.Text(
                                f"📊 {backup['tamanho']:.2f} MB",
                                size=14
                            )
                        ])
                    ]),
                    bgcolor=ft.colors.BLUE_50,
                    padding=10,
                    border_radius=5,
                    ink=True,
                    on_click=lambda e, path=backup['path']: toggle_backup(e, path)
                )
                backup_list.controls.append(container)
            
            def confirmar_delecao(e):
                try:
                    for backup_path in selected_backups:
                        os.remove(backup_path)
                    
                    dlg_modal.open = False
                    self.page.update()
                    
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(self.t("backups_deleted")),
                            bgcolor=ft.colors.GREEN
                        )
                    )
                except Exception as e:
                    print(f"Erro ao deletar backups: {e}")
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(self.t("error_deleting_backups")),
                            bgcolor=ft.colors.RED
                        )
                    )
            
            # Diálogo de confirmação
            dlg_modal = ft.AlertDialog(
                modal=True,
                title=ft.Text(self.t("delete_backups")),
                content=ft.Column([
                    ft.Text(self.t("select_backups_delete")),
                    backup_list
                ]),
                actions=[
                    ft.TextButton(
                        self.t("cancel"),
                        on_click=lambda x: setattr(dlg_modal, 'open', False)
                    ),
                    ft.TextButton(
                        self.t("delete"),
                        on_click=confirmar_delecao,
                        style=ft.ButtonStyle(
                            color=ft.colors.RED
                        )
                    )
                ]
            )
            
            self.page.dialog = dlg_modal
            dlg_modal.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao listar backups: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(self.t("error_listing_backups")),
                    bgcolor=ft.colors.RED
                )
            )
