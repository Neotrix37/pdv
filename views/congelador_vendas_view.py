import flet as ft
from database.database import Database
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style
from views.generic_header import create_header
from datetime import datetime

class CongeladorVendasView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        self.produto_selecionado = None
        
        # Header da página
        self.header = create_header(
            self.page,
            "PDV do Congelador",
            ft.icons.AC_UNIT,
            "Venda de produtos por peso"
        )
        
        # Campo de busca
        self.busca_field = ft.TextField(
            label="Buscar produto",
            prefix_icon=ft.icons.SEARCH,
            width=300,
            on_change=self.filtrar_produtos,
            bgcolor=ft.colors.WHITE,
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            color=ft.colors.BLACK
        )
        
        # Tabela de produtos
        self.produtos_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Nome", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Preço/KG", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Estoque", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK))
            ],
            rows=[]
        )
        
        # Área de venda
        self.produto_selecionado_text = ft.Text(
            "Nenhum produto selecionado",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        self.preco_kg_text = ft.Text(
            "Preço/KG: MT 0.00",
            size=16,
            color=ft.colors.BLACK
        )
        
        self.estoque_text = ft.Text(
            "Estoque: 0 KG",
            size=16,
            color=ft.colors.BLACK
        )
        
        self.valor_venda_field = ft.TextField(
            label="Valor da Venda (MT)",
            width=200,
            prefix_text="MT ",
            on_change=self.calcular_peso_venda,
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            color=ft.colors.BLACK
        )
        
        self.peso_calculado_text = ft.Text(
            "Peso: 0 KG",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLACK
        )
        
        # Carregar formas de pagamento do banco
        self.forma_pagamento = ft.Dropdown(
            label="Forma de Pagamento",
            width=200,
            options=self.carregar_formas_pagamento(),
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            color=ft.colors.BLACK
        )
        
        self.btn_finalizar = ft.ElevatedButton(
            "Finalizar Venda",
            icon=ft.icons.SHOPPING_CART_CHECKOUT,
            on_click=self.realizar_venda,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN
            )
        )

    def build(self):
        return ft.Column([
            self.header,
            
            ft.Container(height=20),
            
            # Apenas o botão de voltar ao congelador
            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        "Voltar ao Congelador",
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/congelador")
                    )
                ]),
                padding=10
            ),
            
            # Área de venda
            ft.Container(
                content=ft.Column([
                    self.produto_selecionado_text,
                    self.preco_kg_text,
                    self.estoque_text,
                    
                    ft.Row([
                        self.valor_venda_field,
                        self.peso_calculado_text
                    ]),
                    ft.Row([
                        self.forma_pagamento,
                        self.btn_finalizar
                    ])
                ]),
                padding=20,
                bgcolor=ft.colors.WHITE,
                border_radius=10
            ),
            
            # Área de busca
            ft.Container(
                content=ft.Row([
                    self.busca_field,
                    ft.Text("Produtos disponíveis:", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK)
                ]),
                padding=10
            ),
            
            # Tabela de produtos com scroll
            ft.Container(
                content=ft.Column(
                    [self.produtos_table],
                    scroll=ft.ScrollMode.AUTO
                ),
                height=300,
                padding=10,
                border=ft.border.all(1, ft.colors.BLACK26),
                border_radius=10
            )
        ])

    def carregar_formas_pagamento(self):
        try:
            formas = self.db.get_formas_pagamento()
            return [ft.dropdown.Option(forma['nome']) for forma in formas]
        except:
            # Formas de pagamento padrão caso não consiga carregar do banco
            return [
                ft.dropdown.Option("Dinheiro"),
                ft.dropdown.Option("M-PESA"),
                ft.dropdown.Option("E-Mola"),
                ft.dropdown.Option("Cartão POS"),
                ft.dropdown.Option("Transferência")
            ]

    def carregar_produtos(self):
        try:
            produtos = self.db.fetchall("""
                SELECT * FROM produtos 
                WHERE venda_por_peso = 1 
                AND ativo = 1
                AND estoque > 0
                ORDER BY nome
            """)
            self.atualizar_tabela_produtos(produtos)
        except Exception as error:
            print(f"Erro ao carregar produtos: {error}")
            self.mostrar_erro("Erro ao carregar produtos!")

    def filtrar_produtos(self, e):
        try:
            busca = self.busca_field.value.lower() if self.busca_field.value else ""
            
            # Se a busca estiver vazia, recarregar todos os produtos
            if not busca:
                self.carregar_produtos()
                return
            
            produtos = self.db.fetchall("""
                SELECT * FROM produtos 
                WHERE venda_por_peso = 1 
                AND ativo = 1
                AND estoque > 0
                AND (
                    LOWER(codigo) LIKE ? 
                    OR LOWER(nome) LIKE ?
                    OR LOWER(descricao) LIKE ?
                )
                ORDER BY nome
            """, (f"%{busca}%", f"%{busca}%", f"%{busca}%"))
            
            self.atualizar_tabela_produtos(produtos)
            
        except Exception as error:
            print(f"Erro ao filtrar produtos: {error}")
            self.mostrar_erro("Erro ao filtrar produtos!")

    def atualizar_tabela_produtos(self, produtos):
        """Função auxiliar para atualizar a tabela de produtos"""
        self.produtos_table.rows.clear()
        for produto in produtos:
            self.produtos_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(produto['codigo'], color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(produto['nome'], color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(f"MT {produto['preco_venda']:.2f}", color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(f"{produto['estoque']:.3f} KG", color=ft.colors.BLACK)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.SHOPPING_CART,
                                icon_color=ft.colors.BLUE,
                                tooltip="Selecionar para Venda",
                                data=produto,
                                on_click=self.selecionar_produto
                            )
                        )
                    ]
                )
            )

    def selecionar_produto(self, e):
        try:
            produto = e.control.data
            self.produto_selecionado = produto
            preco_kg = produto['preco_venda']
            
            self.produto_selecionado_text.value = f"Produto: {produto['nome']}"
            self.preco_kg_text.value = f"Preço/KG: MT {preco_kg:.2f}"
            self.estoque_text.value = f"Estoque: {produto['estoque']:.3f} KG"
            
            # Criar tabela de referência em um diálogo
            tabela_ref = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Valor (MT)", color=ft.colors.BLACK)),
                    ft.DataColumn(ft.Text("Peso (KG)", color=ft.colors.BLACK))
                ],
                rows=[]
            )
            
            # Valores de exemplo começando de 30 MT (valor mínimo)
            for valor in [30, 50, 100, 150, 200]:
                peso = valor / preco_kg
                tabela_ref.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"MT {valor:.2f}", color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(f"{peso:.3f} KG", color=ft.colors.BLACK))
                        ]
                    )
                )
            
            def close_dialog(e):
                self.page.dialog.open = False
                self.page.update()
            
            # Criar e mostrar o diálogo
            self.page.dialog = ft.AlertDialog(
                title=ft.Text("Valores de Referência", color=ft.colors.BLACK),
                content=ft.Container(
                    content=tabela_ref,
                    padding=10,
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=10
                ),
                actions=[
                    ft.TextButton("Fechar", on_click=close_dialog)
                ]
            )
            self.page.dialog.open = True
            
            self.valor_venda_field.value = ""
            self.peso_calculado_text.value = "Peso: 0 KG"
            self.btn_finalizar.disabled = True
            
            self.update()
            self.page.update()
            
        except Exception as error:
            print(f"Erro ao selecionar produto: {error}")
            self.mostrar_erro("Erro ao selecionar produto!")

    def calcular_peso_venda(self, e):
        try:
            if not self.produto_selecionado:
                return
            
            valor = float(self.valor_venda_field.value or 0)
            preco_kg = float(self.produto_selecionado['preco_venda'])
            
            if preco_kg <= 0:
                self.mostrar_erro("Preço por KG inválido!")
                return
            
            peso = valor / preco_kg
            self.peso_calculado_text.value = f"Peso: {peso:.3f} KG"
            
            # Habilita o botão se houver estoque suficiente
            self.btn_finalizar.disabled = peso <= 0 or peso > self.produto_selecionado['estoque']
            
            self.update()
            
        except:
            self.peso_calculado_text.value = "Peso: 0 KG"
            self.btn_finalizar.disabled = True
            self.update()

    def realizar_venda(self, e):
        try:
            MIN_VALOR_VENDA = 30  # Mínimo de 30 MT
            MIN_PESO_KG = 0.100   # Mínimo de 100 gramas
            
            if not self.produto_selecionado:
                self.mostrar_erro("Selecione um produto!")
                return
            
            if not self.valor_venda_field.value:
                self.mostrar_erro("Informe o valor da venda!")
                return
            
            if not self.forma_pagamento.value:
                self.mostrar_erro("Selecione a forma de pagamento!")
                return
            
            valor = float(self.valor_venda_field.value)
            
            # Validar valor mínimo
            if valor < MIN_VALOR_VENDA:
                self.mostrar_erro(f"Valor mínimo de venda: MT {MIN_VALOR_VENDA:.2f}")
                return
            
            preco_kg = float(self.produto_selecionado['preco_venda'])
            peso = valor / preco_kg
            
            # Validar peso mínimo
            if peso < MIN_PESO_KG:
                self.mostrar_erro(f"Peso mínimo: {MIN_PESO_KG*1000:.0f} gramas")
                return
            
            if peso > self.produto_selecionado['estoque']:
                self.mostrar_erro(f"Estoque insuficiente! Disponível: {self.produto_selecionado['estoque']:.3f} KG")
                return
            
            # Confirmar venda
            self.page.dialog = ft.AlertDialog(
                title=ft.Text("Confirmar Venda"),
                content=ft.Column([
                    ft.Text(f"Produto: {self.produto_selecionado['nome']}", color=ft.colors.BLACK),
                    ft.Text(f"Valor: MT {valor:.2f}", color=ft.colors.BLACK),
                    ft.Text(f"Peso: {peso:.3f} KG", color=ft.colors.BLACK),
                    ft.Text(f"Forma de Pagamento: {self.forma_pagamento.value}", color=ft.colors.BLACK)
                ], spacing=10),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: setattr(self.page.dialog, 'open', False)),
                    ft.TextButton("Confirmar", on_click=lambda _: self.confirmar_venda(valor, peso))
                ]
            )
            self.page.dialog.open = True
            self.page.update()
            
        except Exception as error:
            print(f"Erro ao realizar venda: {error}")
            self.mostrar_erro("Erro ao realizar venda!")

    def confirmar_venda(self, valor, peso):
        try:
            # Start transaction
            cursor = self.db.conn.cursor()
            
            # Registrar venda
            cursor.execute("""
                INSERT INTO vendas (
                    usuario_id, total, forma_pagamento,
                    data_venda, status
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                self.usuario['id'],
                valor,
                self.forma_pagamento.value,
                datetime.now(),
                'Ativa'
            ))
            
            # Get the ID of the inserted venda
            venda_id = cursor.lastrowid
            
            # Registrar item
            cursor.execute("""
                INSERT INTO itens_venda (
                    venda_id, produto_id, quantidade,
                    preco_unitario, preco_custo_unitario,
                    subtotal, peso_kg
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                venda_id,
                self.produto_selecionado['id'],
                peso,
                self.produto_selecionado['preco_venda'],
                self.produto_selecionado['preco_custo'],
                valor,
                peso
            ))
            
            # Atualizar estoque
            cursor.execute("""
                UPDATE produtos 
                SET estoque = estoque - ?
                WHERE id = ?
            """, (peso, self.produto_selecionado['id']))
            
            # Commit the transaction
            self.db.conn.commit()
            
            # Fechar diálogo
            self.page.dialog.open = False
            
            # Limpar campos
            self.produto_selecionado = None
            self.produto_selecionado_text.value = "Nenhum produto selecionado"
            self.preco_kg_text.value = "Preço/KG: MT 0.00"
            self.estoque_text.value = "Estoque: 0 KG"
            self.valor_venda_field.value = ""
            self.peso_calculado_text.value = "Peso: 0 KG"
            self.forma_pagamento.value = None
            self.btn_finalizar.disabled = True
            
            # Recarregar produtos
            self.carregar_produtos()
            
            self.mostrar_sucesso("Venda realizada com sucesso!")
            self.update()
            
        except Exception as error:
            # Rollback in case of error
            self.db.conn.rollback()
            print(f"Erro ao confirmar venda: {error}")
            self.mostrar_erro("Erro ao confirmar venda!")

    def mostrar_erro(self, mensagem):
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(mensagem),
                bgcolor=ft.colors.RED_600
            )
        )

    def mostrar_sucesso(self, mensagem):
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(mensagem),
                bgcolor=ft.colors.GREEN_600
            )
        )

    def did_mount(self):
        self.carregar_produtos() 