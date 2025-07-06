import flet as ft
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.pdv_view import PDVView
from views.produtos_view import ProdutosView
from views.relatorios_view import RelatoriosView
from views.usuarios_view import UsuariosView
from views.minhas_vendas_view import MinhasVendasView
from views.todas_vendas_view import TodasVendasView
from database.database import Database
from views.configuracoes_view import ConfiguracoesView
from views.printer_config_view import PrinterConfigView
from views.relatorio_financeiro_view import RelatorioFinanceiroView
from views.despesas_view import DespesasView
from views.busca_vendas_view import BuscaVendasView
from views.clientes_view import ClientesView
from views.dividas_view import DividasView
from views.gerenciar_vendas_view import GerenciarVendasView
from views.congelador_view import CongeladorView
from views.congelador_vendas_view import CongeladorVendasView
from views.graficos_view import GraficosView
import os
import json
import platform

def main(page: ft.Page):
    # Configurações globais
    page.bgcolor = ft.colors.WHITE
    
    # Detectar sistema operacional
    sistema = platform.system().lower()
    
    # Configurações específicas por sistema operacional
    if sistema == "windows":
        page.window_maximized = True
        page.window_width = 1920
        page.window_height = 1080
        page.window_resizable = True
        page.window_maximizable = True
        app_data = os.path.join(os.environ['APPDATA'], 'SistemaGestao')
    else:
        page.window_width = 1366
        page.window_height = 768
        page.window_maximized = True
        page.window_resizable = True
        app_data = os.path.join(os.path.expanduser('~'), '.sistemagestao')
    
    # Configurações comuns
    page.title = "Sistema de Gestão"
    page.padding = 0
    page.spacing = 0
    
    # Criar diretórios necessários
    os.makedirs(app_data, exist_ok=True)
    os.makedirs(os.path.join(app_data, "assets"), exist_ok=True)
    os.makedirs(os.path.join(app_data, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(app_data, "database"), exist_ok=True)
    
    # Definir caminhos de assets e uploads
    page.assets_dir = os.path.join(app_data, "assets")
    page.upload_dir = os.path.join(app_data, "uploads")
    
    # Inicializar banco de dados
    db = Database()
    
    # Inicializar page.data como dicionário vazio
    page.data = {}
    
    # Carregar configurações
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                page.data["language"] = config.get('idioma', 'pt')
        except Exception:
            page.data["language"] = 'pt'
    else:
        page.data["language"] = 'pt'
    
    def login_success(usuario):
        page.session.set("usuario", usuario)
        page.go("/dashboard")
    
    def route_change(route):
        page.views.clear()
        
        if page.route == "/":
            page.views.append(
                ft.View(
                    route="/",
                    controls=[LoginView(page)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/dashboard":
            if not page.data:
                page.go("/")
                return
                
            page.views.append(
                ft.View(
                    route="/dashboard",
                    controls=[DashboardView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/pdv":
            page.views.append(
                ft.View(
                    route="/pdv",
                    controls=[PDVView(page, page.data)],
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/produtos":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
            else:
                page.views.append(
                    ft.View(
                        route="/produtos",
                        controls=[ProdutosView(page, page.data)],
                        bgcolor=ft.colors.WHITE
                    )
                )
        elif page.route == "/usuarios":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
            else:
                page.views.append(
                    ft.View(
                        route="/usuarios",
                        controls=[UsuariosView(page, page.data)],
                        bgcolor=ft.colors.WHITE
                    )
                )
        elif page.route == "/relatorios":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
            else:
                page.views.append(
                    ft.View(
                        route="/relatorios",
                        controls=[RelatoriosView(page, page.data)],
                        bgcolor=ft.colors.WHITE
                    )
                )
        elif page.route == "/minhas-vendas":
            page.views.append(
                ft.View(
                    route="/minhas-vendas",
                    controls=[MinhasVendasView(page, page.data)],
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/todas-vendas":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
            else:
                page.views.append(
                    ft.View(
                        route="/todas-vendas",
                        controls=[TodasVendasView(page, page.data)],
                        bgcolor=ft.colors.WHITE
                    )
                )
        elif page.route == "/configuracoes":
            page.views.append(
                ft.View(
                    route="/configuracoes",
                    controls=[ConfiguracoesView(page, page.data)],
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/printer":
            page.views.append(
                ft.View(
                    "/printer",
                    [PrinterConfigView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/despesas":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
            else:
                page.views.append(
                    ft.View(
                        route="/despesas",
                        controls=[DespesasView(page, page.data)],
                        bgcolor=ft.colors.WHITE
                    )
                )
        elif page.route == "/relatorio-financeiro":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
            else:
                page.views.append(
                    ft.View(
                        route="/relatorio-financeiro",
                        controls=[RelatorioFinanceiroView(page, page.data)],
                        bgcolor=ft.colors.WHITE
                    )
                )
        elif page.route == "/busca-vendas":
            page.views.append(
                ft.View(
                    route="/busca-vendas",
                    controls=[BuscaVendasView(page, page.data)],
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/clientes":
            if not page.data:
                page.go("/")
                return
            
            if not page.data.get('is_admin'):
                page.go("/dashboard")
                return
            
            page.views.append(
                ft.View(
                    route="/clientes",
                    controls=[ClientesView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/dividas":
            if not page.data:
                page.go("/")
                return
            
            page.views.append(
                ft.View(
                    route="/dividas",
                    controls=[DividasView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/gerenciar-vendas":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
            else:
                page.views.append(
                    ft.View(
                        route="/gerenciar-vendas",
                        controls=[GerenciarVendasView(page, page.data)],
                        bgcolor=ft.colors.WHITE
                    )
                )
        elif page.route == "/congelador":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
                return
            
            page.views.append(
                ft.View(
                    route="/congelador",
                    controls=[CongeladorView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        
        # Adicionar nova rota para vendas do congelador
        elif page.route == "/congelador-vendas":
            page.views.append(
                ft.View(
                    route="/congelador-vendas",
                    controls=[CongeladorVendasView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        
        # Nova rota para gráficos
        elif page.route == "/graficos":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
            else:
                page.views.append(
                    ft.View(
                        route="/graficos",
                        controls=[GraficosView(page, page.data)],
                        bgcolor=ft.colors.WHITE
                    )
                )
        
        page.update()
    
    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.go(page.route)

if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir="assets",
        upload_dir="uploads",
        web_renderer="auto"
    )
