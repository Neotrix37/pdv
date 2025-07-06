import flet as ft
from database.database import Database
from datetime import datetime, date
import locale
from utils.translation_mixin import TranslationMixin

class DespesasView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.BLUE_50
        self.usuario = usuario
        self.db = Database()
        locale.setlocale(locale.LC_ALL, 'pt_PT.UTF-8')

        # Buscar categorias do banco de dados
        self.categorias = [
            categoria['nome'] for categoria in 
            self.db.fetchall("SELECT nome FROM categorias_despesa WHERE 1 ORDER BY nome")
        ]

        # Campos do formulário com cores ajustadas
        self.tipo_despesa = ft.Dropdown(
            label="Tipo de Despesa",
            width=200,
            options=[
                ft.dropdown.Option("Fixa"),
                ft.dropdown.Option("Variável")
            ],
            value="Fixa"
        )

        self.categoria = ft.Dropdown(
            label="Categoria",
            width=200,
            options=[ft.dropdown.Option(cat) for cat in self.categorias]
        )

        self.descricao = ft.TextField(
            label="Descrição",
            width=400,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLUE_900),
            border_color=ft.colors.BLUE_900,
            focused_border_color=ft.colors.BLUE_900,
            cursor_color=ft.colors.BLUE_900
        )

        self.valor = ft.TextField(
            label="Valor",
            width=200,
            prefix_text="MT ",
            keyboard_type=ft.KeyboardType.NUMBER,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLUE_900),
            border_color=ft.colors.BLUE_900,
            focused_border_color=ft.colors.BLUE_900,
            cursor_color=ft.colors.BLUE_900
        )

        self.data_vencimento = ft.TextField(
            label="Data de Vencimento",
            width=200,
            value=date.today().strftime("%Y-%m-%d"),
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLUE_900),
            border_color=ft.colors.BLUE_900,
            focused_border_color=ft.colors.BLUE_900,
            cursor_color=ft.colors.BLUE_900
        )

        self.status = ft.Dropdown(
            label="Status",
            width=200,
            options=[
                ft.dropdown.Option("Pendente"),
                ft.dropdown.Option("Pago")
            ],
            value="Pendente"
        )

        # Adicionar filtros
        self.filtro_status = ft.Dropdown(
            label="Filtrar por Status",
            width=200,
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Pendente"),
                ft.dropdown.Option("Pago")
            ],
            value="Todos",
            on_change=self.aplicar_filtros
        )

        self.filtro_tipo = ft.Dropdown(
            label="Filtrar por Tipo",
            width=200,
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Fixa"),
                ft.dropdown.Option("Variável")
            ],
            value="Todos",
            on_change=self.aplicar_filtros
        )

        # Tabela de despesas com cores ajustadas
        self.despesas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Tipo", color=ft.colors.BLACK, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Categoria", color=ft.colors.BLACK, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Descrição", color=ft.colors.BLACK, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor", color=ft.colors.BLACK, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Vencimento", color=ft.colors.BLACK, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", color=ft.colors.BLACK, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK, weight=ft.FontWeight.BOLD))
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.BLUE_900),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.colors.BLUE_200),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.BLUE_200),
            heading_row_color=ft.colors.BLUE_50,
            heading_row_height=70
        )

        # Carregar despesas iniciais
        self.carregar_despesas()

    def salvar_despesa(self, e):
        try:
            dados = {
                'tipo': self.tipo_despesa.value,
                'categoria': self.categoria.value,
                'descricao': self.descricao.value,
                'valor': float(self.valor.value.replace('MT ', '').replace(',', '.')),
                'data_vencimento': self.data_vencimento.value,
                'status': self.status.value
            }

            self.db.execute("""
                INSERT INTO despesas_recorrentes 
                (tipo, categoria, descricao, valor, data_vencimento, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dados['tipo'],
                dados['categoria'],
                dados['descricao'],
                dados['valor'],
                dados['data_vencimento'],
                dados['status']
            ))

            self.limpar_formulario()
            self.carregar_despesas()
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Despesa salva com sucesso!"))
            )

        except Exception as e:
            print(f"Erro ao salvar despesa: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Erro ao salvar despesa!"))
            )

    def carregar_despesas(self):
        try:
            despesas = self.db.fetchall("""
                SELECT * FROM despesas_recorrentes
                ORDER BY data_vencimento DESC
            """)

            self.despesas_table.rows.clear()
            for despesa in despesas:
                self.despesas_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(despesa['tipo'], color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(despesa['categoria'], color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(despesa['descricao'], color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(f"MT {despesa['valor']:.2f}", color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(despesa['data_vencimento'], color=ft.colors.BLACK)),
                            ft.DataCell(
                                ft.Text(
                                    despesa['status'],
                                    color=ft.colors.GREEN if despesa['status'] == 'Pago' else ft.colors.RED_600,
                                    weight=ft.FontWeight.BOLD
                                )
                            ),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.EDIT,
                                        icon_color=ft.colors.BLUE_900,
                                        tooltip="Editar",
                                        data=despesa,
                                        on_click=self.editar_despesa
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        icon_color=ft.colors.RED_900,
                                        tooltip="Excluir",
                                        data=despesa,
                                        on_click=self.confirmar_exclusao
                                    )
                                ])
                            )
                        ],
                        color=ft.colors.WHITE
                    )
                )
            self.update()

        except Exception as e:
            print(f"Erro ao carregar despesas: {e}")

    def editar_despesa(self, e):
        try:
            despesa = e.control.data
            
            # Preencher formulário com dados da despesa
            self.tipo_despesa.value = despesa['tipo']
            self.categoria.value = despesa['categoria']
            self.descricao.value = despesa['descricao']
            self.valor.value = str(despesa['valor'])
            self.data_vencimento.value = despesa['data_vencimento']
            self.status.value = despesa['status']
            
            # Criar botão de atualização
            btn_atualizar = ft.ElevatedButton(
                "Atualizar",
                on_click=lambda x: self.atualizar_despesa(despesa['id'])
            )
            
            # Dialog de edição
            dlg_modal = ft.AlertDialog(
                modal=True,
                title=ft.Text("Editar Despesa"),
                content=ft.Column([
                    self.tipo_despesa,
                    self.categoria,
                    self.descricao,
                    self.valor,
                    self.data_vencimento,
                    self.status,
                    ft.Row([
                        btn_atualizar,
                        ft.OutlinedButton("Cancelar", on_click=lambda x: self.fechar_dialogo(dlg_modal))
                    ])
                ]),
                actions=[]
            )
            
            self.page.dialog = dlg_modal
            dlg_modal.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao editar despesa: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Erro ao editar despesa!"))
            )

    def atualizar_despesa(self, despesa_id):
        try:
            dados = {
                'tipo': self.tipo_despesa.value,
                'categoria': self.categoria.value,
                'descricao': self.descricao.value,
                'valor': float(self.valor.value.replace('MT ', '').replace(',', '.')),
                'data_vencimento': self.data_vencimento.value,
                'status': self.status.value,
                'data_pagamento': datetime.now().strftime("%Y-%m-%d") if self.status.value == "Pago" else None,
                'id': despesa_id
            }
            
            self.db.execute("""
                UPDATE despesas_recorrentes 
                SET tipo = ?, categoria = ?, descricao = ?, 
                    valor = ?, data_vencimento = ?, status = ?,
                    data_pagamento = ?
                WHERE id = ?
            """, (
                dados['tipo'],
                dados['categoria'],
                dados['descricao'],
                dados['valor'],
                dados['data_vencimento'],
                dados['status'],
                dados['data_pagamento'],
                dados['id']
            ))
            
            # Fechar diálogo e atualizar lista
            self.page.dialog.open = False
            self.page.update()
            self.carregar_despesas()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Despesa atualizada com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
        except Exception as e:
            print(f"Erro ao atualizar despesa: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Erro ao atualizar despesa!"))
            )

    def limpar_formulario(self):
        """Limpa todos os campos do formulário"""
        self.tipo_despesa.value = "Fixa"
        self.categoria.value = None
        self.descricao.value = ""
        self.valor.value = ""
        self.data_vencimento.value = date.today().strftime("%Y-%m-%d")
        self.status.value = "Pendente"
        self.update()

    def confirmar_exclusao(self, e):
        try:
            despesa = e.control.data
            
            def excluir_despesa(e):
                try:
                    self.db.execute(
                        "DELETE FROM despesas_recorrentes WHERE id = ?",
                        (despesa['id'],)
                    )
                    
                    # Fechar diálogo e atualizar lista
                    dlg_modal.open = False
                    self.page.update()
                    self.carregar_despesas()
                    
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Despesa excluída com sucesso!"),
                            bgcolor=ft.colors.GREEN
                        )
                    )
                    
                except Exception as e:
                    print(f"Erro ao excluir despesa: {e}")
                    self.page.show_snack_bar(
                        ft.SnackBar(content=ft.Text("Erro ao excluir despesa!"))
                    )
            
            # Diálogo de confirmação
            dlg_modal = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar Exclusão"),
                content=ft.Text("Tem certeza que deseja excluir esta despesa?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda x: self.fechar_dialogo(dlg_modal)),
                    ft.TextButton("Excluir", on_click=excluir_despesa)
                ]
            )
            
            self.page.dialog = dlg_modal
            dlg_modal.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao confirmar exclusão: {e}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Erro ao processar exclusão!"))
            )

    def fechar_dialogo(self, dlg):
        """Fecha um diálogo e atualiza a página"""
        dlg.open = False
        self.page.update()

    def aplicar_filtros(self, e):
        try:
            query = """
                SELECT * FROM despesas_recorrentes
                WHERE 1=1
            """
            params = []

            if self.filtro_status.value != "Todos":
                query += " AND status = ?"
                params.append(self.filtro_status.value)

            if self.filtro_tipo.value != "Todos":
                query += " AND tipo = ?"
                params.append(self.filtro_tipo.value)

            query += " ORDER BY data_vencimento DESC"

            despesas = self.db.fetchall(query, tuple(params))
            self.atualizar_tabela_despesas(despesas)

        except Exception as e:
            print(f"Erro ao aplicar filtros: {e}")

    def atualizar_tabela_despesas(self, despesas):
        self.despesas_table.rows.clear()
        for despesa in despesas:
            self.despesas_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(despesa['tipo'], color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(despesa['categoria'], color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(despesa['descricao'], color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(f"MT {despesa['valor']:.2f}", color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(despesa['data_vencimento'], color=ft.colors.BLACK)),
                        ft.DataCell(
                            ft.Text(
                                despesa['status'],
                                color=ft.colors.GREEN if despesa['status'] == 'Pago' else ft.colors.RED_600,
                                weight=ft.FontWeight.BOLD
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    icon_color=ft.colors.BLUE_900,
                                    tooltip="Editar",
                                    data=despesa,
                                    on_click=self.editar_despesa
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=ft.colors.RED_900,
                                    tooltip="Excluir",
                                    data=despesa,
                                    on_click=self.confirmar_exclusao
                                )
                            ])
                        )
                    ]
                )
            )
        self.update()

    def build(self):
        return ft.Column([
            # Cabeçalho com cores ajustadas
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/dashboard"),
                        icon_color=ft.colors.BLUE_900
                    ),
                    ft.Text(
                        "Gestão de Despesas",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    )
                ]),
                padding=20
            ),

            # Formulário com fundo branco para melhor contraste
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Nova Despesa",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    ),
                    ft.Row([
                        self.tipo_despesa,
                        self.categoria,
                        self.valor
                    ]),
                    ft.Row([
                        self.descricao,
                        self.data_vencimento,
                        self.status
                    ]),
                    ft.Row([
                        ft.ElevatedButton(
                            "Salvar",
                            on_click=self.salvar_despesa,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.GREEN,
                                color=ft.colors.WHITE
                            )
                        ),
                        ft.OutlinedButton(
                            "Limpar",
                            on_click=lambda _: self.limpar_formulario(),
                            style=ft.ButtonStyle(
                                color=ft.colors.BLUE_900
                            )
                        )
                    ])
                ]),
                padding=20,
                bgcolor=ft.colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color=ft.colors.with_opacity(0.25, ft.colors.BLACK)
                )
            ),

            # Filtros
            ft.Container(
                content=ft.Row([
                    self.filtro_status,
                    self.filtro_tipo
                ]),
                padding=20,
                bgcolor=ft.colors.WHITE,
                border_radius=10
            ),

            # Tabela com fundo branco
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Despesas Cadastradas",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900
                    ),
                    self.despesas_table
                ]),
                padding=20,
                bgcolor=ft.colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color=ft.colors.with_opacity(0.25, ft.colors.BLACK)
                )
            )
        ])