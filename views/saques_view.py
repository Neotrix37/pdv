import flet as ft
from datetime import datetime, date
import locale
import asyncio
import threading
import time
import traceback
from database.database import Database
from views.generic_header import create_header
from views.generic_table_style import apply_table_style

class SaquesView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.usuario = usuario
        
        # Cabeçalho
        self.header = create_header(
            page=self.page,
            title="Sistema de Saques",
            icon=ft.icons.ACCOUNT_BALANCE_WALLET,
            subtitle="Funcionalidade em desenvolvimento"
        )
        
        # Mensagem de desenvolvimento
        self.mensagem_desenvolvimento = ft.Container(
            content=ft.Column([
                ft.Icon(
                    name=ft.icons.BUILD_CIRCLE,
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
                    "O sistema de saques está sendo desenvolvido e será disponibilizado em breve.",
                                             size=16, 
                    color=ft.colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                ft.Text(
                    "Funcionalidades planejadas:",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=10),
                ft.Text("• Registro de saques de vendas e lucros", size=14, color=ft.colors.GREY_600),
                ft.Text("• Controle de saldo disponível", size=14, color=ft.colors.GREY_600),
                ft.Text("• Histórico de transações", size=14, color=ft.colors.GREY_600),
                ft.Text("• Relatórios financeiros", size=14, color=ft.colors.GREY_600),
                ft.Text("• Aprovação de saques", size=14, color=ft.colors.GREY_600),
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
