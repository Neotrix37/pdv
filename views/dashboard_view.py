import asyncio
import flet as ft
from datetime import datetime
from database.database import Database
from utils.translations import get_text
from utils.translation_mixin import TranslationMixin
from repositories.sync_manager import SyncManager
from utils.status_indicator import StatusIndicator
import asyncio
from typing import List, Dict, Any, Optional
import os
import httpx

class DashboardView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.BLUE_50
        self.usuario = usuario
        self.db = Database()
        self.lang = page.data.get("language", "pt")
        
        # Inicializar indicador de status de conexão
        self.status_indicator = StatusIndicator()
        
        # Inicializar os textos dos valores com valores reais
        # Usar os novos métodos que consideram os saques
        total_vendas_mes = self.db.get_vendas_disponiveis_mes()  # Vendas menos saques
        total_vendas_dia = self.db.get_total_vendas_hoje()
        total_vendas_congelador = self.db.get_total_vendas_congelador_hoje()
        valor_estoque = self.db.get_valor_estoque()
        valor_potencial = self.db.get_valor_venda_estoque()
        lucro_mes = 0.0  # Inicializa com valor padrão
        lucro_dia = 0.0  # Inicializa com valor padrão
        
        # Obter valores específicos para administradores
        if self._flag_true(self.usuario.get('is_admin')):
            lucro_mes = self.db.get_lucro_disponivel_mes()  # Lucro menos saques
            lucro_dia = self.db.get_lucro_dia()
        
        self.vendas_mes = ft.Text(
            value=f"MT {total_vendas_mes:.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.lucro_mes = ft.Text(
            value=f"MT {lucro_mes:.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.vendas_dia = ft.Text(
            value=f"MT {total_vendas_dia:.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.vendas_congelador = ft.Text(
            value=f"MT {total_vendas_congelador:.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        # Adicionar novos textos para valor do estoque e valor potencial
        self.valor_estoque = ft.Text(
            value=f"MT {valor_estoque:.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.valor_potencial = ft.Text(
            value=f"MT {valor_potencial:.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        # Adicionar atributo para o lucro diário
        self.lucro_dia = ft.Text(
            value=f"MT {lucro_dia:.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        # Adicionar atributo para o lucro potencial do estoque
        self.lucro_potencial = ft.Text(
            value=f"MT {self.db.get_lucro_potencial_estoque():.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        print(f"Build - Vendas mês: MT {total_vendas_mes:.2f}")
        print(f"Build - Lucro mês: MT {lucro_mes:.2f}")
        
        # Forçar atualização dos Text objects apenas se estiverem na página
        try:
            if hasattr(self, 'vendas_mes') and hasattr(self.vendas_mes, 'page') and self.vendas_mes.page:
                self.vendas_mes.update()
            if hasattr(self, 'lucro_mes') and hasattr(self.lucro_mes, 'page') and self.lucro_mes.page and self._flag_true(self.usuario.get('is_admin')):
                self.lucro_mes.update()
            if hasattr(self, 'vendas_dia') and hasattr(self.vendas_dia, 'page') and self.vendas_dia.page:
                self.vendas_dia.update()
            if hasattr(self, 'vendas_congelador') and hasattr(self.vendas_congelador, 'page') and self.vendas_congelador.page:
                self.vendas_congelador.update()
            if hasattr(self, 'valor_estoque') and hasattr(self.valor_estoque, 'page') and self.valor_estoque.page:
                self.valor_estoque.update()
            if hasattr(self, 'valor_potencial') and hasattr(self.valor_potencial, 'page') and self.valor_potencial.page:
                self.valor_potencial.update()
            if hasattr(self, 'lucro_dia') and hasattr(self.lucro_dia, 'page') and self.lucro_dia.page:
                self.lucro_dia.update()
            if hasattr(self, 'lucro_potencial') and hasattr(self.lucro_potencial, 'page') and self.lucro_potencial.page:
                self.lucro_potencial.update()
        except Exception as e:
            print(f"Erro ao atualizar componentes do dashboard: {e}")
            print(f"Erro ao atualizar valores no build: {e}")

        # Card de Lucro Potencial
        card_lucro_potencial = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Lucro Potencial do Estoque",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    self.lucro_potencial
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=200,
            height=100,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            padding=15,
            alignment=ft.alignment.center,
            tooltip="Valor estimado de lucro se todo o estoque for vendido"
        )

        # Criar os cards
        card_vendas_mes = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Vendas do Mês",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    self.vendas_mes
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=200,
            height=100,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            padding=15,
            alignment=ft.alignment.center
        )

        card_lucro_mes = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Lucro do Mês",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    self.lucro_mes
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=200,
            height=100,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            padding=15,
            alignment=ft.alignment.center
        )

        card_vendas_dia = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Vendas de Hoje",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    self.vendas_dia
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=200,
            height=100,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            padding=15,
            alignment=ft.alignment.center
        )

        card_vendas_congelador = ft.Container(
            alignment=ft.alignment.center
        )

        # Criar card para valor do estoque
        card_valor_estoque = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Valor Total em Estoque",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    ),
                    self.valor_estoque
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=200,
            height=100,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_700, ft.colors.BLUE_900]
            ),
            border_radius=10,
            padding=15,
            alignment=ft.alignment.center
        )

        # Criar card para valor potencial
        card_valor_potencial = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Valor Potencial de Vendas",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    ),
                    self.valor_potencial
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            width=200,
            height=100,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.GREEN_700, ft.colors.GREEN_900]
            ),
            border_radius=10,
            padding=15,
            alignment=ft.alignment.center
        )

        # Adicionar referências para as tabelas
        self.vendas_table = ft.Ref[ft.DataTable]()
        self.estoque_table = ft.Ref[ft.DataTable]()

        # Modificar a criação das tabelas para usar as referências
        vendas_table = ft.DataTable(
            ref=self.vendas_table,
            columns=[
                ft.DataColumn(ft.Text("ID", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Vendedor", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Total", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Pagamento", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Data/Hora", color=ft.colors.GREY_900))
            ],
            rows=[]
        )

        estoque_table = ft.DataTable(
            ref=self.estoque_table,
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Produto", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Estoque", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Mínimo", color=ft.colors.GREY_900))
            ],
            rows=[]
        )

    # Método para sincronizar dados
    async def sincronizar_dados(self, e):
        # Obter a referência do botão de sincronização
        sync_button = e.control
        
        # Mostrar feedback visual de carregamento
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.colors.WHITE),
                    ft.Text("Sincronizando dados com o servidor...", color=ft.colors.WHITE)
                ],
                spacing=10
            ),
            bgcolor=ft.colors.BLUE_700,
            duration=5000
        )
        
        # Iniciar animação de rotação no botão
        sync_button.icon = ft.icons.SYNC
        sync_button.disabled = True
        self.page.update()
        
        try:
            # Executar a sincronização usando o novo SyncManager
            sync_manager = SyncManager()
            results = await sync_manager.sincronizar_todas_entidades()
            
            # Atualizar os valores do dashboard
            self.atualizar_valores()
            
            # Mostrar mensagem de sucesso
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.WHITE),
                        ft.Text("Dados sincronizados com sucesso!", color=ft.colors.WHITE)
                    ],
                    spacing=10
                ),
                bgcolor=ft.colors.GREEN_700,
                duration=3000
            )
            
        except Exception as e:
            # Em caso de erro, mostrar mensagem de erro
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.ERROR, color=ft.colors.WHITE),
                        ft.Text(f"Erro ao sincronizar: {str(e)}", color=ft.colors.WHITE)
                    ],
                    spacing=10
                ),
                bgcolor=ft.colors.RED_700,
                duration=5000
            )
        finally:
            # Restaurar o botão e atualizar a UI
            sync_button.disabled = False
            sync_button.icon = ft.icons.SYNC
            self.page.snack_bar.open = True
            self.page.update()

    def _is_web(self) -> bool:
        """Detecta se está rodando no navegador (web)."""
        try:
            if os.getenv('WEB_MODE', '').lower() == 'true':
                return True
            return str(getattr(self.page, 'platform', '')).lower() in ("ios", "android", "web")
        except Exception:
            return False

    def _get_backend_url(self) -> str:
        """Obtém a URL do backend do arquivo de configuração ou variáveis de ambiente."""
        try:
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    conf = json.load(f)
                    return conf.get('server_url', os.getenv('BACKEND_URL', 'http://localhost:8000'))
        except Exception:
            pass
        return os.getenv('BACKEND_URL', 'http://localhost:8000')

    def _get_api_base(self) -> str:
        """Retorna a base da API, garantindo que haja exatamente um '/api'."""
        base = (self._get_backend_url() or '').rstrip('/')
        if base.endswith('/api'):
            return base
        if base.endswith('/api/'):
            return base[:-1]
        return base + '/api'

    def _fetch_web_dashboard_numbers_sync(self):
        """Versão síncrona: busca números de vendas no backend e atualiza os cards (para web)."""
        api_base = self._get_api_base()
        try:
            hoje = datetime.now().date().isoformat()
            ano_mes = datetime.now().strftime('%Y-%m')

            vendas_dia = 0.0
            vendas_mes = 0.0
            lucro_dia = 0.0
            lucro_mes = 0.0

            # Preferir endpoints de métricas (com fallback)
            url_dia_1 = f"{api_base}/metricas/vendas-dia"
            url_mes_1 = f"{api_base}/metricas/vendas-mes"
            with httpx.Client(timeout=10.0) as client:
                try:
                    print(f"[WEB] Dashboard buscando métricas em: {url_dia_1} e {url_mes_1}")
                    resp_dia = client.get(url_dia_1)
                    resp_mes = client.get(url_mes_1)
                    if resp_dia.status_code == 200:
                        payload = resp_dia.json() or {}
                        vendas_dia = float(payload.get('total') or 0.0)
                    else:
                        print(f"[WEB] Falha ao buscar vendas-dia ({resp_dia.status_code}) em {url_dia_1}")
                    if resp_mes.status_code == 200:
                        payload = resp_mes.json() or {}
                        vendas_mes = float(payload.get('total') or 0.0)
                    else:
                        print(f"[WEB] Falha ao buscar vendas-mes ({resp_mes.status_code}) em {url_mes_1}")
                except Exception as ex:
                    print(f"[WEB] Erro ao buscar métricas: {ex}. Fallback para listar vendas...")
                    # Fallback: listar vendas e somar
                    url1 = f"{api_base}/vendas/"
                    url2 = f"{api_base}/vendas"
                    try:
                        resp = client.get(url1)
                        if resp.status_code == 404:
                            resp = client.get(url2)
                        if resp.status_code == 200:
                            vendas = resp.json() or []
                            for v in vendas:
                                status = (v.get('status') or '').lower()
                                if status == 'anulada':
                                    continue
                                total = float(v.get('total') or 0)
                                data_venda = v.get('data_venda') or ''
                                if data_venda.startswith(hoje):
                                    vendas_dia += total
                                if data_venda.startswith(ano_mes):
                                    vendas_mes += total
                        else:
                            print(f"[WEB] Falha ao buscar vendas no fallback ({resp.status_code}) em {url1} e {url2}")
                    except Exception as ex2:
                        print(f"[WEB] Erro no fallback listar vendas: {ex2}")

            # Atualizar textos
            self.vendas_dia.value = f"MT {vendas_dia:.2f}"
            self.vendas_mes.value = f"MT {vendas_mes:.2f}"
            if self._flag_true(self.usuario.get('is_admin')):
                self.lucro_dia.value = f"MT {lucro_dia:.2f}"
                self.lucro_mes.value = f"MT {lucro_mes:.2f}"
            # Atualizar UI
            try:
                self.update()
                if hasattr(self, 'page') and self.page:
                    self.page.update()
            except Exception:
                pass

        except Exception as e:
            print(f"Erro ao buscar números do dashboard (web): {e}")

    def build(self):
        # Diagnóstico: exibir permissões do usuário
        try:
            print("[DASHBOARD] Usuario logado:", {
                'nome': self.usuario.get('nome'),
                'usuario': self.usuario.get('usuario'),
                'is_admin': self.usuario.get('is_admin'),
                'pode_abastecer': self.usuario.get('pode_abastecer'),
                'pode_gerenciar_despesas': self.usuario.get('pode_gerenciar_despesas'),
            })
        except Exception:
            pass
        # Cabeçalho com botão sair
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        name=ft.icons.DASHBOARD,  # Adicionado ícone de dashboard
                        size=50,
                        color=ft.colors.WHITE # Adicionando a cor do texto
                    ),
                    ft.Text(
                        "Dashboard",
                        size=30,
                        weight=ft.FontWeight.BOLD, # Deixando o texto em negrito
                        color=ft.colors.WHITE
                    ),
                    ft.Container(width=20),  # Espaçador
                    ft.Text(
                        f"{self.t('welcome')}, {self.usuario.get('nome', 'Usuário')}!",
                        size=16,
                        color=ft.colors.WHITE
                    ),
                    ft.Container(expand=True),  # Espaçador flexível
                    # Indicador de status de conexão
                    self.status_indicator,
                    ft.Container(width=15),  # Espaço entre status e botões
                    ft.Row([
                        ft.IconButton(
                            icon=ft.icons.SYNC,
                            tooltip="Sincronizar Dados",
                            on_click=self._on_sync_clicked,
                            icon_color=ft.colors.WHITE,
                            icon_size=20,
                            style=ft.ButtonStyle(
                                side=ft.border.BorderSide(1, ft.colors.WHITE),
                                shape=ft.RoundedRectangleBorder(radius=5),
                                padding=8,
                                bgcolor=ft.colors.with_opacity(ft.colors.BLUE_600, 0.3)
                            ),
                            animate_rotation=ft.animation.Animation(300, ft.AnimationCurve.BOUNCE_OUT),
                        ),
                        ft.Container(width=8),  # Espaço entre os botões
                        ft.IconButton(
                            icon=ft.icons.LOGOUT,
                            tooltip="Terminar Sessão",
                            on_click=lambda e: self.terminar_sessao(),
                            icon_color=ft.colors.WHITE,
                            icon_size=20,
                            style=ft.ButtonStyle(
                                side=ft.border.BorderSide(1, ft.colors.WHITE),
                                shape=ft.RoundedRectangleBorder(radius=5),
                                padding=8
                            )
                        ),
                        ft.Container(width=8),  # Espaço entre os botões
                        ft.IconButton(
                            icon=ft.icons.POWER_SETTINGS_NEW,
                            tooltip="Sair do Sistema",
                            on_click=lambda e: self.sair(),
                            icon_color=ft.colors.RED_300,
                            icon_size=20,
                            style=ft.ButtonStyle(
                                side=ft.border.BorderSide(1, ft.colors.RED_300),
                                shape=ft.RoundedRectangleBorder(radius=5),
                                padding=8,
                                bgcolor=ft.colors.with_opacity(ft.colors.RED_900, 0.3)
                            )
                        )
                    ])
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
            ),
            padding=50,
            border_radius=10
        )

        # Botões de ação
        buttons = [
            ft.Container(
                content=ft.ElevatedButton(
                    "PDV",
                    icon=ft.icons.POINT_OF_SALE,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN
                    ),
                    on_click=lambda _: self.page.go("/pdv")
                ),
                col={"sm": 6, "md": 3}
            ),
            ft.Container(
                content=ft.ElevatedButton(
                    "Minhas Vendas",
                    icon=ft.icons.SHOPPING_CART,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.BLUE
                    ),
                    on_click=lambda _: self.page.go("/minhas-vendas")
                ),
                col={"sm": 6, "md": 3}
            ),
            ft.Container(
                content=ft.ElevatedButton(
                    "Configurações",
                    icon=ft.icons.SETTINGS,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.ORANGE
                    ),
                    on_click=lambda _: self.page.go("/configuracoes")
                ),
                col={"sm": 6, "md": 3}
            ),
            ft.Container(
                content=ft.ElevatedButton(
                    "Dívidas",
                    icon=ft.icons.ACCOUNT_BALANCE_WALLET,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.RED_700
                    ),
                    on_click=lambda _: self.page.go("/dividas")
                ),
                col={"sm": 6, "md": 3}
            ),
            ft.Container(
                content=ft.ElevatedButton(
                    "Sobre",
                    icon=ft.icons.INFO,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.TEAL_700
                    ),
                    on_click=lambda _: self.page.go("/sobre")
                ),
                col={"sm": 6, "md": 3}
            )
        ]
        
        # Adicionar botão de abastecimento para usuários com permissão (admin ou pode_abastecer)
        if self._flag_true(self.usuario.get('is_admin')) or self._flag_true(self.usuario.get('pode_abastecer')):
            buttons.extend([
                ft.Container(
                    content=ft.ElevatedButton(
                        "Abastecimento",
                        icon=ft.icons.LOCAL_SHIPPING,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_800
                        ),
                        on_click=lambda _: self.page.go("/abastecimento")
                    ),
                    col={"sm": 6, "md": 3}
                )
            ])
        
        # Adicionar botão de despesas para usuários com permissão (admin ou pode_gerenciar_despesas)
        if self._flag_true(self.usuario.get('is_admin')) or self._flag_true(self.usuario.get('pode_gerenciar_despesas')):
            buttons.extend([
                ft.Container(
                    content=ft.ElevatedButton(
                        "Gestão de Despesas",
                        icon=ft.icons.MONEY_OFF,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.RED
                        ),
                        on_click=lambda _: self.page.go("/despesas")
                    ),
                    col={"sm": 6, "md": 3}
                )
            ])
        
        if self._flag_true(self.usuario.get('is_admin')):
            buttons.extend([
                ft.Container(
                    content=ft.ElevatedButton(
                        "Buscar Vendas",
                        icon=ft.icons.SEARCH,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE
                        ),
                        on_click=lambda _: self.page.go("/busca-vendas")
                    ),
                    col={"sm": 6, "md": 3}
                ),
            ])
            
            buttons.extend([
                ft.Container(
                    content=ft.ElevatedButton(
                        "Produtos",
                        icon=ft.icons.INVENTORY,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.INDIGO
                        ),
                        on_click=lambda _: self.page.go("/produtos")
                    ),
                    col={"sm": 6, "md": 3}
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Clientes",
                        icon=ft.icons.PEOPLE_ALT,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.CYAN_700
                        ),
                        on_click=lambda _: self.page.go("/clientes")
                    ),
                    col={"sm": 6, "md": 3}
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Funcionários",
                        icon=ft.icons.PEOPLE,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_700
                        ),
                        on_click=lambda _: self.page.go("/usuarios")
                    ),
                    col={"sm": 6, "md": 3}
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Todas as Vendas",
                        icon=ft.icons.RECEIPT_LONG,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.TEAL
                        ),
                        on_click=lambda _: self.page.go("/todas-vendas")
                    ),
                    col={"sm": 6, "md": 3}
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Relatórios",
                        icon=ft.icons.REPORT,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.ORANGE_500
                        ),
                        on_click=lambda _: self.page.go("/relatorios")
                    ),
                    col={"sm": 6, "md": 3}
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Relatório Financeiro",
                        icon=ft.icons.REPORT,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE
                        ),
                        on_click=lambda _: self.page.go("/relatorio-financeiro")
                    ),
                    col={"sm": 6, "md": 3}
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Gerenciar Vendas",
                        icon=ft.icons.EDIT_NOTE,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE
                        ),
                        on_click=lambda _: self.page.go("/gerenciar-vendas")
                    ),
                    col={"sm": 6, "md": 3}
                )
            ])

        return ft.Container(
                content=ft.Column(
                    controls=[
                        header,
                        ft.Container(height=20),
                        ft.ResponsiveRow(
                            controls=buttons
                        ),
                        ft.Container(height=20),
                        self.get_stats_cards()
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True
                ),
                padding=20
            )

    def _flag_true(self, value) -> bool:
        """Converte flags vindas como bool/int/str para booleano confiável.
        Aceita valores como 1, '1', 'true', 'True', 'SIM', 'yes', 'y'.
        """
        try:
            if isinstance(value, bool):
                return value
            if value is None:
                return False
            # ints/floats
            if isinstance(value, (int, float)):
                return int(value) != 0
            s = str(value).strip().lower()
            return s in ("1", "true", "sim", "yes", "y", "t")
        except Exception:
            return False

    def get_stats_cards(self):
        try:
            # Buscar vendas do dia
            if self.usuario.get('is_admin'):
                vendas_dia = self.db.get_total_vendas_hoje()
            else:
                vendas_dia = self.db.fetchone("""
                    SELECT COALESCE(SUM(total), 0) as total
                    FROM vendas 
                    WHERE usuario_id = ? 
                        AND DATE(data_venda) = DATE('now')
                        AND (status IS NULL OR status != 'Anulada')
                """, (self.usuario['id'],))['total']

            # Buscar vendas do mês
            if self.usuario.get('is_admin'):
                vendas_mes = self.db.get_total_vendas_mes()
            else:
                vendas_mes = self.db.fetchone("""
                    SELECT COALESCE(SUM(total), 0) as total
                    FROM vendas 
                    WHERE usuario_id = ? 
                        AND strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
                        AND (status IS NULL OR status != 'Anulada')
                """, (self.usuario['id'],))['total']

            # Produtos com estoque baixo
            estoque_baixo = self.db.fetchone("""
                SELECT COUNT(*) 
                FROM produtos 
                WHERE estoque <= estoque_minimo AND ativo = 1
            """)[0]

            # Inicializar valores padrão
            valor_estoque = self.db.get_valor_estoque()
            valor_potencial = self.db.get_valor_venda_estoque()
            lucro_mes = 0.0  # Inicializa com valor padrão
            lucro_dia = 0.0  # Inicializa com valor padrão
            
            # Buscar valores específicos para administradores
            if self._flag_true(self.usuario.get('is_admin')):
                lucro_mes = self.db.get_lucro_mes()
                lucro_dia = self.db.get_lucro_dia()
            
            # Cards base que todos os usuários verão
            cards = [
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            self.t("my_sales_today"),
                            size=16, 
                            color=ft.colors.WHITE
                        ),
                        ft.Text(
                            f"MT {vendas_dia:.2f}",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[ft.colors.GREEN_700, ft.colors.GREEN_900]
                    ),
                    padding=25,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                    ),
                    col={"sm": 6, "md": 3}
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            self.t("my_sales_month"),
                            size=16,
                            color=ft.colors.WHITE
                        ),
                        ft.Text(
                            f"MT {vendas_mes:.2f}",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[ft.colors.BLUE_700, ft.colors.BLUE_900]
                    ),
                    padding=25,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                    ),
                    col={"sm": 6, "md": 3}
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Produtos com Estoque Baixo",
                            size=16,
                            color=ft.colors.WHITE
                        ),
                        ft.Text(
                            str(estoque_baixo),
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[ft.colors.RED_700, ft.colors.RED_900]
                    ),
                    padding=25,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                    ),
                    col={"sm": 6, "md": 3}
                )
            ]

            # Adicionar cards adicionais apenas para admin
            if self.usuario.get('is_admin'):
                admin_cards = [
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Lucro de Hoje",
                                size=16,
                                color=ft.colors.WHITE
                            ),
                            ft.Text(
                                f"MT {lucro_dia:.2f}",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.WHITE
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.colors.ORANGE_700, ft.colors.ORANGE_900]
                        ),
                        padding=25,
                        border_radius=10,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                        ),
                        col={"sm": 6, "md": 3}
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Lucro Potencial do Estoque",
                                size=16,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.colors.WHITE
                            ),
                            ft.Text(
                                f"MT {self.db.get_lucro_potencial_estoque():.2f}",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.WHITE
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.colors.PURPLE_700, ft.colors.PURPLE_900]
                        ),
                        padding=25,
                        border_radius=10,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                        ),
                        col={"sm": 6, "md": 3}
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Lucro do Mês",
                                size=16,
                                color=ft.colors.WHITE
                            ),
                            ft.Text(
                                f"MT {lucro_mes:.2f}",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.WHITE
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.colors.BLUE_700, ft.colors.BLUE_900]
                        ),
                        padding=25,
                        border_radius=10,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                        ),
                        col={"sm": 6, "md": 3}
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Valor Total em Estoque",
                                size=16,
                                color=ft.colors.WHITE
                            ),
                            ft.Text(
                                f"MT {valor_estoque:.2f}",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.WHITE
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.colors.INDIGO_700, ft.colors.INDIGO_900]
                        ),
                        padding=25,
                        border_radius=10,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                        ),
                        col={"sm": 6, "md": 3}
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Valor Potencial de Vendas",
                                size=16,
                                color=ft.colors.WHITE
                            ),
                            ft.Text(
                                f"MT {valor_potencial:.2f}",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.WHITE
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.colors.TEAL_700, ft.colors.TEAL_900]
                        ),
                        padding=25,
                        border_radius=10,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                        ),
                        col={"sm": 6, "md": 3}
                    )
                ]
                cards.extend(admin_cards)

            return ft.ResponsiveRow(controls=cards)
            
        except Exception as e:
            print(f"Erro ao carregar estatísticas: {e}")
            return ft.Text("Erro ao carregar estatísticas")

    def get_lucro_mes(self):
        try:
            query = """
                SELECT
                    SUM(
                        CASE
                            WHEN v.status = 'Anulada' THEN 0
                            ELSE (
                                CASE 
                                    WHEN iv.status = 'Removido' THEN 0
                                    ELSE (iv.subtotal - (iv.preco_custo_unitario * iv.quantidade))
                                END
                            )
                        END
                    ) as lucro
                FROM vendas v
                JOIN itens_venda iv ON v.id = iv.venda_id
                WHERE strftime('%Y-%m', v.data_venda) = strftime('%Y-%m', 'now')
            """
            result = self.db.fetchone(query)
            return result['lucro'] or 0

        except Exception as e:
            return 0

    def get_latest_sales(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT v.id, v.data_venda, u.nome, v.total, v.forma_pagamento 
                FROM vendas v
                JOIN usuarios u ON u.id = v.usuario_id
                WHERE (v.status IS NULL OR v.status != 'Anulada')
                ORDER BY v.data_venda DESC LIMIT 5
            """)
            vendas = cursor.fetchall()
        except Exception as e:
            vendas = []

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(name=ft.icons.RECEIPT_LONG, color=ft.colors.BLUE),
                        ft.Text("Últimas Vendas", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK)
                    ],
                    alignment=ft.MainAxisAlignment.START
                ),
                ft.Container(
                    content=ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("ID")),
                            ft.DataColumn(ft.Text("Data")),
                            ft.DataColumn(ft.Text("Vendedor")),
                            ft.DataColumn(ft.Text("Total")),
                            ft.DataColumn(ft.Text("Pagamento"))
                        ],
                        rows=[
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(str(v[0]))),
                                    ft.DataCell(ft.Text(datetime.strptime(v[1], '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M'))),
                                    ft.DataCell(ft.Text(v[2])),
                                    ft.DataCell(ft.Text(f"MT {v[3]:,.2f}")),
                                    ft.DataCell(ft.Text(v[4]))
                                ]
                            ) for v in vendas
                        ]
                    ),
                    padding=10
                )
            ],
            spacing=10
        )

    def get_top_products(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT p.codigo, p.nome, 
                       COUNT(iv.id) as vendidos,
                       p.estoque
                FROM produtos p
                LEFT JOIN itens_venda iv ON p.id = iv.produto_id
                GROUP BY p.id
                ORDER BY vendidos DESC
                LIMIT 5
            """)
            produtos = cursor.fetchall()
        except Exception as e:
            produtos = []

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(name=ft.icons.TRENDING_UP, color=ft.colors.GREEN),
                        ft.Text("Produtos Mais Vendidos", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK)
                    ],
                    alignment=ft.MainAxisAlignment.START
                ),
                ft.Container(
                    content=ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Código")),
                            ft.DataColumn(ft.Text("Nome")),
                            ft.DataColumn(ft.Text("Vendidos")),
                            ft.DataColumn(ft.Text("Estoque"))
                        ],
                        rows=[
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(p[0])),
                                    ft.DataCell(ft.Text(p[1])),
                                    ft.DataCell(ft.Text(str(p[2]))),
                                    ft.DataCell(ft.Text(str(p[3])))
                                ]
                            ) for p in produtos
                        ]
                    ),
                    padding=10
                )
            ],
            spacing=10
        )

    def get_tables_row(self):
        # Tabela de Vendas Recentes - Modificada para filtrar por usuário
        query_vendas = """
            SELECT 
                v.id,
                u.nome as vendedor,
                v.total,
                v.forma_pagamento,
                v.data_venda
            FROM vendas v
            JOIN usuarios u ON u.id = v.usuario_id
            WHERE (v.status IS NULL OR v.status != 'Anulada')
            AND DATE(v.data_venda) = DATE('now')
            {}
            ORDER BY v.data_venda DESC
            LIMIT 5
        """
        
        # Adiciona filtro por usuário se não for admin
        where_clause = "AND v.usuario_id = ?" if not self.usuario.get('is_admin') else ""
        params = (self.usuario['id'],) if not self.usuario.get('is_admin') else ()
        
        vendas_recentes = self.db.fetchall(
            query_vendas.format(where_clause), 
            params
        )

        vendas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Vendedor", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Total", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Pagamento", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Data/Hora", color=ft.colors.GREY_900))
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(v['id']), color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(v['vendedor'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(f"MT {v['total']:.2f}", color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(v['forma_pagamento'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(v['data_venda'], color=ft.colors.GREY_900))
                    ]
                ) for v in vendas_recentes
            ]
        )

        # Tabela de Produtos com Estoque Baixo
        produtos_baixo_estoque = self.get_low_stock_products(limit=5)

        estoque_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.GREY_900, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Produto", color=ft.colors.GREY_900, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estoque", color=ft.colors.GREY_900, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Mínimo", color=ft.colors.GREY_900, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.GREY_900, weight=ft.FontWeight.BOLD))
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p['codigo'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(p['nome'], color=ft.colors.GREY_900)),
                        ft.DataCell(
                            ft.Text(
                                str(p['estoque']),
                                color=ft.colors.RED if p['estoque'] <= p['estoque_minimo'] else ft.colors.GREY_900,
                                weight=ft.FontWeight.BOLD if p['estoque'] <= p['estoque_minimo'] else None
                            )
                        ),
                        ft.DataCell(ft.Text(str(p['estoque_minimo']), color=ft.colors.GREY_900)),
                        ft.DataCell(
                            ft.Row(
                                [ft.IconButton(
                                    icon=ft.icons.VISIBILITY,
                                    icon_color=ft.colors.BLUE_600,
                                    tooltip="Visualizar produto",
                                    on_click=lambda e, p=p: self.show_edit_product_dialog(p)
                                )],
                                alignment=ft.MainAxisAlignment.CENTER
                            )
                        )
                    ],
                    on_select_changed=lambda e, p=p: self.show_edit_product_dialog(p)
                ) for p in produtos_baixo_estoque
            ],
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=5,
            heading_row_color=ft.colors.BLUE_50,
            heading_row_height=40,
            data_row_min_height=40,
            data_row_max_height=40,
            horizontal_margin=10,
            column_spacing=20,
            divider_thickness=0.5,
            show_bottom_border=True,
            sort_column_index=2,
            sort_ascending=True
        )

        # Container para as tabelas
        return ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Vendas Recentes" if self.usuario.get('is_admin') else "Minhas Vendas Recentes",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLACK
                        ),
                        ft.Container(
                            content=ft.Column(
                                [vendas_table],
                                scroll=ft.ScrollMode.AUTO
                            ),
                            height=270,
                            border=ft.border.all(1, ft.colors.BLACK26),
                            border_radius=10,
                            padding=10
                        )
                    ]),
                    bgcolor=ft.colors.WHITE,
                    padding=20,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.1, ft.colors.BLACK)
                    ),
                    col={"sm": 12, "md": 12, "lg": 6}
                ),
                # Card de Produtos com Estoque Baixo
                ft.Container(
                    content=ft.Column(
                        controls=[
                            # Cabeçalho do card com ícone de alerta e seta
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        # Lado esquerdo: Ícone e texto
                                        ft.Row(
                                            controls=[
                                                ft.Icon(ft.icons.WARNING_AMBER, color=ft.colors.AMBER),
                                                ft.Text(
                                                    "Produtos com Estoque Baixo",
                                                    size=16,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=ft.colors.BLACK
                                                ),
                                                ft.Text(
                                                    "🔍",
                                                    size=20,
                                                    color=ft.colors.RED_400,
                                                    tooltip="Ver produtos com estoque baixo"
                                                )
                                            ],
                                            spacing=5,
                                            expand=True
                                        ),
                                        # Lado direito: Seta de navegação
                                        ft.Icon(ft.icons.ARROW_FORWARD_IOS, size=16, color=ft.colors.GREY_600)
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            ),
                            # Tabela de produtos
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.GestureDetector(
                                            content=estoque_table,
                                            on_tap=lambda e: self.handle_low_stock_click(e)
                                        )
                                    ],
                                    scroll=ft.ScrollMode.AUTO
                                ),
                                height=270,
                                margin=ft.margin.only(top=10),
                                border=ft.border.all(1, ft.colors.BLACK26),
                                border_radius=10,
                                padding=10
                            )
                        ]
                    ),
                    bgcolor=ft.colors.WHITE,
                    padding=20,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.1, ft.colors.BLACK)
                    ),
                    col={"sm": 12, "md": 12, "lg": 6},
                    on_click=lambda e: self.handle_low_stock_click(e),
                    on_hover=lambda e: self.handle_hover(e),
                    ink=True,
                    tooltip="Clique para ver e editar todos os produtos com estoque baixo"
                )
            ]
        )
    def terminar_sessao(self):
        """Termina a sessão atual e volta para a tela de login"""
        # Limpa os dados da sessão
        self.page.data.clear()
        # Volta para a tela de login
        self.page.go("/")
        
    def sair(self):
        """Fecha o aplicativo"""
        # Fecha a aplicação
        self.page.window_destroy()

    def ir_para_clientes(self, e):
        self.page.go("/clientes")

    def ir_para_compras_dia(self, e):
        print("Clicou em Compras do Dia")
        self.page.go("/compras-dia")

    def atualizar_valores(self, resetar=False):
        """Atualiza os valores mostrados nos cards
        
        Args:
            resetar (bool, optional): Se True, zera os valores para funcionários. Defaults to False.
        """
        print("\n=== ATUALIZANDO VALORES DO DASHBOARD ===")
        print(f"Usuário: {self.usuario.get('nome', 'N/A')} (Admin: {self.usuario.get('is_admin', False)})")
        print(f"Resetar valores: {resetar}")
        print("Chamando métodos do banco de dados...")
        
        # Valores básicos para todos os usuários
        # Se for funcionário e resetar=True, zerar os valores
        if not self.usuario.get('is_admin') and resetar:
            total_vendas_mes = 0.0
            total_vendas_dia = 0.0
            total_vendas_congelador = 0.0
            valor_estoque = self.db.get_valor_estoque()  # Manter valor do estoque
            valor_potencial = self.db.get_valor_venda_estoque()  # Manter valor potencial
            lucro_mes = 0.0
            lucro_dia = 0.0
        else:
            # Tentar buscar vendas locais primeiro
            total_vendas_mes = self.db.get_vendas_disponiveis_mes()  # Vendas menos saques
            total_vendas_dia = self.db.get_total_vendas_hoje()
            total_vendas_congelador = self.db.get_total_vendas_congelador_hoje()
            
            # Se não há vendas locais, tentar buscar do servidor
            if total_vendas_dia == 0.0 and total_vendas_mes == 0.0:
                print("🌐 Sem vendas locais - buscando do servidor...")
                vendas_servidor = self._buscar_vendas_servidor()
                if vendas_servidor:
                    total_vendas_dia = vendas_servidor.get('vendas_dia', 0.0)
                    total_vendas_mes = vendas_servidor.get('vendas_mes', 0.0)
                    print(f"📊 Vendas do servidor - Dia: MT {total_vendas_dia:.2f}, Mês: MT {total_vendas_mes:.2f}")
            
            valor_estoque = self.db.get_valor_estoque()
            valor_potencial = self.db.get_valor_venda_estoque()
            
            # Valores padrão para lucros
            lucro_mes = 0.0
            lucro_dia = 0.0
            
            # Obter valores específicos para administradores
            if self.usuario.get('is_admin'):
                lucro_mes = self.db.get_lucro_disponivel_mes()  # Lucro menos saques
                lucro_dia = self.db.get_lucro_dia()

        print(f"Total vendas mês (disponível): MT {total_vendas_mes:.2f}")
        print(f"Lucro mês (disponível): MT {lucro_mes:.2f}")
        print(f"Total vendas dia: MT {total_vendas_dia:.2f}")
        print(f"Lucro dia: MT {lucro_dia:.2f}")
        print(f"Vendas congelador: MT {total_vendas_congelador:.2f}")
        print(f"Valor em estoque: MT {valor_estoque:.2f}")
        print(f"Valor potencial: MT {valor_potencial:.2f}")

        # Verificar se os objetos de texto existem antes de atualizá-los
        if hasattr(self, 'vendas_mes') and self.vendas_mes:
            self.vendas_mes.value = f"MT {total_vendas_mes:.2f}"
        if hasattr(self, 'vendas_dia') and self.vendas_dia:
            self.vendas_dia.value = f"MT {total_vendas_dia:.2f}"
        if hasattr(self, 'vendas_congelador') and self.vendas_congelador:
            self.vendas_congelador.value = f"MT {total_vendas_congelador:.2f}"
        if hasattr(self, 'valor_estoque') and self.valor_estoque:
            self.valor_estoque.value = f"MT {valor_estoque:.2f}"
        if hasattr(self, 'valor_potencial') and self.valor_potencial:
            self.valor_potencial.value = f"MT {valor_potencial:.2f}"
        if hasattr(self, 'lucro_mes') and self.lucro_mes:
            self.lucro_mes.value = f"MT {lucro_mes:.2f}"
        if hasattr(self, 'lucro_dia') and self.lucro_dia:
            self.lucro_dia.value = f"MT {lucro_dia:.2f}"

        try:
            # Forçar atualização da UI de múltiplas formas
            print("Forçando atualização da UI...")
            
            # 1. Forçar reconstrução dos cards primeiro
            self._force_rebuild_cards(resetar=resetar)
            
            # 2. Atualizar o controle
            self.update()
            
            # 3. Atualizar a página
            if hasattr(self, 'page') and self.page:
                self.page.update()
            
            # 4. Forçar atualização adicional após um pequeno delay
            if hasattr(self, 'page') and self.page:
                # Tentar forçar uma atualização adicional
                try:
                    self.page.update()
                except:
                    pass
            
            print("=== VALORES DO DASHBOARD ATUALIZADOS ===\n")
        except Exception as e:
            print(f"Erro ao atualizar dashboard: {e}")
            # Tentar atualizar a página se o controle não estiver na página
            try:
                if hasattr(self, 'page') and self.page:
                    self.page.update()
            except Exception as e2:
                print("=== Fim did_mount() ===")

    def _buscar_vendas_servidor(self) -> Optional[Dict[str, float]]:
        """Busca vendas do servidor quando não há vendas locais"""
        try:
            import httpx
            from datetime import datetime
            import json
            import os
            
            # Obter URL do backend
            backend_url = self._get_backend_url()
            
            print(f"🔗 Tentando buscar vendas do servidor: {backend_url}")
            
            with httpx.Client(timeout=10.0) as client:
                # Buscar todas as vendas do servidor
                response = client.get(f"{backend_url}/api/vendas/")
                
                if response.status_code == 200:
                    vendas = response.json()
                    print(f"📥 Recebidas {len(vendas)} vendas do servidor")
                    
                    # Calcular vendas do dia e mês
                    hoje = datetime.now().date()
                    mes_atual = hoje.strftime('%Y-%m')
                    
                    vendas_dia = 0.0
                    vendas_mes = 0.0
                    
                    for venda in vendas:
                        try:
                            # Parse da data da venda - usar created_at se data_venda não existir
                            data_venda_str = venda.get('data_venda', '') or venda.get('created_at', '')
                            
                            if not data_venda_str:
                                print(f"⚠️ Venda {venda.get('id', 'N/A')} sem data - pulando")
                                continue
                            
                            # Processar data ISO format (created_at) ou date format (data_venda)
                            if 'T' in data_venda_str:
                                data_venda = datetime.fromisoformat(data_venda_str.replace('Z', '+00:00')).date()
                            else:
                                data_venda = datetime.strptime(data_venda_str[:10], '%Y-%m-%d').date()
                            
                            total = float(venda.get('total', 0))
                            cancelada = venda.get('cancelada', False)
                            
                            # Ignorar vendas canceladas
                            if cancelada:
                                continue
                            
                            # Vendas do mês
                            if data_venda.strftime('%Y-%m') == mes_atual:
                                vendas_mes += total
                                
                                # Vendas do dia
                                if data_venda == hoje:
                                    vendas_dia += total
                                    
                        except Exception as e:
                            print(f"⚠️ Erro ao processar venda {venda.get('id', 'N/A')}: {e}")
                            continue
                    
                    return {
                        'vendas_dia': vendas_dia,
                        'vendas_mes': vendas_mes
                    }
                else:
                    print(f"❌ Erro ao buscar vendas: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ Erro ao conectar com servidor: {e}")
            return None
    
    def _get_backend_url(self) -> str:
        """Obtém a URL do backend do arquivo de configuração"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('server_url', 'https://prototipo-production-c729.up.railway.app')
        except Exception:
            pass
        return os.getenv("BACKEND_URL", "https://prototipo-production-c729.up.railway.app")

    def get_low_stock_products(self, limit: int = None) -> List[Dict[str, Any]]:
        """Retorna a lista de produtos com estoque baixo"""
        query = """
            SELECT 
                id,
                codigo,
                nome,
                estoque,
                estoque_minimo,
                preco_venda
            FROM produtos
            WHERE estoque <= estoque_minimo
                AND ativo = 1
            ORDER BY estoque ASC
        """
        if limit:
            query += f" LIMIT {limit}"
            
        return self.db.fetchall(query)

    def show_edit_product_dialog(self, product: Dict[str, Any]):
        """Mostra um diálogo para editar um produto"""
        def save_changes(e):
            try:
                new_stock = int(estoque_field.value)
                new_min_stock = int(estoque_minimo_field.value)
                
                self.db.execute(
                    "UPDATE produtos SET estoque = ?, estoque_minimo = ? WHERE id = ?",
                    (new_stock, new_min_stock, product['id'])
                )
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Produto atualizado com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
                self.page.snack_bar.open = True
                self.page.dialog.open = False
                self.page.update()
                self.atualizar_valores()
            except ValueError:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Por favor, insira valores numéricos válidos"),
                    bgcolor=ft.colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        # Campos do formulário
        estoque_field = ft.TextField(
            label="Estoque Atual",
            value=str(product['estoque']),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200
        )
        
        estoque_minimo_field = ft.TextField(
            label="Estoque Mínimo",
            value=str(product['estoque_minimo']),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Editar {product['nome']}"),
            content=ft.Column(
                [
                    ft.Text(f"Código: {product['codigo']}"),
                    ft.Text(f"Preço: MT {product['preco_venda']:.2f}"),
                    ft.Divider(),
                    estoque_field,
                    estoque_minimo_field
                ],
                tight=True
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg, 'open', False) or self.page.update()),
                ft.TextButton("Salvar", on_click=save_changes),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def handle_low_stock_click(self, e):
        """Manipula o clique no card de estoque baixo"""
        print("DEBUG: handle_low_stock_click chamado")
        print(f"DEBUG: Evento: {e}")
        print(f"DEBUG: Página: {self.page}")
        print(f"DEBUG: Controles: {e.control}")
        self.show_all_low_stock_products(e)
        
    def handle_hover(self, e):
        """Muda a cor do card ao passar o mouse"""
        e.control.bgcolor = ft.colors.BLUE_GREY_50 if e.data == "true" else ft.colors.WHITE
        e.control.update()
        
    def show_all_low_stock_products(self, e=None):
        """Mostra todos os produtos com estoque baixo em uma nova página"""
        print("DEBUG: show_all_low_stock_products chamado")
        print(f"DEBUG: Evento recebido: {e}")
        
        # Força o foco para garantir que o evento de clique seja processado
        if e and hasattr(e, 'control'):
            e.control.focus()
            
        try:
            produtos = self.get_low_stock_products()
            print(f"DEBUG: {len(produtos)} produtos com estoque baixo encontrados")
            
            # Mostra uma mensagem de sucesso para confirmar que o clique foi registrado
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Mostrando {len(produtos)} produtos com estoque baixo"),
                action="OK"
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            print(f"ERRO ao obter produtos com estoque baixo: {str(ex)}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao carregar produtos: {str(ex)}"),
                bgcolor=ft.colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        def create_product_row(p):
            estoque_field = ft.TextField(
                value=str(p['estoque']),
                width=100,
                text_align=ft.TextAlign.RIGHT,
                keyboard_type=ft.KeyboardType.NUMBER
            )
            
            estoque_minimo_field = ft.TextField(
                value=str(p['estoque_minimo']),
                width=100,
                text_align=ft.TextAlign.RIGHT,
                keyboard_type=ft.KeyboardType.NUMBER
            )
            
            def save_product(e):
                try:
                    new_stock = int(estoque_field.value)
                    new_min_stock = int(estoque_minimo_field.value)
                    
                    self.db.execute(
                        "UPDATE produtos SET estoque = ?, estoque_minimo = ? WHERE id = ?",
                        (new_stock, new_min_stock, p['id'])
                    )
                    
                    # Atualiza a interface
                    estoque_field.border_color = ft.colors.GREEN
                    estoque_field.update()
                    
                    # Mostra mensagem de sucesso
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"{p['nome']} atualizado com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    
                except ValueError:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text("Por favor, insira valores numéricos válidos"),
                        bgcolor=ft.colors.RED
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            
            return ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(p['codigo'])),
                    ft.DataCell(ft.Text(p['nome'])),
                    ft.DataCell(estoque_field),
                    ft.DataCell(estoque_minimo_field),
                    ft.DataCell(
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.icons.VISIBILITY,
                                    icon_color=ft.colors.BLUE_600,
                                    tooltip="Visualizar produto",
                                    on_click=lambda e, p=p: self.show_edit_product_dialog(p)
                                ),
                                ft.ElevatedButton(
                                    "Atualizar",
                                    on_click=save_product,
                                    style=ft.ButtonStyle(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        bgcolor=ft.colors.BLUE_50,
                                        color=ft.colors.BLUE_700
                                    )
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=5
                        )
                    )
                ]
            )
        
        # Cria a tabela de produtos
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Produto", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estoque Atual", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estoque Mínimo", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ações", weight=ft.FontWeight.BOLD)),
            ],
            rows=[create_product_row(p) for p in produtos],
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=5,
            heading_row_color=ft.colors.BLUE_50,
            heading_row_height=40,
            data_row_min_height=50,
            horizontal_margin=10,
            column_spacing=20,
            divider_thickness=0.5,
            show_bottom_border=True,
        )
        
        # Cria o diálogo
        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.icons.WARNING_AMBER, color=ft.colors.AMBER),
                    ft.Text("Produtos com Estoque Baixo", weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Total de produtos com estoque baixo: {len(produtos)}", 
                              weight=ft.FontWeight.W_500),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Column([table], scroll=ft.ScrollMode.AUTO),
                            height=400,
                            width=800,
                        )
                    ],
                    spacing=15,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Fechar", 
                    on_click=lambda e: setattr(dlg, 'open', False) or self.page.update(),
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=20, vertical=10))
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def corrigir_estoque(self, e):
        """Corrige o estoque de vendas anuladas de dívidas quitadas"""
        try:
            # Mostrar diálogo de confirmação
            def confirmar_correcao(e):
                try:
                    # Executar correção
                    sucesso = self.db.corrigir_estoque_vendas_anuladas()
                    
                    if sucesso:
                        # Atualizar valores do dashboard
                        self.atualizar_valores()
                        
                        # Fechar diálogo
                        dialog.open = False
                        self.page.update()
                        
                        # Mostrar mensagem de sucesso
                        self.page.show_snack_bar(
                            ft.SnackBar(
                                content=ft.Text("✅ Estoque corrigido com sucesso!"),
                                bgcolor=ft.colors.GREEN
                            )
                        )
                    else:
                        self.page.show_snack_bar(
                            ft.SnackBar(
                                content=ft.Text("❌ Erro ao corrigir estoque!"),
                                bgcolor=ft.colors.RED
                            )
                        )
                        
                except Exception as error:
                    print(f"Erro ao corrigir estoque: {error}")
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"❌ Erro: {str(error)}"),
                            bgcolor=ft.colors.RED
                        )
                    )

            dialog = ft.AlertDialog(
                title=ft.Text("Corrigir Estoque"),
                content=ft.Text(
                    "Esta ação irá corrigir o estoque de vendas anuladas que têm origem em dívidas quitadas. "
                    "Isso é necessário para corrigir valores incorretos no estoque. "
                    "Deseja continuar?"
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                    ft.ElevatedButton(
                        "Corrigir",
                        icon=ft.icons.BUILD,
                        on_click=confirmar_correcao,
                        bgcolor=ft.colors.ORANGE_600,
                        color=ft.colors.WHITE
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as error:
            print(f"Erro ao mostrar diálogo de correção: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def sincronizar_dados_sync(self):
        """Versão síncrona do método de sincronização de dados"""
        try:
            # Usar o novo SyncManager
            import asyncio
            from repositories.sync_manager import SyncManager
            
            print("=== INICIANDO SINCRONIZAÇÃO DE DADOS ===")
            
            # Executar a sincronização de forma síncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sync_manager = SyncManager()
            result = loop.run_until_complete(sync_manager.sincronizar_todas_entidades())
            loop.close()
            
            # Imprimir resumo da sincronização
            print("\n=== RESUMO DA SINCRONIZAÇÃO ===")
            print(f"Status: {result['status']}")
            print(f"Total enviadas: {result['total_enviadas']}")
            print(f"Total recebidas: {result['total_recebidas']}")
            print(f"Duração: {result['duracao_segundos']:.2f} segundos")
            print(f"Mensagem: {result['message']}")
            print("=== FIM DO RESUMO ===\n")
            
            # Atualizar valores do dashboard
            print("=== INÍCIO ATUALIZAÇÃO DASHBOARD ===")
            self.atualizar_valores(resetar=False)
            print("Valores atualizados do banco de dados")
            
            # Reconstruir os cards
            print("Atualizando UI após reconstrução dos cards...")
            self._force_rebuild_cards(resetar=False)
            print("Reconstrução dos cards concluída com sucesso")
            
            # Verificar produtos com estoque baixo
            produtos_baixo_estoque = self.get_low_stock_products()
            print(f"Produtos com estoque baixo: {len(produtos_baixo_estoque)}")
            
            # Manter um print para a mensagem final que aparece na UI
            print("Sincronização concluída com sucesso!")
            return True
        except Exception as ex:
            # Usar logger para registrar o erro
            logger.error(f"Erro na sincronização: {ex}")
            import traceback
            logger.error(traceback.format_exc())
            # Manter print para a UI
            print(f"Erro na sincronização: {ex}")
            return False
    
    def _on_sync_clicked(self, e):
        """Manipulador de clique do botão de sincronização para Flet 0.9.0"""
        # Armazenar referência do controle
        control = e.control
        
        # Função para atualizar a UI (síncrona)
        def update_ui(icon=None, disabled=False, content=None):
            control.icon = icon
            control.content = content
            control.disabled = disabled
            control.update()
        
        # Desabilitar o botão durante a sincronização, mas manter o ícone
        update_ui(icon=ft.icons.SYNC, disabled=True, content=None)
        
        # Função para executar a sincronização híbrida
        def sync_task():
            try:
                # Usar o repositório híbrido para sincronização
                from repositories.sync_manager import SyncManager
                import asyncio
                
                async def sync_hibrido():
                    sync_manager = SyncManager()
                    
                    # Verificar status da conexão
                    is_online = await sync_manager.is_backend_online()
                    
                    if is_online:
                        # Sincronizar todas as entidades
                        resultado = await sync_manager.sincronizar_todas_entidades()
                        return resultado
                    else:
                        return {"status": "offline", "message": "Backend offline - operando localmente"}
                
                # Executar sincronização
                resultado = asyncio.run(sync_hibrido())
                
                # Mostrar mensagem baseada no resultado
                if resultado.get("status") == "success":
                    enviadas = resultado.get("total_enviadas", 0)
                    recebidas = resultado.get("total_recebidas", 0)
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            ft.Text(f"✅ Sincronização completa! Enviadas: {enviadas}, Recebidas: {recebidas}", color=ft.colors.WHITE),
                            bgcolor=ft.colors.GREEN_700,
                            duration=3000,
                        )
                    )
                elif resultado.get("status") == "offline":
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            ft.Text("🔴 Backend offline - Sistema funcionando localmente", color=ft.colors.WHITE),
                            bgcolor=ft.colors.ORANGE_700,
                            duration=3000,
                        )
                    )
                else:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            ft.Text("❌ Erro na sincronização. Verifique o console.", color=ft.colors.WHITE),
                            bgcolor=ft.colors.RED_700,
                            duration=5000,
                        )
                    )
                
            except Exception as ex:
                # Mostrar mensagem de erro
                self.page.show_snack_bar(
                    ft.SnackBar(
                        ft.Text(f"Erro na sincronização: {str(ex)}", color=ft.colors.WHITE),
                        bgcolor=ft.colors.RED_700,
                        duration=5000,
                    )
                )
                print(f"Erro na sincronização: {ex}")
                
            finally:
                # Restaurar estado do botão
                if control.page:  # Verificar se a página ainda existe
                    update_ui(icon=ft.icons.SYNC, disabled=False, content=None)
        
        # Executar a tarefa em uma thread separada
        import threading
        threading.Thread(target=sync_task).start()

    def _force_rebuild_cards(self, resetar=False):
        """Força a reconstrução dos cards do dashboard
        
        Args:
            resetar (bool, optional): Se True, zera os valores para funcionários. Defaults to False.
        """
        try:
            print("Forçando reconstrução dos cards...")
            print(f"Resetar valores: {resetar}")
            
            # Inicializar valores
            if not self.usuario.get('is_admin') and resetar:
                # Se for funcionário e resetar=True, zerar os valores
                total_vendas_mes = 0.0
                total_vendas_dia = 0.0
                total_vendas_congelador = 0.0
                valor_estoque = self.db.get_valor_estoque()  # Manter valor do estoque
                valor_potencial = self.db.get_valor_venda_estoque()  # Manter valor potencial
                lucro_mes = 0.0
                lucro_dia = 0.0
                print("Valores zerados para funcionário")
            else:
                # Caso contrário, buscar valores atualizados
                total_vendas_mes = self.db.get_vendas_disponiveis_mes()
                total_vendas_dia = self.db.get_total_vendas_hoje()
                total_vendas_congelador = self.db.get_total_vendas_congelador_hoje()
                valor_estoque = self.db.get_valor_estoque()
                valor_potencial = self.db.get_valor_venda_estoque()
                lucro_mes = self.db.get_lucro_mes() if self.usuario.get('is_admin') else 0.0
                lucro_dia = self.db.get_lucro_dia() if self.usuario.get('is_admin') else 0.0
                print("Valores atualizados do banco de dados")
            
            # Recriar os Text objects com novos valores
            self.vendas_mes = ft.Text(
                value=f"MT {total_vendas_mes:.2f}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK
            )
            
            self.vendas_dia = ft.Text(
                value=f"MT {total_vendas_dia:.2f}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK
            )
            
            self.vendas_congelador = ft.Text(
                value=f"MT {total_vendas_congelador:.2f}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK
            )
            
            self.valor_estoque = ft.Text(
                value=f"MT {valor_estoque:.2f}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK
            )
            
            self.valor_potencial = ft.Text(
                value=f"MT {valor_potencial:.2f}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK
            )
            
            self.lucro_mes = ft.Text(
                value=f"MT {lucro_mes:.2f}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK
            )
            
            self.lucro_dia = ft.Text(
                value=f"MT {lucro_dia:.2f}",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK
            )
            
            # Forçar atualização da UI
            print("Atualizando UI após reconstrução dos cards...")
            self.update()
            if hasattr(self, 'page') and self.page:
                self.page.update()
            
            print("Reconstrução dos cards concluída com sucesso")
        except Exception as e:
            print(f"Erro ao reconstruir cards: {e}")

    def did_mount(self):
        print("\n=== Debug did_mount() ===")
        try:
            # Verificar se precisa resetar os valores para funcionários
            resetar = self.page.data.get('reset_dashboard_values', False)
            print(f"Verificando reset_dashboard_values: {resetar}")
            
            # Se houver flag de reset, forçar reconstrução dos cards
            if resetar:
                print("Flag de reset encontrada - reconstruindo cards...")
                self._force_rebuild_cards(resetar=True)
                # Remover a flag após processar
                self.page.data.pop('reset_dashboard_values', None)
                # Forçar atualização da UI
                self.update()
                if hasattr(self, 'page') and self.page:
                    self.page.update()
                return
            
            # Verificar se o dashboard precisa ser atualizado
            if hasattr(self.page, 'data') and self.page.data.get('dashboard_needs_update'):
                print("Dashboard marcado para atualização - recalculando valores...")
                self.page.data['dashboard_needs_update'] = False  # Resetar flag
                
                # Forçar reconstrução completa dos cards
                self._force_rebuild_cards(resetar=False)
                
                # Forçar atualização da UI
                self.update()
                if hasattr(self, 'page') and self.page:
                    self.page.update()
            
            # Atualizar valores com a flag de reset
            self.atualizar_valores(resetar=resetar)
            
            # Limpar flag de reset se existir
            if 'reset_dashboard_values' in self.page.data:
                print("Removendo flag reset_dashboard_values")
                del self.page.data['reset_dashboard_values']
                
            print("=== Fim did_mount() ===\n")
            
            # Iniciar monitoramento de conexão
            self.status_indicator.start_monitoring()

            # Se estiver em modo web, buscar números do backend para os cards (em thread)
            try:
                if self._is_web():
                    import threading
                    threading.Thread(target=self._fetch_web_dashboard_numbers_sync, daemon=True).start()
            except Exception as _:
                pass
            
        except Exception as e:
            print(f"Erro no did_mount: {e}")
