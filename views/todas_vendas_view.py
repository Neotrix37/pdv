import flet as ft
from database.database import Database
import locale
from datetime import datetime
from views.generic_table_style import apply_table_style

class TodasVendasView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.BLUE_50
        self.usuario = usuario
        self.db = Database()
        locale.setlocale(locale.LC_ALL, 'pt_PT.UTF-8')
        
        # Inicializar o texto de resumo antes de carregar vendas
        self.resumo_text = ft.Text(
            "Carregando...",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE
        )
        
        # Campo de busca e filtros
        self.data_inicial = ft.TextField(
            label="Data Inicial",
            width=200,
            height=50,
            value=datetime.now().strftime("%Y-%m-%d"),
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.data_final = ft.TextField(
            label="Data Final",
            width=200,
            height=50,
            value=datetime.now().strftime("%Y-%m-%d"),
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Dropdown de usuários
        self.usuarios = self.db.fetchall("SELECT id, nome FROM usuarios WHERE ativo = 1")
        self.usuario_dropdown = ft.Dropdown(
            label="Vendedor",
            width=300,
            options=[
                ft.dropdown.Option("todos", "Todos os Vendedores"),
                *[ft.dropdown.Option(str(u['id']), u['nome']) for u in self.usuarios]
            ]
        )
        self.usuario_dropdown.value = "todos"
        
        # Campo de busca de produtos
        self.busca_produto = ft.TextField(
            label="Buscar produto",
            hint_text="Digite o nome do produto...",
            width=300,
            expand=True,
            border_color=ft.colors.BLUE_GREY_300,
            label_style=ft.TextStyle(color=ft.colors.BLUE_GREY_700),
            on_change=self.filtrar_por_produto
        )
        self.vendas_originais = []  # Armazenará os dados originais para filtragem
        
        # Tabela de vendas
        self.vendas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Vendedor")),
                ft.DataColumn(ft.Text("Data")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("Forma Pagamento")),
                ft.DataColumn(ft.Text("Itens"))
            ],
            rows=[]
        )
        apply_table_style(self.vendas_table)
        
        # Carregar vendas iniciais
        self.carregar_vendas()

    def filtrar_por_produto(self, e):
        termo_busca = self.busca_produto.value.lower()
        
        if not termo_busca:
            # Se o campo de busca estiver vazio, mostra todas as vendas
            self.vendas_table.rows = self.vendas_originais
        else:
            # Filtra as linhas que contêm o termo de busca na coluna de itens
            linhas_filtradas = []
            for row in self.vendas_originais:
                itens = row.cells[5].content.value.lower()  # Índice 5 é a coluna de Itens
                if termo_busca in itens:
                    linhas_filtradas.append(row)
            self.vendas_table.rows = linhas_filtradas
        
        self.vendas_table.update()

    def carregar_vendas(self, e=None):
        try:
            params = [self.data_inicial.value, self.data_final.value]
            where_clause = "WHERE DATE(v.data_venda) BETWEEN ? AND ?"
            
            # Adiciona filtro por usuário se um usuário específico for selecionado
            if self.usuario_dropdown.value and self.usuario_dropdown.value != "todos":
                where_clause += " AND v.usuario_id = ?"
                params.append(self.usuario_dropdown.value)

            vendas = self.db.fetchall(f"""
                SELECT 
                    v.id,
                    u.nome as vendedor,
                    DATE(v.data_venda) as data,
                    TIME(v.data_venda) as hora,
                    v.total,
                    v.forma_pagamento,
                    v.status,
                    GROUP_CONCAT(
                        p.nome || ' (' || iv.quantidade || 'x - MT ' || 
                        printf('%.2f', iv.preco_unitario) || ')'
                    ) as itens
                FROM vendas v
                JOIN usuarios u ON u.id = v.usuario_id
                JOIN itens_venda iv ON iv.venda_id = v.id
                JOIN produtos p ON p.id = iv.produto_id
                {where_clause}
                AND (v.status IS NULL OR v.status != 'Anulada')
                GROUP BY v.id
                ORDER BY v.data_venda DESC
            """, tuple(params))

            # Calcular totais por vendedor
            totais_vendedor = {}
            for v in vendas:
                if v['vendedor'] not in totais_vendedor:
                    totais_vendedor[v['vendedor']] = 0
                totais_vendedor[v['vendedor']] += v['total']

            # Armazenar os dados originais e limpar a tabela
            self.vendas_table.rows.clear()
            self.vendas_originais = []
            
            for v in vendas:
                cor = ft.colors.RED if v['status'] == 'Fechada' else ft.colors.GREY_900
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(v['id']), color=cor)),
                        ft.DataCell(ft.Text(v['vendedor'], color=cor)),
                        ft.DataCell(ft.Text(f"{v['data']} {v['hora']}", color=cor)),
                        ft.DataCell(ft.Text(f"MT {v['total']:.2f}", color=cor)),
                        ft.DataCell(ft.Text(v['forma_pagamento'], color=cor)),
                        ft.DataCell(ft.Text(v['itens'], color=cor))
                    ]
                )
                self.vendas_table.rows.append(row)
                self.vendas_originais.append(row)

            # Atualizar resumo
            resumo = ["Resumo por Vendedor:"]
            total_geral = 0
            for vendedor, total in totais_vendedor.items():
                resumo.append(f"{vendedor}: MT {total:.2f}")
                total_geral += total
            resumo.append(f"\nTotal Geral: MT {total_geral:.2f}")
            
            self.resumo_text.value = "\n".join(resumo)
            self.update()

        except Exception as error:
            print(f"Erro ao carregar vendas: {error}")

    def build(self):
        # Cabeçalho
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/dashboard")
                ),
                ft.Icon(
                    name=ft.icons.SHOPPING_CART,
                    size=30,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Todas as Vendas",
                    size=20,
                    color=ft.colors.WHITE
                )
            ]),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.INDIGO_900, ft.colors.INDIGO_700]
            ),
            padding=20,
            border_radius=10
        )

        # Filtros
        filtros = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.data_inicial,
                    self.data_final,
                    self.usuario_dropdown,
                    ft.ElevatedButton(
                        "Filtrar",
                        icon=ft.icons.FILTER_ALT,
                        on_click=self.carregar_vendas
                    )
                ]),
                self.resumo_text
            ]),
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10
        )

        # Container da tabela
        table_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Todas as Vendas",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE,
                        expand=True
                    ),
                    self.busca_produto
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column(
                        [self.vendas_table],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    height=400,  # Altura fixa para o container
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
            )
        )

        return ft.Column([
            header,
            ft.Container(height=20),
            filtros,
            ft.Container(height=20),
            table_container
        ]) 