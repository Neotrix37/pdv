import flet as ft
from datetime import datetime
from database.database import Database
from utils.translations import get_text
from utils.translation_mixin import TranslationMixin

class DashboardView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.BLUE_50
        self.usuario = usuario
        self.db = Database()
        self.lang = page.data.get("language", "pt")
        
        # Inicializar os textos dos valores
        self.vendas_mes = ft.Text(
            value="MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.lucro_mes = ft.Text(
            value="MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.vendas_dia = ft.Text(
            value="MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.vendas_congelador = ft.Text(
            value="MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        # Adicionar novos textos para valor do estoque e valor potencial
        self.valor_estoque = ft.Text(
            value="MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.valor_potencial = ft.Text(
            value="MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )

    def build(self):
        # Força recálculo dos valores
        total_vendas_mes = self.db.get_total_vendas_mes()
        lucro_mes = self.get_lucro_mes()
        total_vendas_dia = self.db.get_total_vendas_hoje()
        total_vendas_congelador = self.db.get_total_vendas_congelador_hoje()
        valor_estoque = self.db.get_valor_estoque()
        valor_potencial = self.db.get_valor_venda_estoque()

        # Atualizar os textos com os valores
        self.vendas_mes.value = f"MT {total_vendas_mes:.2f}"
        self.lucro_mes.value = f"MT {lucro_mes:.2f}"
        self.vendas_dia.value = f"MT {total_vendas_dia:.2f}"
        self.vendas_congelador.value = f"MT {total_vendas_congelador:.2f}"
        self.valor_estoque.value = f"MT {valor_estoque:.2f}"
        self.valor_potencial.value = f"MT {valor_potencial:.2f}"

        # Criar os cards com os valores atualizados
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
            content=ft.Column(
                [
                    ft.Text(
                        "Vendas Congelador (Hoje)",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLACK
                    ),
                    self.vendas_congelador
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
                        f"{self.t('welcome')}, {self.usuario['nome']}!",
                        size=16,
                        color=ft.colors.WHITE
                    ),
                    ft.Container(expand=True),  # Espaçador flexível
                    ft.IconButton(
                        icon=ft.icons.LOGOUT,
                        icon_color=ft.colors.WHITE,
                        tooltip="Sair",
                        on_click=lambda _: self.sair()
                    )
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
        ]
        
        if self.usuario.get('is_admin'):
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
                        "Gestão de Despesas",
                        icon=ft.icons.MONEY_OFF,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.RED
                        ),
                        on_click=lambda _: self.page.go("/despesas")
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
                ),
                # Novo botão para Gráficos
                ft.Container(
                    content=ft.ElevatedButton(
                        "Gráficos",
                        icon=ft.icons.BAR_CHART,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.PURPLE_700
                        ),
                        on_click=lambda _: self.page.go("/graficos")
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
                    self.get_stats_cards(),
                    ft.Container(height=20),
                    self.get_tables_row()
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=20
        )

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

            # Buscar valor total em estoque e valor potencial apenas para admin
            if self.usuario.get('is_admin'):
                valor_estoque = self.db.get_valor_estoque()
                valor_potencial = self.db.get_valor_venda_estoque()
                lucro_mes = self.db.get_lucro_mes()
            
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
                                self.t("profit_month"),
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
                JOIN usuarios u ON v.usuario_id = u.id
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
        produtos_baixo_estoque = self.db.fetchall("""
            SELECT 
                codigo,
                nome,
                estoque,
                estoque_minimo
            FROM produtos
            WHERE estoque <= estoque_minimo
                AND ativo = 1
            ORDER BY estoque ASC
            LIMIT 5
        """)

        estoque_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Produto", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Estoque", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Mínimo", color=ft.colors.GREY_900))
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p['codigo'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(p['nome'], color=ft.colors.GREY_900)),
                        ft.DataCell(
                            ft.Text(
                                str(p['estoque']),
                                color=ft.colors.RED if p['estoque'] <= p['estoque_minimo'] else ft.colors.GREY_900
                            )
                        ),
                        ft.DataCell(ft.Text(str(p['estoque_minimo']), color=ft.colors.GREY_900))
                    ]
                ) for p in produtos_baixo_estoque
            ]
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
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Produtos com Estoque Baixo",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLACK
                        ),
                        ft.Container(
                            content=ft.Column(
                                [estoque_table],
                                scroll=ft.ScrollMode.AUTO
                            ),
                            height=270,  # Mesma altura da tabela de vendas
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
                )
            ]
        )
    def sair(self):
        # Limpa os dados da sessão
        self.page.data.clear()
        # Volta para a tela de login
        self.page.go("/")

    def ir_para_clientes(self, e):
        self.page.go("/clientes")

    def atualizar_valores(self):
        """Atualiza os valores mostrados nos cards"""
        print("\n=== ATUALIZANDO VALORES DO DASHBOARD ===")
        
        total_vendas_mes = self.db.get_total_vendas_mes()
        lucro_mes = self.get_lucro_mes()
        total_vendas_dia = self.db.get_total_vendas_hoje()
        total_vendas_congelador = self.db.get_total_vendas_congelador_hoje()
        valor_estoque = self.db.get_valor_estoque()
        valor_potencial = self.db.get_valor_venda_estoque()

        print(f"Total vendas mês: MT {total_vendas_mes:.2f}")
        print(f"Lucro mês: MT {lucro_mes:.2f}")
        print(f"Total vendas dia: MT {total_vendas_dia:.2f}")
        print(f"Vendas congelador: MT {total_vendas_congelador:.2f}")
        print(f"Valor em estoque: MT {valor_estoque:.2f}")
        print(f"Valor potencial: MT {valor_potencial:.2f}")

        self.vendas_mes.value = f"MT {total_vendas_mes:.2f}"
        self.lucro_mes.value = f"MT {lucro_mes:.2f}"
        self.vendas_dia.value = f"MT {total_vendas_dia:.2f}"
        self.vendas_congelador.value = f"MT {total_vendas_congelador:.2f}"
        self.valor_estoque.value = f"MT {valor_estoque:.2f}"
        self.valor_potencial.value = f"MT {valor_potencial:.2f}"

        self.update()
        print("=== VALORES DO DASHBOARD ATUALIZADOS ===\n")

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

    def did_mount(self):
        print("\n=== Debug did_mount() ===")
        self.atualizar_valores()
        print("=== Fim did_mount() ===\n")

