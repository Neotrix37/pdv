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
                self.page.show_snack_bar(snack)
                self.page.update()
            except:
                print("Erro ao mostrar mensagem de erro")

    def fazer_backup(self, e):
        try:
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.db")
            
            # Copiar banco de dados
            shutil.copy2(self.db.db_path, backup_file)
            
            snack = ft.SnackBar(
                content=ft.Text(get_text("backup_success", self.idioma.value)),
                bgcolor=ft.colors.GREEN
            )
            self.page.show_snack_bar(snack)
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao fazer backup: {e}")
            snack = ft.SnackBar(
                content=ft.Text(get_text("backup_error", self.idioma.value)),
                bgcolor=ft.colors.RED
            )
            self.page.show_snack_bar(snack)
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
                        on_click=lambda x: self.confirmar_restauracao(self.selected_backup) if self.selected_backup else None
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
            self.page.show_snack_bar(snack)
            self.page.update()

    def confirmar_restauracao(self, backup_path):
        try:
            # Fazer backup do banco atual antes de restaurar
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_restore_backup = os.path.join(self.backup_dir, f"pre_restore_{timestamp}.db")
            shutil.copy2(self.db.db_path, pre_restore_backup)
            
            # Restaurar backup selecionado
            shutil.copy2(backup_path, self.db.db_path)
            
            self.fechar_dialogo(self.page.dialog)
            
            snack = ft.SnackBar(
                content=ft.Text(get_text("backup_restored", self.idioma.value)),
                bgcolor=ft.colors.GREEN
            )
            self.page.show_snack_bar(snack)
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao restaurar backup: {e}")
            snack = ft.SnackBar(
                content=ft.Text(get_text("restore_error", self.idioma.value)),
                bgcolor=ft.colors.RED
            )
            self.page.show_snack_bar(snack)
            self.page.update()

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
        try:
            # Primeiro fecha o diálogo
            self.fechar_dialogo(dlg)
            
            # Fecha a conexão atual
            if hasattr(self.db, 'conn') and self.db.conn:
                self.db.conn.close()
            
            # Caminho do arquivo do banco de dados
            db_path = self.db.db_path
            
            # Verifica se o arquivo existe e o deleta
            if os.path.exists(db_path):
                os.remove(db_path)
            
            # Força a reinicialização do singleton do Database
            Database._instance = None
            
            # Cria uma nova instância do Database (isso vai criar um novo banco e o usuário admin)
            self.db = Database()
            
            # Mostra mensagem de sucesso
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(
                        "Banco de dados resetado com sucesso! Um novo banco foi criado.",
                        color=ft.colors.WHITE
                    ),
                    bgcolor=ft.colors.GREEN,
                    duration=3000
                )
            )
            
            # Redireciona para a tela de login
            self.page.data.clear()
            self.page.go("/")
            
        except Exception as e:
            print(f"Erro ao resetar banco de dados: {e}")
            # Em caso de erro, tenta recriar a conexão
            self.db = Database()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(
                        "Erro ao resetar banco de dados!",
                        color=ft.colors.WHITE
                    ),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

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
                    )
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10
            )
        )

        # Se for admin, adiciona as outras configurações
        if self.usuario.get('is_admin'):
            # Configurações Gerais
            controls.extend([
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            self.t("general_settings"),
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLACK
                        ),
                        self.nome_empresa,
                        self.idioma,
                        ft.ElevatedButton(
                            text=self.t("save_settings"),
                            icon=ft.icons.SAVE,
                            bgcolor=ft.colors.GREEN,
                            color=ft.colors.WHITE,
                            on_click=self.salvar_configuracoes
                        )
                    ]),
                    bgcolor=ft.colors.WHITE,
                    padding=20,
                    border_radius=10
                ),

                # Backup e Restauração
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            self.t("backup_restore"),
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLACK
                        ),
                        ft.Row([
                            ft.ElevatedButton(
                                text=self.t("make_backup"),
                                icon=ft.icons.BACKUP,
                                bgcolor=ft.colors.BLUE,
                                color=ft.colors.WHITE,
                                on_click=self.fazer_backup
                            ),
                            ft.ElevatedButton(
                                text=self.t("restore_backup"),
                                icon=ft.icons.RESTORE,
                                bgcolor=ft.colors.ORANGE,
                                color=ft.colors.WHITE,
                                on_click=self.restaurar_backup
                            ),
                            ft.ElevatedButton(
                                text=self.t("delete_backups"),
                                icon=ft.icons.DELETE_FOREVER,
                                bgcolor=ft.colors.RED,
                                color=ft.colors.WHITE,
                                on_click=self.deletar_backups
                            )
                        ])
                    ]),
                    bgcolor=ft.colors.WHITE,
                    padding=20,
                    border_radius=10
                ),

                # Reset do Sistema
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            self.t("system_reset"),
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.RED
                        ),
                        ft.ElevatedButton(
                            text=self.t("reset_database"),
                            icon=ft.icons.WARNING_ROUNDED,
                            bgcolor=ft.colors.RED_900,
                            color=ft.colors.WHITE,
                            on_click=self.confirmar_reset_banco
                        )
                    ]),
                    bgcolor=ft.colors.WHITE,
                    padding=20,
                    border_radius=10
                )
            ])

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
