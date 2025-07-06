import flet as ft
from database.database import Database
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style

class DividasView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        
        # Lista para armazenar itens da dívida atual
        self.itens_divida = []
        self.total_divida = 0
        self.valor_original = 0.0
        self.desconto_aplicado = 0.0
        self.percentual_desconto = 0.0
        
        self.inicializar_campos()
        self.inicializar_tabelas()

    def inicializar_campos(self):
        # Dropdown de clientes
        self.cliente_dropdown = ft.Dropdown(
            label="Selecione o Cliente",
            width=400,
            height=50,
            text_size=14,
            color=ft.colors.WHITE,
            label_style=ft.TextStyle(color=ft.colors.WHITE),
            focused_border_color=ft.colors.BLUE,
            border_color=ft.colors.BLUE_400,
            bgcolor=ft.colors.BLUE_900,
            focused_color=ft.colors.BLACK,
            text_style=ft.TextStyle(color=ft.colors.BLACK),
            on_change=self.carregar_dividas_cliente
        )
        
        # Dropdown de produtos
        self.produto_dropdown = ft.Dropdown(
            label="Selecione o Produto",
            width=400,
            height=50,
            text_size=14,
            color=ft.colors.WHITE,
            label_style=ft.TextStyle(color=ft.colors.WHITE),
            focused_border_color=ft.colors.BLUE,
            border_color=ft.colors.BLUE_400,
            bgcolor=ft.colors.BLUE_900,
            focused_color=ft.colors.BLACK,
            text_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Campo de quantidade
        self.quantidade_field = ft.TextField(
            label="Quantidade",
            width=150,
            height=50,
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            focused_border_color=ft.colors.BLUE,
            border_color=ft.colors.BLUE_400
        )
        
        # Campo de observação
        self.observacao_field = ft.TextField(
            label="Observação",
            width=400,
            height=50,
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            focused_border_color=ft.colors.BLUE,
            border_color=ft.colors.BLUE_400
        )
        
        # Campo para mostrar informações do desconto
        self.info_desconto = ft.Text(
            "",
            size=14,
            color=ft.colors.GREEN,
            weight=ft.FontWeight.BOLD,
            visible=False
        )
        
        # Campo para mostrar o total da dívida
        self.total_text = ft.Text(
            f"Total: MT {self.total_divida:.2f}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )

    def inicializar_tabelas(self):
        # Tabela de itens da dívida atual
        self.itens_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Produto", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Quantidade", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Preço Unit.", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Subtotal", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK)),
            ],
            rows=[]
        )
        apply_table_style(self.itens_table)
        
        # Tabela de dívidas do cliente
        self.dividas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Data", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Valor Total", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Valor Pago", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Saldo", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Status", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK)),
            ],
            rows=[]
        )
        apply_table_style(self.dividas_table)

    def build(self):
        # Header com cores padrão (azul)
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/dashboard"),
                    icon_color=ft.colors.WHITE
                ),
                ft.Icon(
                    name=ft.icons.ACCOUNT_BALANCE_WALLET,
                    size=30,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Gestão de Dívidas",
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

        # Nova Dívida
        nova_divida = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Nova Dívida",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLACK
                ),
                ft.Row([self.cliente_dropdown]),
                self.info_desconto,
                ft.Row([
                    self.produto_dropdown,
                    self.quantidade_field,
                    ft.ElevatedButton(
                        "Adicionar Item",
                        icon=ft.icons.ADD,
                        on_click=self.adicionar_item
                    )
                ]),
                ft.Container(
                    content=self.itens_table,
                    height=200,
                    border=ft.border.all(1, ft.colors.BLACK26),
                    border_radius=10,
                    padding=10
                ),
                self.observacao_field,
                ft.Row([
                    self.total_text,
                    ft.ElevatedButton(
                        "Salvar Dívida",
                        icon=ft.icons.SAVE,
                        on_click=self.salvar_divida
                    )
                ])
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

        # Lista de Dívidas
        self.dividas_container = ft.Container(
            content=ft.Column(
                [self.dividas_table],
                scroll=ft.ScrollMode.ALWAYS,
                expand=True
            ),
            height=250,
            border=ft.border.all(1, ft.colors.BLACK26),
            border_radius=10,
            padding=10,
            bgcolor=ft.colors.WHITE
        )

        lista_dividas = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Dívidas do Cliente",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLACK
                ),
                self.dividas_container
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

        # Adicione este botão junto aos outros controles
        mostrar_todas = ft.ElevatedButton(
            "Mostrar Todas as Dívidas",
            icon=ft.icons.LIST_ALT,
            on_click=self.carregar_todas_dividas
        )

        return ft.Column(
            controls=[
                header,
                ft.Container(height=20),
                nova_divida,
                ft.Container(height=20),
                lista_dividas,
                ft.Container(height=20),
                mostrar_todas
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )

    def did_mount(self):
        self.carregar_clientes()
        self.carregar_produtos()

    def carregar_clientes(self):
        try:
            clientes = self.db.fetchall("""
                SELECT id, nome, nuit 
                FROM clientes 
                ORDER BY nome
            """)
            
            self.cliente_dropdown.options = [
                ft.dropdown.Option(
                    key=str(c['id']),
                    text=f"{c['nome']} ({c['nuit'] or 'Sem NUIT'})"
                ) for c in clientes
            ]
            self.update()
        except Exception as ex:
            print(f"Erro ao carregar clientes: {ex}")

    def carregar_produtos(self):
        try:
            produtos = self.db.fetchall("""
                SELECT id, codigo, nome, descricao, preco_venda, estoque, venda_por_peso, unidade_medida
                FROM produtos 
                WHERE ativo = 1
                ORDER BY nome
            """)
            
            self.produto_dropdown.options = [
                ft.dropdown.Option(
                    key=str(p['id']),
                    text=f"{p['nome']} | {p['descricao'] or '-'} | Estoque: {p['estoque']}{' KG' if p['venda_por_peso'] else ' un'} | MT {p['preco_venda']:.2f}{'/KG' if p['venda_por_peso'] else ''}"
                ) for p in produtos
            ]
            self.update()
        except Exception as ex:
            print(f"Erro ao carregar produtos: {ex}")

    def carregar_dividas_cliente(self, e):
        if not self.cliente_dropdown.value:
            return
        
        try:
            # Busca informações do cliente incluindo se é especial
            cliente = self.db.fetchone("""
                SELECT nome, especial, desconto_divida FROM clientes WHERE id = ?
            """, (self.cliente_dropdown.value,))
            
            # Verifica se o cliente é especial e aplica o desconto
            if cliente and cliente['especial'] and cliente['desconto_divida']:
                self.percentual_desconto = cliente['desconto_divida']
                self.info_desconto.value = f"🎯 Cliente especial: desconto de {self.percentual_desconto * 100:.1f}% aplicado"
                self.info_desconto.visible = True
                self.info_desconto.color = ft.colors.GREEN
            else:
                self.percentual_desconto = 0.0
                self.info_desconto.visible = False
            
            # Busca as dívidas com JOIN para obter o nome do cliente
            dividas = self.db.fetchall("""
                SELECT 
                    d.id,
                    d.data_divida,
                    d.valor_total,
                    d.valor_original,
                    d.desconto_aplicado,
                    d.percentual_desconto,
                    d.valor_pago,
                    d.status,
                    d.observacao,
                    c.nome as cliente_nome
                FROM dividas d
                JOIN clientes c ON c.id = d.cliente_id
                WHERE d.cliente_id = ?
                ORDER BY d.data_divida DESC
            """, (self.cliente_dropdown.value,))
            
            # Recria a tabela com os novos dados
            self.dividas_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Data", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Valor Total", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Desconto", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Valor Pago", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Saldo", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Status", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK)),
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(d['data_divida'].split()[0])),
                            ft.DataCell(ft.Text(f"MT {d['valor_total']:.2f}", weight=ft.FontWeight.BOLD)),
                            ft.DataCell(
                                ft.Text(
                                    f"MT {d['desconto_aplicado']:.2f}",
                                    color=ft.colors.GREEN,
                                    weight=ft.FontWeight.BOLD
                                ) if d['desconto_aplicado'] and d['desconto_aplicado'] > 0 else ft.Text("-")
                            ),
                            ft.DataCell(ft.Text(f"MT {d['valor_pago']:.2f}")),
                            ft.DataCell(ft.Text(f"MT {(d['valor_total'] - d['valor_pago']):.2f}")),
                            ft.DataCell(ft.Text(d['status'])),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.PAYMENT,
                                        icon_color=ft.colors.GREY if d['status'] == 'Quitado' else ft.colors.GREEN,
                                        tooltip="Registrar Pagamento" if d['status'] != 'Quitado' else "Dívida já paga",
                                        data=d,
                                        on_click=(self.registrar_pagamento if d['status'] != 'Quitado' else lambda e: self.page.show_snack_bar(ft.SnackBar(content=ft.Text('Esta dívida já foi paga!'), bgcolor=ft.colors.BLUE))),
                                        disabled=False
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.VISIBILITY,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Ver Detalhes",
                                        data=d,
                                        on_click=self.ver_detalhes
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE_FOREVER,
                                        icon_color=ft.colors.RED,
                                        tooltip="Remover Dívida",
                                        data=d,
                                        on_click=self.confirmar_remocao_divida
                                    ) if d['status'] != 'Quitado' else ft.Container(width=0)
                                ])
                            )
                        ]
                    ) for d in dividas
                ]
            )
            
            # Aplica o estilo da tabela
            apply_table_style(self.dividas_table)
            
            # Atualiza o container da tabela
            if hasattr(self, 'dividas_container'):
                self.dividas_container.content = self.dividas_table
                self.dividas_container.update()
            
            self.update()
            
        except Exception as ex:
            print(f"Erro ao carregar dívidas: {ex}")
            import traceback
            print(traceback.format_exc())
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao carregar dívidas: {str(ex)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def adicionar_item(self, e):
        try:
            if not self.produto_dropdown.value:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Selecione o produto!"),
                        bgcolor=ft.colors.RED
                    )
                )
                return

            produto = self.db.fetchone("""
                SELECT id, nome, codigo, preco_venda, estoque, venda_por_peso, unidade_medida
                FROM produtos 
                WHERE id = ?
            """, (self.produto_dropdown.value,))
            
            if not produto:
                raise ValueError("Produto não encontrado!")
            
            # Se for produto vendido por peso, mostrar diálogo
            if produto['venda_por_peso'] == 1:
                self.mostrar_dialogo_venda_por_peso(produto)
            else:
                # Produto normal - usar quantidade
                if not self.quantidade_field.value:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Informe a quantidade!"),
                            bgcolor=ft.colors.RED
                        )
                    )
                    return
                
                quantidade = float(self.quantidade_field.value)
                if quantidade <= 0:
                    raise ValueError("Quantidade deve ser maior que zero!")
                    
                if quantidade > produto['estoque']:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Quantidade maior que o estoque disponível!"),
                            bgcolor=ft.colors.RED
                        )
                    )
                    return

                subtotal = quantidade * produto['preco_venda']
                
                # Adiciona à lista de itens
                self.itens_divida.append({
                    'produto_id': produto['id'],
                    'nome': produto['nome'],
                    'quantidade': quantidade,
                    'preco_unitario': produto['preco_venda'],
                    'subtotal': subtotal,
                    'peso_kg': 0,  # Produto não vendido por peso
                    'venda_por_peso': False
                })
                
                # Atualiza a tabela de itens
                self.atualizar_tabela_itens()
                
                # Limpa os campos
                self.produto_dropdown.value = None
                self.quantidade_field.value = ""
                
                # Atualiza os campos
                self.produto_dropdown.update()
                self.quantidade_field.update()
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("✅ Item adicionado com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            
        except Exception as ex:
            print(f"Erro ao adicionar item: {ex}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao adicionar item: {str(ex)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def atualizar_tabela_itens(self):
        try:
            self.itens_table.rows.clear()
            self.valor_original = 0
            
            for item in self.itens_divida:
                self.valor_original += item['subtotal']
                
                # Determinar a unidade de medida
                if item.get('venda_por_peso', False):
                    quantidade_text = f"{item['quantidade']:.3f} KG"
                    preco_text = f"MT {item['preco_unitario']:.2f}/KG"
                else:
                    quantidade_text = f"{item['quantidade']:.0f} un"
                    preco_text = f"MT {item['preco_unitario']:.2f}"
                
                self.itens_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(item['nome'])),
                            ft.DataCell(ft.Text(quantidade_text)),
                            ft.DataCell(ft.Text(preco_text)),
                            ft.DataCell(ft.Text(f"MT {item['subtotal']:.2f}")),
                            ft.DataCell(
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=ft.colors.RED,
                                    tooltip="Remover Item",
                                    data=item,
                                    on_click=self.remover_item
                                )
                            )
                        ]
                    )
                )
            
            # Calcula o desconto se aplicável
            if self.percentual_desconto > 0:
                self.desconto_aplicado = self.valor_original * self.percentual_desconto
                self.total_divida = self.valor_original - self.desconto_aplicado
            else:
                self.desconto_aplicado = 0
                self.total_divida = self.valor_original
            
            # Força a atualização da tabela
            self.itens_table.update()
            
            # Atualiza o texto do total
            if hasattr(self, 'total_text'):
                if self.percentual_desconto > 0:
                    self.total_text.value = f"Total Original: MT {self.valor_original:.2f} | Desconto: MT {self.desconto_aplicado:.2f} | Total Final: MT {self.total_divida:.2f}"
                else:
                    self.total_text.value = f"Total: MT {self.total_divida:.2f}"
                self.total_text.update()
            
            self.update()
            
        except Exception as ex:
            print(f"Erro ao atualizar tabela: {ex}")
            import traceback
            print(traceback.format_exc())

    def remover_item(self, e):
        try:
            item = e.control.data
            self.itens_divida.remove(item)
            self.atualizar_tabela_itens()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Item removido com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
        except Exception as ex:
            print(f"Erro ao remover item: {ex}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao remover item: {str(ex)}"),
                    bgcolor=ft.colors.RED
                            )
        )

    def mostrar_dialogo_venda_por_peso(self, produto):
        """Mostra diálogo para produtos vendidos por peso"""
        
        def close_dialog(e):
            self.page.dialog.open = False
            self.page.update()

        def calcular_por_peso(e):
            try:
                peso = float(peso_field.value or 0)
                valor = peso * produto['preco_venda']
                valor_field.value = f"{valor:.2f}"
                peso_calculado_text.value = f"Peso: {peso:.3f} KG"
                self.page.update()
            except ValueError:
                valor_field.value = "0.00"
                peso_calculado_text.value = "Peso: 0.000 KG"
                self.page.update()

        def calcular_por_valor(e):
            try:
                valor = float(valor_field.value or 0)
                peso = valor / produto['preco_venda']
                peso_field.value = f"{peso:.3f}"
                peso_calculado_text.value = f"Peso: {peso:.3f} KG"
                self.page.update()
            except ValueError:
                peso_field.value = "0.000"
                peso_calculado_text.value = "Peso: 0.000 KG"
                self.page.update()

        def confirmar_venda(e):
            try:
                valor = float(valor_field.value or 0)
                peso = float(peso_field.value or 0)
                
                if valor <= 0 or peso <= 0:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Valor ou peso inválido!"),
                            bgcolor=ft.colors.RED
                        )
                    )
                    return
                    
                if peso > produto['estoque']:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(f"Estoque insuficiente! Disponível: {produto['estoque']:.3f} KG"),
                            bgcolor=ft.colors.RED
                        )
                    )
                    return
                    
                # Adicionar ao carrinho
                self.itens_divida.append({
                    'produto_id': produto['id'],
                    'nome': produto['nome'],
                    'quantidade': peso,  # Peso em KG
                    'preco_unitario': produto['preco_venda'],  # Preço por KG
                    'subtotal': valor,
                    'peso_kg': peso,
                    'venda_por_peso': True
                })
                
                self.atualizar_tabela_itens()
                close_dialog(None)
                
                # Limpa os campos
                self.produto_dropdown.value = None
                self.produto_dropdown.update()
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("✅ Item adicionado com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
                
            except ValueError:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Valores inválidos!"),
                        bgcolor=ft.colors.RED
                    )
                )
        
        peso_field = ft.TextField(
            label="Peso (KG)",
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            on_change=calcular_por_peso,
            suffix_text="KG"
        )
        
        valor_field = ft.TextField(
            label="Valor (MT)",
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            on_change=calcular_por_valor,
            prefix_text="MT ",
            autofocus=True  # Foco inicial no campo de valor
        )
        
        peso_calculado_text = ft.Text(
            "Peso: 0.000 KG",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_900
        )
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text(
                "Venda por Peso",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK
            ),
            content=ft.Container(
                content=ft.Column([
                    # Informações do produto
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                produto['nome'],
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLACK
                            ),
                            ft.Text(
                                f"Código: {produto['codigo']}",
                                color=ft.colors.BLACK
                            ),
                        ]),
                        bgcolor=ft.colors.BLUE_50,
                        padding=10,
                        border_radius=5
                    ),
                    
                    # Preço e estoque
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        "Preço/KG",
                                        color=ft.colors.BLACK,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        f"MT {produto['preco_venda']:.2f}",
                                        size=20,
                                        color=ft.colors.GREEN
                                    )
                                ]),
                                padding=10
                            ),
                            ft.VerticalDivider(),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        "Estoque",
                                        color=ft.colors.BLACK,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        f"{produto['estoque']:.3f} KG",
                                        size=20,
                                        color=ft.colors.BLUE
                                    )
                                ]),
                                padding=10
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND),
                        bgcolor=ft.colors.BLUE_50,
                        padding=10,
                        border_radius=5
                    ),
                    
                    # Campos de entrada
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Digite o valor OU o peso:",
                                size=16,
                                color=ft.colors.BLACK,
                                weight=ft.FontWeight.BOLD
                            ),
                            valor_field,
                            peso_field,
                            peso_calculado_text
                        ], spacing=10),
                        padding=20
                    )
                ], spacing=20),
                padding=10
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=close_dialog,
                    style=ft.ButtonStyle(
                        color=ft.colors.RED
                    )
                ),
                ft.TextButton(
                    "Confirmar",
                    on_click=confirmar_venda,
                    style=ft.ButtonStyle(
                        color=ft.colors.GREEN
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog.open = True
        self.page.update()

    def salvar_divida(self, e):
        try:
            print("\n=== INICIANDO SALVAMENTO DE DÍVIDA ===")
            
            if not self.cliente_dropdown.value:
                raise ValueError("Selecione um cliente!")
            
            if not self.itens_divida:
                raise ValueError("Adicione pelo menos um item!")
            
            print(f"Cliente ID: {self.cliente_dropdown.value}")
            print(f"Total da dívida: {self.total_divida}")
            print(f"Valor original: {self.valor_original}")
            print(f"Desconto aplicado: {self.desconto_aplicado}")
            print(f"Percentual desconto: {self.percentual_desconto}")
            print(f"Número de itens: {len(self.itens_divida)}")
            
            # Insere a dívida
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO dividas (
                    cliente_id, valor_total, valor_original, desconto_aplicado, 
                    percentual_desconto, observacao, usuario_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.cliente_dropdown.value,
                self.total_divida,
                self.valor_original,
                self.desconto_aplicado,
                self.percentual_desconto,
                self.observacao_field.value,
                self.usuario['id'],
                'Pendente'
            ))
            
            divida_id = cursor.lastrowid
            print(f"Dívida criada com ID: {divida_id}")
            
            # Insere os itens e atualiza o estoque
            for i, item in enumerate(self.itens_divida):
                print(f"\n--- Processando item {i+1}/{len(self.itens_divida)} ---")
                print(f"Produto ID: {item['produto_id']}")
                print(f"Quantidade: {item['quantidade']}")
                print(f"Preço unitário: {item['preco_unitario']}")
                print(f"Subtotal: {item['subtotal']}")
                print(f"Peso KG: {item.get('peso_kg', 0)}")
                
                # Verificar estoque atual antes da atualização
                estoque_antes = self.db.fetchone("""
                    SELECT estoque, nome FROM produtos WHERE id = ?
                """, (item['produto_id'],))
                print(f"Estoque antes: {estoque_antes['estoque']} - {estoque_antes['nome']}")
                
                self.db.execute("""
                    INSERT INTO itens_divida (
                        divida_id, produto_id, quantidade,
                        preco_unitario, subtotal, peso_kg
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    divida_id,
                    item['produto_id'],
                    item['quantidade'],
                    item['preco_unitario'],
                    item['subtotal'],
                    item.get('peso_kg', 0)
                ))
                
                # Atualiza o estoque do produto
                self.db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item['quantidade'], item['produto_id'])
                )
                
                # Verificar estoque após a atualização
                estoque_depois = self.db.fetchone("""
                    SELECT estoque FROM produtos WHERE id = ?
                """, (item['produto_id'],))
                print(f"Estoque depois: {estoque_depois['estoque']}")
                print(f"Diferença: {estoque_antes['estoque'] - estoque_depois['estoque']}")
            
            # Commit das alterações
            self.db.conn.commit()
            
            # Limpa o formulário
            self.cliente_dropdown.value = None
            self.observacao_field.value = ""
            self.itens_divida.clear()
            self.percentual_desconto = 0.0
            self.valor_original = 0.0
            self.desconto_aplicado = 0.0
            self.info_desconto.visible = False
            self.atualizar_tabela_itens()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Dívida registrada com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
            # Recarrega as dívidas do cliente
            self.carregar_dividas_cliente(None)
            
        except Exception as error:
            print(f"Erro ao salvar dívida: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao salvar dívida: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def registrar_pagamento(self, e):
        divida = e.control.data
        
        def fechar_dialogo(e):
            dialog.open = False
            self.page.update()
        
        def confirmar_pagamento(e):
            try:
                print(f"\n=== REGISTRANDO PAGAMENTO DE DÍVIDA ===")
                print(f"Dívida ID: {divida['id']}")
                print(f"Valor total da dívida: {divida['valor_total']}")
                print(f"Valor já pago: {divida['valor_pago']}")
                
                if not valor_field.value or valor_field.value.strip() == "":
                    raise ValueError("Informe o valor do pagamento!")
                
                valor = float(valor_field.value)
                if valor <= 0:
                    raise ValueError("Valor deve ser maior que zero!")
                
                saldo = divida['valor_total'] - divida['valor_pago']
                print(f"Valor do pagamento: {valor}")
                print(f"Saldo devedor: {saldo}")
                
                # Usar tolerância para comparação de float
                if valor > saldo + 0.01:  # Tolerância de 1 centavo
                    raise ValueError(f"Valor maior que o saldo devedor! Saldo: MT {saldo:.2f}")
                
                # Registra o pagamento
                print(f"Registrando pagamento: {valor} - {forma_pagamento.value}")
                self.db.execute("""
                    INSERT INTO pagamentos_divida (
                        divida_id, valor, forma_pagamento, usuario_id
                    ) VALUES (?, ?, ?, ?)
                """, (divida['id'], valor, forma_pagamento.value, self.usuario['id']))
                
                # Atualiza o valor pago na dívida
                novo_valor_pago = divida['valor_pago'] + valor
                # Usar tolerância para determinar se a dívida foi quitada
                novo_status = 'Quitado' if novo_valor_pago >= divida['valor_total'] - 0.01 else 'Pendente'
                
                print(f"Novo valor pago: {novo_valor_pago}")
                print(f"Novo status: {novo_status}")
                
                self.db.execute("""
                    UPDATE dividas 
                    SET valor_pago = ?, status = ?
                    WHERE id = ?
                """, (novo_valor_pago, novo_status, divida['id']))
                
                # Se a dívida foi quitada, verificar se o trigger foi executado
                if novo_status == 'Quitado':
                    print("Dívida quitada - verificando se venda foi criada...")
                    venda_criada = self.db.fetchone("""
                        SELECT id, origem FROM vendas 
                        WHERE origem = 'divida_quitada' 
                        ORDER BY id DESC LIMIT 1
                    """)
                    if venda_criada:
                        print(f"Venda criada pelo trigger: ID {venda_criada['id']}")
                    else:
                        print("AVISO: Nenhuma venda foi criada pelo trigger!")
                
                self.db.conn.commit()
                fechar_dialogo(None)
                self.carregar_dividas_cliente(None)
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("✅ Pagamento registrado com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
                
            except Exception as error:
                print(f"Erro ao registrar pagamento: {error}")
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"❌ Erro: {str(error)}"),
                        bgcolor=ft.colors.RED
                    )
                )
        
        saldo_devedor = divida['valor_total'] - divida['valor_pago']
        
        valor_field = ft.TextField(
            label="Valor do Pagamento",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="MT ",
            value=f"{saldo_devedor:.2f}" if saldo_devedor > 0 else "0.00",
            hint_text="Digite o valor a pagar"
        )
        
        # Busca as formas de pagamento do banco de dados
        formas_pagamento = self.db.fetchall("SELECT nome FROM formas_pagamento WHERE ativo = 1 ORDER BY nome")
        
        forma_pagamento = ft.Dropdown(
            label="Forma de Pagamento",
            width=200,
            options=[
                ft.dropdown.Option(fp['nome']) for fp in formas_pagamento
            ]
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("Registrar Pagamento"),
            content=ft.Column([
                ft.Text(f"Dívida Total: MT {divida['valor_total']:.2f}"),
                ft.Text(f"Valor Pago: MT {divida['valor_pago']:.2f}"),
                ft.Text(f"Saldo Devedor: MT {saldo_devedor:.2f}", 
                       color=ft.colors.RED if saldo_devedor > 0 else ft.colors.GREEN,
                       weight=ft.FontWeight.BOLD),
                valor_field,
                forma_pagamento
            ], tight=True),
            actions=[
                ft.ElevatedButton(
                    "Cancelar",
                    icon=ft.icons.CANCEL,
                    bgcolor=ft.colors.RED_400,
                    color=ft.colors.WHITE,
                    on_click=fechar_dialogo
                ),
                ft.ElevatedButton(
                    "Confirmar",
                    icon=ft.icons.CHECK_CIRCLE,
                    bgcolor=ft.colors.GREEN_400,
                    color=ft.colors.WHITE,
                    on_click=confirmar_pagamento
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def fechar_dialogo(self, dialog):
        dialog.open = False
        self.page.update()

    def ver_detalhes(self, e):
        divida = e.control.data
        
        try:
            # Busca os itens da dívida e informações de desconto
            itens = self.db.fetchall("""
                SELECT 
                    i.quantidade,
                    i.preco_unitario,
                    i.subtotal,
                    i.peso_kg,
                    p.nome as produto_nome,
                    p.codigo as produto_codigo,
                    p.venda_por_peso
                FROM itens_divida i
                JOIN produtos p ON p.id = i.produto_id
                WHERE i.divida_id = ?
            """, (divida['id'],))
            
            # Busca informações de desconto da dívida
            info_divida = self.db.fetchone("""
                SELECT valor_original, desconto_aplicado, percentual_desconto
                FROM dividas WHERE id = ?
            """, (divida['id'],))
            
            # Ajustar a query dos pagamentos
            pagamentos = self.db.fetchall("""
                SELECT 
                    strftime('%Y-%m-%d', data_pagamento) as data_pagamento,  -- Formatação da data
                    valor,
                    forma_pagamento
                FROM pagamentos_divida
                WHERE divida_id = ?
                ORDER BY data_pagamento
            """, (divida['id'],))
            
            # Cria as tabelas de detalhes
            itens_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Produto")),
                    ft.DataColumn(ft.Text("Qtd/Peso")),
                    ft.DataColumn(ft.Text("Preço Unit.")),
                    ft.DataColumn(ft.Text("Subtotal"))
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"{i['produto_nome']} ({i['produto_codigo']})")),
                            ft.DataCell(ft.Text(
                                f"{i['quantidade']:.3f} KG" if i['venda_por_peso'] else f"{i['quantidade']:.0f} un"
                            )),
                            ft.DataCell(ft.Text(
                                f"MT {i['preco_unitario']:.2f}/KG" if i['venda_por_peso'] else f"MT {i['preco_unitario']:.2f}"
                            )),
                            ft.DataCell(ft.Text(f"MT {i['subtotal']:.2f}"))
                        ]
                    ) for i in itens
                ]
            )
            
            pagamentos_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Data")),
                    ft.DataColumn(ft.Text("Valor")),
                    ft.DataColumn(ft.Text("Forma"))
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(p['data_pagamento'])),
                            ft.DataCell(ft.Text(f"MT {p['valor']:.2f}")),
                            ft.DataCell(ft.Text(p['forma_pagamento']))
                        ]
                    ) for p in pagamentos
                ]
            )
            
            dialog = ft.AlertDialog(
                title=ft.Text("Detalhes da Dívida"),
                content=ft.Column([
                    ft.Text("Itens da Dívida:", size=16, weight=ft.FontWeight.BOLD),
                    itens_table,
                    ft.Divider(),
                    ft.Text("Pagamentos Realizados:", size=16, weight=ft.FontWeight.BOLD),
                    pagamentos_table if pagamentos else ft.Text("Nenhum pagamento registrado"),
                    ft.Divider(),
                    # Informações de desconto se aplicável
                    ft.Text(
                        f"Valor Original: MT {info_divida['valor_original']:.2f}",
                        color=ft.colors.BLUE
                    ) if info_divida and info_divida['valor_original'] > 0 else ft.Container(),
                    ft.Text(
                        f"Desconto Aplicado: MT {info_divida['desconto_aplicado']:.2f} ({info_divida['percentual_desconto'] * 100:.1f}%)",
                        color=ft.colors.GREEN
                    ) if info_divida and info_divida['desconto_aplicado'] > 0 else ft.Container(),
                    ft.Divider() if info_divida and info_divida['desconto_aplicado'] > 0 else ft.Container(),
                    ft.Text(f"Total da Dívida: MT {divida['valor_total']:.2f}"),
                    ft.Text(f"Total Pago: MT {divida['valor_pago']:.2f}"),
                    ft.Text(
                        f"Saldo Devedor: MT {(divida['valor_total'] - divida['valor_pago']):.2f}",
                        color=ft.colors.RED if divida['valor_pago'] < divida['valor_total'] else ft.colors.GREEN
                    )
                ], scroll=ft.ScrollMode.AUTO, height=400),
                actions=[
                    ft.ElevatedButton(
                        "Fechar",
                        on_click=lambda e: self.fechar_dialogo(dialog)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as error:
            print(f"Erro ao mostrar detalhes: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao mostrar detalhes: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def carregar_todas_dividas(self, e=None):
        try:
            # Modificar a query para formatar a data corretamente
            query = """
                SELECT 
                    d.id,
                    strftime('%Y-%m-%d', d.data_divida) as data_divida,  /* Formatação da data */
                    d.valor_total,
                    d.valor_original,
                    d.desconto_aplicado,
                    d.percentual_desconto,
                    d.valor_pago,
                    d.status,
                    d.observacao,
                    c.nome as cliente_nome,
                    c.nuit as cliente_nuit
                FROM dividas d
                JOIN clientes c ON c.id = d.cliente_id
                ORDER BY d.data_divida DESC
            """
            
            self.todas_dividas = self.db.fetchall(query)
            
            # Cria a nova tabela
            self.dividas_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Cliente")),
                    ft.DataColumn(ft.Text("Data")),
                    ft.DataColumn(ft.Text("Valor Total")),
                    ft.DataColumn(ft.Text("Desconto")),
                    ft.DataColumn(ft.Text("Valor Pago")),
                    ft.DataColumn(ft.Text("Saldo")),
                    ft.DataColumn(ft.Text("Status")),
                    ft.DataColumn(ft.Text("Ações"))
                ],
                rows=[]
            )
            apply_table_style(self.dividas_table)
            
            # Campo de busca
            self.busca_cliente = ft.TextField(
                label="Buscar Cliente",
                width=300,
                height=50,
                text_size=14,
                color=ft.colors.BLACK,
                label_style=ft.TextStyle(color=ft.colors.BLACK),
                focused_border_color=ft.colors.BLUE,
                border_color=ft.colors.BLUE_400,
                on_submit=self.filtrar_dividas  # Mudamos de on_change para on_submit
            )
            
            # Atualiza a tabela com todas as dívidas
            self.atualizar_tabela_dividas(self.todas_dividas)
            
            # Cria o container com o campo de busca e a tabela
            self.dividas_container.content = ft.Column([
                self.busca_cliente,
                ft.Container(height=10),
                self.dividas_table
            ])
            
            # Atualiza a view
            self.update()
            
        except Exception as ex:
            print(f"Erro ao carregar todas as dívidas: {ex}")
            import traceback
            print(traceback.format_exc())
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao carregar dívidas: {str(ex)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def filtrar_dividas(self, e):
        try:
            if not hasattr(self, 'todas_dividas'):
                return
            
            termo_busca = self.busca_cliente.value.lower()
            
            # Se o campo estiver vazio, mostra todas as dívidas
            if not termo_busca:
                self.atualizar_tabela_dividas(self.todas_dividas)
                return
            
            # Filtra as dívidas
            dividas_filtradas = [
                d for d in self.todas_dividas
                if termo_busca in d['cliente_nome'].lower() or 
                   (d['cliente_nuit'] and termo_busca in str(d['cliente_nuit']).lower())
            ]
            
            # Atualiza a tabela com os resultados filtrados
            self.atualizar_tabela_dividas(dividas_filtradas)
            self.update()
            
        except Exception as ex:
            print(f"Erro ao filtrar dívidas: {ex}")
            import traceback
            print(traceback.format_exc())

    def atualizar_tabela_dividas(self, dividas):
        try:
            self.dividas_table.rows.clear()
            for d in dividas:
                saldo = d['valor_total'] - d['valor_pago']
                self.dividas_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(d['cliente_nome'])),
                            ft.DataCell(ft.Text(d['data_divida'])),  # A data já vem formatada
                            ft.DataCell(ft.Text(f"MT {d['valor_total']:.2f}")),
                            ft.DataCell(
                                ft.Text(
                                    f"MT {d['desconto_aplicado']:.2f}",
                                    color=ft.colors.GREEN,
                                    weight=ft.FontWeight.BOLD
                                ) if d['desconto_aplicado'] and d['desconto_aplicado'] > 0 else ft.Text("-")
                            ),
                            ft.DataCell(ft.Text(f"MT {d['valor_pago']:.2f}")),
                            ft.DataCell(ft.Text(f"MT {saldo:.2f}")),
                            ft.DataCell(ft.Text(d['status'])),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.PAYMENT,
                                        icon_color=ft.colors.GREY if d['status'] == 'Quitado' else ft.colors.GREEN,
                                        tooltip="Registrar Pagamento" if d['status'] != 'Quitado' else "Dívida já paga",
                                        data=d,
                                        on_click=(self.registrar_pagamento if d['status'] != 'Quitado' else lambda e: self.page.show_snack_bar(ft.SnackBar(content=ft.Text('Esta dívida já foi paga!'), bgcolor=ft.colors.BLUE))),
                                        disabled=False
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.VISIBILITY,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Ver Detalhes",
                                        data=d,
                                        on_click=self.ver_detalhes
                                    )
                                ])
                            )
                        ]
                    )
                )
            self.update()
        except Exception as ex:
            print(f"Erro ao atualizar tabela: {ex}")
            import traceback
            print(traceback.format_exc())

    def confirmar_remocao_divida(self, e):
        divida = e.control.data
        
        def fechar_dialog(e):
            self.page.dialog.open = False
            self.page.update()
        
        def remover_divida(e):
            try:
                print(f"\n=== REMOVENDO DÍVIDA ===")
                print(f"Dívida ID: {divida['id']}")
                print(f"Status da dívida: {divida['status']}")
                print(f"Valor total: {divida['valor_total']}")
                print(f"Valor pago: {divida['valor_pago']}")
                
                # Verificar se a dívida foi quitada
                if divida['status'] == 'Quitado':
                    # Se foi quitada, não devolver estoque (já foi devolvido quando a venda foi anulada)
                    print("Dívida quitada - não devolvendo estoque")
                    
                    # Verificar se existe venda correspondente
                    venda_correspondente = self.db.fetchone("""
                        SELECT id, status FROM vendas 
                        WHERE origem = 'divida_quitada' 
                        ORDER BY id DESC LIMIT 1
                    """)
                    if venda_correspondente:
                        print(f"Venda correspondente encontrada: ID {venda_correspondente['id']}, Status: {venda_correspondente['status']}")
                    else:
                        print("AVISO: Nenhuma venda correspondente encontrada!")
                else:
                    # Devolver produtos ao estoque apenas se a dívida não foi quitada
                    print("Dívida pendente - devolvendo estoque")
                    itens = self.db.fetchall("""
                        SELECT produto_id, quantidade 
                        FROM itens_divida 
                        WHERE divida_id = ?
                    """, (divida['id'],))
                    
                    print(f"Número de itens para devolver: {len(itens)}")
                    for item in itens:
                        # Verificar estoque antes
                        estoque_antes = self.db.fetchone("""
                            SELECT estoque, nome FROM produtos WHERE id = ?
                        """, (item['produto_id'],))
                        print(f"Produto {estoque_antes['nome']}: estoque antes = {estoque_antes['estoque']}")
                        
                        self.db.execute("""
                            UPDATE produtos 
                            SET estoque = estoque + ? 
                            WHERE id = ?
                        """, (item['quantidade'], item['produto_id']))
                        
                        # Verificar estoque depois
                        estoque_depois = self.db.fetchone("""
                            SELECT estoque FROM produtos WHERE id = ?
                        """, (item['produto_id'],))
                        print(f"Produto {estoque_antes['nome']}: estoque depois = {estoque_depois['estoque']}")
                
                # Remove a dívida e seus itens
                print("Removendo itens da dívida...")
                self.db.execute("DELETE FROM itens_divida WHERE divida_id = ?", (divida['id'],))
                
                print("Removendo pagamentos da dívida...")
                self.db.execute("DELETE FROM pagamentos_divida WHERE divida_id = ?", (divida['id'],))
                
                print("Removendo dívida...")
                self.db.execute("DELETE FROM dividas WHERE id = ?", (divida['id'],))
                
                self.db.conn.commit()
                print("Dívida removida com sucesso!")
                
                self.page.dialog.open = False
                self.page.update()
                
                # Recarrega as dívidas
                self.carregar_dividas_cliente(None)
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("✅ Dívida removida com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
                
            except Exception as error:
                print(f"Erro ao remover dívida: {error}")
                self.db.conn.rollback()
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"❌ Erro ao remover dívida: {str(error)}"),
                        bgcolor=ft.colors.RED
                    )
                )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Remoção"),
            content=ft.Column([
                ft.Text(
                    "Tem certeza que deseja remover esta dívida?",
                    color=ft.colors.BLACK
                ),
                ft.Text(
                    "Esta ação irá:",
                    color=ft.colors.BLACK,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "• Devolver os produtos ao estoque\n"
                    "• Remover todos os pagamentos registrados\n"
                    "• Excluir permanentemente a dívida",
                    color=ft.colors.RED
                ),
                ft.Text(
                    "\nEsta ação não pode ser desfeita!",
                    color=ft.colors.RED,
                    weight=ft.FontWeight.BOLD
                )
            ]),
            actions=[
                ft.ElevatedButton(
                    "Cancelar",
                    icon=ft.icons.CANCEL,
                    bgcolor=ft.colors.BLUE_400,
                    color=ft.colors.WHITE,
                    on_click=fechar_dialog
                ),
                ft.ElevatedButton(
                    "Remover",
                    icon=ft.icons.DELETE_FOREVER,
                    bgcolor=ft.colors.RED_400,
                    color=ft.colors.WHITE,
                    on_click=remover_divida
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()