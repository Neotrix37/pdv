import flet as ft
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.pdv_view import PDVView
from views.produtos_view import ProdutosView
from views.relatorios_view import RelatoriosView
from views.usuarios_view import UsuariosView
from views.minhas_vendas_view import MinhasVendasView
from views.todas_vendas_view import TodasVendasView
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
from views.abastecimento_view import AbastecimentoView
from views.sobre_view import SobreView
from database.database import Database
import os
import json
import platform
import traceback
import sys
import shutil
from pathlib import Path

def resource_path(relative_path: str) -> str:
    """Resolve path for PyInstaller (sys._MEIPASS) or source tree."""
    try:
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path:
            return os.path.join(base_path, relative_path)
        return os.path.join(os.path.dirname(__file__), relative_path)
    except Exception:
        return os.path.join(os.path.dirname(__file__), relative_path)


def main(page: ft.Page):
    # Configurações globais
    page.bgcolor = ft.colors.WHITE
    
    # Detectar se está rodando no navegador
    try:
        is_web = str(page.platform) in ["ios", "android"] or os.getenv('WEB_MODE') == 'true'
    except:
        is_web = os.getenv('WEB_MODE') == 'true'
    
    # Configurações de janela (apenas para desktop)
    if not is_web:
        page.window_full_screen = True  # Força tela cheia
        page.window_resizable = False   # Desabilita redimensionamento
        page.window_maximizable = False # Desabilita o botão de maximizar
        # Definir ícone da janela a partir dos assets empacotados, se existir
        try:
            icon_path = resource_path(os.path.join('assets', 'icon.ico'))
            if os.path.exists(icon_path):
                page.window_icon = icon_path
        except Exception:
            pass
    
    # Configurações de dados do aplicativo
    if is_web:
        # No navegador, usamos storage local
        app_data = "app_data"
        if not os.path.exists(app_data):
            os.makedirs(app_data, exist_ok=True)
    else:
        # No desktop, usamos diretórios do sistema
        sistema = platform.system().lower()
        if sistema == "windows":
            app_data = os.path.join(os.environ['APPDATA'], 'SistemaGestao')
        else:
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
    # Quando empacotado, a pasta assets embutida pode ser usada diretamente
    if getattr(sys, 'frozen', False):
        bundled_assets = resource_path('assets')
        if os.path.exists(bundled_assets):
            page.assets_dir = bundled_assets
        else:
            page.assets_dir = os.path.join(app_data, "assets")
    else:
        page.assets_dir = os.path.join(app_data, "assets")
    page.upload_dir = os.path.join(app_data, "uploads")

    # Garantir que o banco inicial exista em app_data/database/sistema.db
    try:
        target_db_dir = os.path.join(app_data, "database")
        target_db_path = os.path.join(target_db_dir, "sistema.db")
        bundled_db_path = resource_path(os.path.join('database', 'sistema.db'))
        if not os.path.exists(target_db_path) and os.path.exists(bundled_db_path):
            shutil.copy2(bundled_db_path, target_db_path)
    except Exception as _e:
        # Apenas registra no console, não interrompe a execução
        print(f"[STARTUP] Aviso: não foi possível copiar banco inicial: {_e}")
    
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
    
    def on_login_success(user):
        # Armazenar dados do usuário na sessão e em page.data
        try:
            page.session.set("usuario", user)
        except Exception:
            pass
        page.data = user
        # Redirecionar para o dashboard
        page.go("/dashboard")
    
    def route_change(route):
        page.views.clear()
        # Restaurar usuário da sessão se page.data estiver vazio (especialmente no modo web)
        try:
            if (not page.data) and page.session.contains_key("usuario"):
                sess_user = page.session.get("usuario")
                if sess_user:
                    page.data = sess_user
        except Exception:
            pass
        
        if page.route in ["/", "/login"]:
            # Para rota de login, limpar estado da página
            if page.route == "/login":
                page.data = {}
            
            # Limpar todas as views existentes
            page.views.clear()
            
            # Forçar atualização da página antes de adicionar nova view
            page.update()
            
            # Criar nova view de login
            try:
                login_view = LoginView(page, on_login_success)
                page.views.append(
                    ft.View(
                        route=page.route,
                        controls=[login_view],
                        padding=0,
                        bgcolor=ft.colors.WHITE
                    )
                )
                # Forçar atualização após adicionar a view
                page.update()
            except Exception as e:
                print(f"Erro ao criar view de login: {e}")
                # Fallback: tentar novamente após um pequeno delay
                import time
                time.sleep(0.1)
                try:
                    login_view = LoginView(page, on_login_success)
                    page.views.append(
                        ft.View(
                            route=page.route,
                            controls=[login_view],
                            padding=0,
                            bgcolor=ft.colors.WHITE
                        )
                    )
                    page.update()
                except Exception as e2:
                    print(f"Erro crítico ao criar view de login: {e2}")
        elif page.route == "/dashboard":
            if not page.data:
                page.go("/")
                return
                
            print("Acessando rota /dashboard")  # Log de depuração
            
            # Verificar se já existe uma view de dashboard
            existing_view = next((v for v in page.views if v.route == "/dashboard"), None)
            
            if existing_view:
                page.views.remove(existing_view)
            
            try:
                print("Criando nova view de dashboard...")  # Log de depuração
                dashboard_view = DashboardView(page, page.data) 
                print("View de dashboard criada com sucesso")  # Log de depuração
                
                # Armazenar referência ao dashboard_view na página
                page.dashboard_view = dashboard_view
                print("Referência ao dashboard_view armazenada na página")
                
                # Verificar se a view tem o método build
                if not hasattr(dashboard_view, 'build') or not callable(dashboard_view.build):
                    raise Exception("A view de dashboard não possui um método build válido")
                
                page.views.append(
                    ft.View(
                        route="/dashboard",
                        controls=[dashboard_view],
                        padding=0,
                        spacing=0,
                    )
                )
                page.update()
                
            except Exception as e:
                error_msg = f"Erro ao carregar o dashboard: {str(e)}\n\n{traceback.format_exc()}"
                print(error_msg)  # Log detalhado no console
                
                # Exibir mensagem de erro na interface
                page.views.append(
                    ft.View(
                        route="/dashboard",
                        controls=[
                            ft.AppBar(title=ft.Text("Erro"), bgcolor=ft.colors.RED_700),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Erro ao carregar o dashboard", size=20, color=ft.colors.RED),
                                        ft.Text(str(e), selectable=True),
                                        ft.ElevatedButton(
                                            "Voltar",
                                            on_click=lambda _: page.go("/"),
                                            icon=ft.icons.ARROW_BACK
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    expand=True
                                ),
                                padding=20,
                                expand=True
                            )
                        ],
                        padding=0,
                        spacing=0,
                    )
                )
                page.update()
                return
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
            print("Acessando rota /minhas-vendas")
            page.views.append(
                ft.View(
                    route="/minhas-vendas",
                    controls=[MinhasVendasView(page, page.data)],
                    bgcolor=ft.colors.WHITE
                )
            )
        elif page.route == "/todas-vendas":
            print("Acessando rota /todas-vendas")
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
                    spacing=0,
                )
            )
            page.update()
            return
        elif page.route == "/pdv":
            page.views.append(
                ft.View(
                    route="/pdv",
                    controls=[PDVView(page, page.data)],
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
                        padding=0,
                        bgcolor=ft.colors.WHITE
                    )
                )
        
            
        # Rota para abastecimento (mínima)
        elif page.route == "/abastecimento":
            # Debug: verificar permissões do usuário
            print(f"[ABASTECIMENTO] Usuário: {page.data.get('usuario', 'N/A')}")
            print(f"[ABASTECIMENTO] is_admin: {page.data.get('is_admin', False)}")
            print(f"[ABASTECIMENTO] pode_abastecer: {page.data.get('pode_abastecer', False)}")
            print(f"[ABASTECIMENTO] page.data completo: {page.data}")
            
            # Verificar se é admin OU tem permissão de abastecimento
            if not page.data.get('is_admin') and not page.data.get('pode_abastecer'):
                print("[ABASTECIMENTO] Acesso negado - redirecionando para dashboard")
                page.go("/dashboard")
                return
            page.views.append(
                ft.View(
                    route="/abastecimento",
                    controls=[AbastecimentoView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        
        elif page.route == "/despesas":
            # Debug: verificar permissões do usuário
            print(f"[DESPESAS] Usuário: {page.data.get('usuario', 'N/A')}")
            print(f"[DESPESAS] is_admin: {page.data.get('is_admin', False)}")
            print(f"[DESPESAS] pode_gerenciar_despesas: {page.data.get('pode_gerenciar_despesas', False)}")
            print(f"[DESPESAS] page.data completo: {page.data}")
            
            # Verificar se é admin OU tem permissão de gerenciar despesas
            if not page.data.get('is_admin') and not page.data.get('pode_gerenciar_despesas'):
                print("[DESPESAS] Acesso negado - redirecionando para dashboard")
                page.go("/dashboard")
                return
            page.views.append(
                ft.View(
                    route="/despesas",
                    controls=[DespesasView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )
        
        elif page.route == "/relatorio-financeiro":
            if not page.data.get('is_admin'):
                page.go("/dashboard")
                return
            page.views.append(
                ft.View(
                    route="/relatorio-financeiro",
                    controls=[RelatorioFinanceiroView(page, page.data)],
                    padding=0,
                    bgcolor=ft.colors.WHITE
                )
            )

        
        # Rota para página Sobre
        elif page.route == "/sobre":
            page.views.append(
                ft.View(
                    route="/sobre",
                    controls=[SobreView(page, page.data)],
                    bgcolor=ft.colors.WHITE
                )
            )
                
        page.update()
    
    def view_pop(view):
        try:
            page.views.pop()
            # Verificar se ainda há views na lista antes de acessar
            if len(page.views) > 0:
                top_view = page.views[-1]
                page.go(top_view.route)
            else:
                # Se não há views, ir para a rota padrão
                page.go("/login")
        except Exception as e:
            print(f"Erro em view_pop: {e}")
            page.go("/dashboard")
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.go(page.route)

if __name__ == "__main__":
    # Verificar se foi solicitado modo desktop
    desktop_mode = "--desktop" in sys.argv
    
    # Configurações do aplicativo
    app_settings = {
        "target": main,
        "assets_dir": "assets",
        "upload_dir": "uploads",
        "web_renderer": "auto"
    }
    
    # Forçar modo desktop para executável
    app_settings["view"] = ft.FLET_APP_HIDDEN
    
    # Iniciar o aplicativo
    ft.app(**app_settings)
