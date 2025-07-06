import flet as ft
from database.database import Database
from werkzeug.security import check_password_hash
from utils.translation_mixin import TranslationMixin

class LoginView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = Database()
        self.tentativas = 0
        
        # Remover a configuração de largura da janela
        # self.page.window_width = 1000  <- remover esta linha
        self.page.window_min_width = 400
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.bgcolor = ft.colors.BLUE_GREY_50
        self.page.padding = 0
        
        # Campos do formulário
        self.username = ft.TextField(
            label=self.t("username"),
            width=300,
            height=50,
            prefix_icon=ft.icons.PERSON,
            border_color=ft.colors.BLUE_900,
            focused_border_color=ft.colors.BLUE_900,
            focused_color=ft.colors.BLUE_900,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        self.password = ft.TextField(
            label=self.t("password"),
            password=True,
            can_reveal_password=True,
            width=300,
            height=50,
            prefix_icon=ft.icons.LOCK,
            border_color=ft.colors.BLUE_900,
            focused_border_color=ft.colors.BLUE_900,
            focused_color=ft.colors.BLUE_900,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Mensagem de erro
        self.error_text = ft.Text(
            color=ft.colors.RED,
            size=12,
            visible=False
        )
        
        # Registrar callback para redimensionamento
        self.page.on_resize = self.handle_resize

    def handle_resize(self, e):
        """Ajusta o layout baseado no tamanho da tela"""
        if not self.page:
            return
            
        try:
            if self.page.window_width < 1000:
                scale = self.page.window_width / 1000
                self.page.window_width = 1000
                self.page.window_scale = scale
            else:
                self.page.window_scale = 1
            self.page.update()
        except Exception as err:
            print(f"Erro ao redimensionar: {str(err)}")

    def fazer_login(self, e):
        try:
            # Adicionar validação de formato de email/usuário
            if not self.is_valid_username(self.username.value):
                self.error_text.value = self.t("Porfavor, preencha todos os campos")
                self.error_text.visible = True
                self.update()
                return
            
            # Adicionar tempo de bloqueio progressivo
            if self.tentativas >= 3:
                tempo_espera = 2 ** (self.tentativas - 2)  # 2, 4, 8, 16... minutos
                self.error_text.value = self.t("Demasiadas tentativas sem sucesso. Reinicie o sistema").format(tempo_espera)
                self.error_text.visible = True
                self.username.disabled = True
                self.password.disabled = True
                self.update()
                return
            
            usuario = self.db.fetchone(
                """SELECT id, nome, usuario, senha, is_admin, ativo 
                   FROM usuarios 
                   WHERE usuario = ? AND ativo = 1""",
                (self.username.value,),
                dictionary=True
            )
            
            if usuario and check_password_hash(usuario['senha'], self.password.value):
                self.page.data = {
                    'id': usuario['id'],
                    'nome': usuario['nome'],
                    'usuario': usuario['usuario'],
                    'is_admin': bool(usuario['is_admin'])
                }
                self.page.go("/dashboard")
            else:
                self.tentativas += 1
                self.error_text.value = self.t("invalid_credentials")
                self.error_text.visible = True
                self.update()
                
        except Exception as err:
            print(f"Erro no login: {str(err)}")
            self.error_text.value = self.t("login_error")
            self.error_text.visible = True
            self.update()

    def is_valid_username(self, username):
        # Implementar validação de formato
        return bool(username and len(username) >= 3)

    def build(self):
        return ft.Container(
            expand=True,  # Faz o container ocupar todo o espaço disponível
            alignment=ft.alignment.center,  # Alinhamento central
            margin=ft.margin.only(top=200),  # Adiciona margem superior
            content=ft.Container(
                width=1000,  # Container interno com largura fixa
                height=600,
                content=ft.Row(
                    [
                        # Metade Esquerda
                        ft.Container(
                            width=500,  # Metade da largura
                            height=600,
                            content=ft.Column(
                                [
                                    ft.Icon(
                                        name=ft.icons.SHOPPING_CART,
                                        size=80,
                                        color=ft.colors.WHITE
                                    ),
                                    ft.Text(
                                        "Sistema de Gestão",
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.WHITE
                                    ),
                                    ft.Text(
                                        "Sua solução completa para gestão comercial",
                                        size=16,
                                        color=ft.colors.WHITE,
                                        opacity=0.8,
                                        text_align=ft.TextAlign.CENTER
                                    ),

                                    ft.Text(
                                        "Neotrix",
                                        size=21,
                                        color=ft.colors.WHITE,
                                        opacity=1.8,
                                        text_align=ft.TextAlign.CENTER,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                    "Tecnologias ão seu alcance",
                                        size=14,
                                        color=ft.colors.WHITE,
                                        opacity=0.9,
                                        text_align=ft.TextAlign.CENTER,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=20
                            ),
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_center,
                                end=ft.alignment.bottom_center,
                                colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
                            ),
                        ),
                        
                        # Metade Direita
                        ft.Container(
                            width=500,  # Metade da largura
                            height=600,
                            bgcolor=ft.colors.WHITE,
                            padding=50,
                            content=ft.Column(
                                [
                                    ft.Text(
                                        self.t("welcome"),
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.BLUE_900
                                    ),
                                    ft.Text(
                                        self.t("login_message"),
                                        size=16,
                                        color=ft.colors.GREY_700,
                                        text_align=ft.TextAlign.CENTER
                                    ),
                                    ft.Container(height=40),
                                    self.error_text,
                                    self.username,
                                    ft.Container(height=20),
                                    self.password,
                                    ft.Container(height=40),
                                    ft.ElevatedButton(
                                        content=ft.Row(
                                            [
                                                ft.Icon(ft.icons.LOGIN, color=ft.colors.WHITE),
                                                ft.Text(
                                                    self.t("enter"),
                                                    size=16,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=ft.colors.WHITE
                                                )
                                            ],
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=10
                                        ),
                                        width=300,
                                        height=50,
                                        style=ft.ButtonStyle(
                                            color=ft.colors.WHITE,
                                            bgcolor=ft.colors.BLUE_900,
                                            shape=ft.RoundedRectangleBorder(radius=8)
                                        ),
                                        on_click=self.fazer_login
                                    ),
                                    ft.Container(
                                        height=40,
                                        expand=True  # Empurra o copyright para baixo
                                    ),
                                    ft.Text(
                                        "© 2024 Sistema de Gestão. Vuchada",
                                        size=12,
                                        color=ft.colors.GREY_700,
                                        text_align=ft.TextAlign.CENTER
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                alignment=ft.MainAxisAlignment.START,
                                spacing=10
                            )
                        )
                    ],
                    spacing=0
                ),
                border_radius=10,
                bgcolor=ft.colors.WHITE,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.colors.with_opacity(0.2, ft.colors.BLACK),
                    offset=ft.Offset(0, 0)
                )
            )
        )

    def did_mount(self):
        self.handle_resize(None)  # Ajusta o layout inicial
