import flet as ft

class SobreView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario

    def build(self):
        # Header simples
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    icon_color=ft.colors.WHITE,
                    on_click=lambda e: self.page.go("/dashboard"),
                    tooltip="Voltar para Dashboard"
                ),
                ft.Icon(ft.icons.INFO_OUTLINE, size=30, color=ft.colors.WHITE),
                ft.Column([
                    ft.Text("Sobre o Sistema", size=20, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                    ft.Text("Informações do PDV e Neotrix Tecnologias", size=14, color=ft.colors.WHITE)
                ])
            ], spacing=10),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_900, ft.colors.PURPLE_900]
            ),
            padding=20,
            border_radius=10
        )
        
        # Cards seguindo o padrão do dashboard - Tamanho reduzido
        card_sistema = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Sistema PDV",
                    size=16,
                    color=ft.colors.WHITE,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "Sistema de Gestão Comercial",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(height=8),
                ft.Text(
                    "• Gestão de produtos e estoque", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• Sistema de vendas integrado", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• Controle financeiro", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• Relatórios detalhados", 
                    size=12, 
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_700, ft.colors.BLUE_900]
            ),
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            width=300,
            height=250,
            col={"sm": 12, "md": 6}
        )
        
        card_tecnologias = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Tecnologias",
                    size=16,
                    color=ft.colors.WHITE,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "Stack Tecnológico",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(height=8),
                ft.Text(
                    "• Python 3.12+", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• Flet Framework 0.9.0", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• SQLite Database", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• PyInstaller", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "📋 Versão: 1.0.0", 
                    size=12, 
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.PURPLE_700, ft.colors.PURPLE_900]
            ),
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            width=300,
            height=250,
            col={"sm": 12, "md": 6}
        )
        
        card_empresa = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Neotrix Tecnologias",
                    size=16,
                    color=ft.colors.WHITE,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "Tecnologia ao seu alcance",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE,
                    italic=True
                ),
                ft.Container(height=8),
                ft.Text(
                    "📧 neotrixtecnologias37@gmail.com", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "📱 +258 872 664 074", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "🌍 Moçambique", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "👨‍💼 Helder Alves Fonseca", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "CEO & Desenvolvedor", 
                    size=12, 
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.GREEN_700, ft.colors.GREEN_900]
            ),
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            width=300,
            height=270,
            col={"sm": 12, "md": 6}
        )
        
        card_missao = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Missão & Valores",
                    size=16,
                    color=ft.colors.WHITE,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "Nossa Missão",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(height=8),
                ft.Text(
                    "Desenvolver soluções tecnológicas inovadoras", 
                    size=12, 
                    color=ft.colors.WHITE,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "💎 Nossos Valores:", 
                    size=12, 
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• Inovação constante", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• Qualidade superior", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• Suporte ao cliente", 
                    size=12, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "• Transparência", 
                    size=12, 
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.ORANGE_700, ft.colors.ORANGE_900]
            ),
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            width=300,
            height=270,
            col={"sm": 12, "md": 6}
        )
        
        # Primeira fila: Sistema PDV e Tecnologias
        primeira_fila = ft.ResponsiveRow([
            card_sistema,
            card_tecnologias
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        # Segunda fila: Empresa e Missão & Valores
        segunda_fila = ft.ResponsiveRow([
            card_empresa,
            card_missao
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=20),
                primeira_fila,
                ft.Container(height=20),
                segunda_fila
            ], scroll=ft.ScrollMode.AUTO, expand=True),
            padding=20
        )