import flet as ft
from database.database import Database
from werkzeug.security import check_password_hash
from utils.translation_mixin import TranslationMixin

def LoginView(page: ft.Page, on_login_success):
    # Configuração da página
    page.bgcolor = ft.colors.WHITE
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Cores do tema
    primary_color = ft.colors.BLUE_900
    
    # Campos do formulário
    username = ft.TextField(
        label="Usuário",
        prefix_icon=ft.icons.PERSON,
        autofocus=True,
        width=300,
        border_radius=8,
        border_color="#d1d5db",
        height=48,
        text_size=14
    )
    
    password = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.icons.LOCK,
        width=300,
        border_radius=8,
        border_color="#d1d5db",
        height=48,
        text_size=14,
        on_submit=lambda e: do_login(e)
    )
    
    error_text = ft.Text("", color=ft.colors.RED, size=12)
    
    def do_login(e):
        # Remover espaços acidentais
        user_inp = (username.value or "").strip()
        pass_inp = (password.value or "").strip()

        if not user_inp or not pass_inp:
            error_text.value = "Por favor, preencha todos os campos"
            page.update()
            return
            
        # Autenticar usuário
        db = Database()
        user = db.verificar_login(user_inp, pass_inp)
        
        if user:
            error_text.value = ""
            on_login_success(user)
        else:
            error_text.value = "Usuário ou senha inválidos!"
        page.update()
    
    # Card de login
    login_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Bem-vindo(a)", size=28, weight=ft.FontWeight.BOLD, color=primary_color),
                ft.Text("Faça login para acessar o sistema", size=14, color=ft.colors.GREY_700),
                username,
                password,
                ft.ElevatedButton(
                    "Entrar",
                    icon=ft.icons.LOGIN,
                    style=ft.ButtonStyle(
                        bgcolor=primary_color,
                        color=ft.colors.WHITE,
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    on_click=do_login,
                    width=300,
                    height=48
                ),
                error_text
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            width=400,
            height=400
        ),
        padding=40,
        bgcolor=ft.colors.WHITE,
        border_radius=ft.border_radius.only(top_right=16, bottom_right=16),
        width=400,
        height=400
    )
    
    # Card lateral esquerdo
    left_card = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.SHOPPING_CART, size=64, color=ft.colors.WHITE),
            ft.Text("Sistema de Gestão", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Text("Sua solução completa para gestão comercial", size=14, color=ft.colors.WHITE70),
            ft.Container(height=40),  # Espaçamento
            ft.Text("Neotrix", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Text("Tecnologias ao seu alcance", size=12, color=ft.colors.WHITE70, italic=True),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10),
        bgcolor=primary_color,
        padding=40,
        width=400,
        height=400,
        border_radius=ft.border_radius.only(top_left=16, bottom_left=16)
    )
    
    # Criar o container principal que contém ambos os cards
    main_container = ft.Container(
        content=ft.Row(
            [
                left_card,
                login_card
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER
        ),
        bgcolor=ft.colors.WHITE,
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
            offset=ft.Offset(0, 4)
        )
    )
    
    # Layout principal - centraliza tudo na tela
    return ft.Container(
        content=main_container,
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=ft.colors.TRANSPARENT,
        padding=ft.padding.all(20)
    )

    # Código abaixo removido por estar inatingível após o return acima e conter referências inválidas
