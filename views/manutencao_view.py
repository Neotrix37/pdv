import flet as ft
from datetime import datetime
from views.generic_header import create_header
from views.generic_table_style import apply_table_style

class ManutencaoView(ft.UserControl):
    def __init__(self, page: ft.Page, mensagem: str = None):
        super().__init__()
        self.page = page
        self.mensagem = mensagem or "Esta funcionalidade está em desenvolvimento e estará disponível em breve!"
        self.page.title = "Em Desenvolvimento"
        
        # Cabeçalho
        self.header = create_header(
            page=self.page,
            title="Manutenção",
            icon=ft.icons.CONSTRUCTION,
            subtitle="Funcionalidade em desenvolvimento"
        )
        
        # Mensagem de desenvolvimento
        self.mensagem_desenvolvimento = ft.Container(
            content=ft.Column([
                ft.Icon(
                    name=ft.icons.CONSTRUCTION,
                    size=80,
                    color=ft.colors.ORANGE_500
                ),
                ft.Text(
                    "Funcionalidade em Desenvolvimento",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.ORANGE_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    self.mensagem,
                    size=16, 
                    color=ft.colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                ft.Text(
                    "Informações Importantes:",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=10),
                ft.Text("• Esta funcionalidade está sendo implementada", size=14, color=ft.colors.GREY_600),
                ft.Text("• Estará disponível em breve", size=14, color=ft.colors.GREY_600),
                ft.Text("• Agradecemos a sua compreensão", size=14, color=ft.colors.GREY_600),
                ft.Container(height=20),
                ft.Container(height=30),
                ft.Text(
                    "Versão atual: 1.0.0",
                    size=12,
                    color=ft.colors.GREY_500,
                    italic=True
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            padding=ft.padding.all(40),
            margin=ft.margin.all(20)
        )
        
    def build(self):
        return ft.Column([
            self.header,
            self.mensagem_desenvolvimento
        ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    # Método voltar_inicio removido pois o header já possui botão de voltar
