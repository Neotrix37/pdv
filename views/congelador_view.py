import flet as ft
from database.database import Database
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style
from views.generic_header import create_header

class CongeladorView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        
        # Campos do formulário
        self.codigo_field = ft.TextField(
            label="Código",
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        self.nome_field = ft.TextField(
            label="Nome do Produto",
            width=400,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Novo campo de descrição
        self.descricao_field = ft.TextField(
            label="Descrição",
            width=400,
            height=50,
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        self.preco_kg_field = ft.TextField(
            label="Preço de Venda por KG",
            width=200,
            height=50,
            prefix_text="MT ",
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        self.preco_custo_field = ft.TextField(
            label="Preço de Custo por KG",
            width=200,
            height=50,
            prefix_text="MT ",
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        self.estoque_kg_field = ft.TextField(
            label="Estoque (KG)",
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Tabela de produtos
        self.produtos_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Preço/KG")),
                ft.DataColumn(ft.Text("Estoque")),
                ft.DataColumn(ft.Text("Ações"))
            ],
            rows=[]
        )
        apply_table_style(self.produtos_table)
        
        # ID do produto em edição
        self.produto_em_edicao = None

    def build(self):
        # Criar header
        header = create_header(
            self.page,
            "Gerenciamento do Congelador",
            ft.icons.AC_UNIT,
            "Controle de produtos vendidos por peso"
        )

        return ft.Column([
            header,
            ft.Container(height=20),  # Espaçamento após o header
            
            # Container do formulário
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        self.codigo_field,
                        self.nome_field
                    ]),
                    ft.Row([
                        self.descricao_field
                    ]),
                    ft.Row([
                        self.preco_custo_field,
                        self.preco_kg_field,
                        self.estoque_kg_field
                    ]),
                    ft.Row([
                        ft.ElevatedButton(
                            "Salvar",
                            icon=ft.icons.SAVE,
                            on_click=self.salvar_produto,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.BLUE,
                                color=ft.colors.WHITE
                            )
                        ),
                        ft.OutlinedButton(
                            "Limpar",
                            icon=ft.icons.CLEAR,
                            on_click=self.limpar_formulario
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
            
            ft.Container(height=20),  # Espaçamento
            
            # Tabela de produtos com scroll
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Produtos Cadastrados",
                        size=16,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(
                        content=ft.Column(
                            [self.produtos_table],
                            scroll=ft.ScrollMode.AUTO
                        ),
                        height=400,  # Altura fixa para a tabela
                        border=ft.border.all(1, ft.colors.BLACK26),
                        border_radius=10,
                        padding=10
                    )
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

    def salvar_produto(self, e):
        try:
            if not self.validar_campos():
                return
            
            dados = {
                'codigo': self.codigo_field.value,
                'nome': self.nome_field.value,
                'descricao': self.descricao_field.value,
                'preco_custo': float(self.preco_custo_field.value or 0),
                'preco_venda': float(self.preco_kg_field.value or 0),
                'estoque': float(self.estoque_kg_field.value or 0),
                'venda_por_peso': 1,  # Sempre 1 para produtos do congelador
                'unidade_medida': 'kg'
            }
            
            if self.produto_em_edicao:
                # Atualizar produto existente
                self.db.execute("""
                    UPDATE produtos 
                    SET codigo = :codigo,
                        nome = :nome,
                        descricao = :descricao,
                        preco_custo = :preco_custo,
                        preco_venda = :preco_venda,
                        estoque = :estoque,
                        venda_por_peso = :venda_por_peso,
                        unidade_medida = :unidade_medida
                    WHERE id = :id
                """, {**dados, 'id': self.produto_em_edicao})
            else:
                # Inserir novo produto
                self.db.execute("""
                    INSERT INTO produtos 
                    (codigo, nome, descricao, preco_custo, preco_venda, estoque, 
                     venda_por_peso, unidade_medida)
                    VALUES 
                    (:codigo, :nome, :descricao, :preco_custo, :preco_venda, :estoque,
                     :venda_por_peso, :unidade_medida)
                """, dados)
            
            self.limpar_formulario()
            self.carregar_produtos()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Produto salvo com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
        except Exception as error:
            print(f"Erro ao salvar produto: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao salvar produto!"),
                    bgcolor=ft.colors.RED
                )
            )

    def carregar_produtos(self):
        try:
            produtos = self.db.fetchall("""
                SELECT 
                    id, 
                    codigo, 
                    nome, 
                    descricao,
                    COALESCE(preco_custo, 0) as preco_custo,
                    COALESCE(preco_venda, 0) as preco_venda,
                    COALESCE(estoque, 0) as estoque,
                    COALESCE(estoque_minimo, 0) as estoque_minimo,
                    venda_por_peso
                FROM produtos 
                WHERE venda_por_peso = 1 
                ORDER BY nome
            """)
            
            # Limpar linhas existentes
            self.produtos_table.rows.clear()
            
            for produto in produtos:
                self.produtos_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(produto['codigo'] or '-')),
                            ft.DataCell(ft.Text(produto['nome'] or '-')),
                            ft.DataCell(ft.Text(produto['descricao'] or '-')),
                            ft.DataCell(ft.Text(f"MT {float(produto['preco_venda']):.2f}")),
                            ft.DataCell(ft.Text(f"{float(produto['estoque']):.3f} KG")),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.EDIT,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Editar",
                                        data=produto,
                                        on_click=self.editar_produto
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        icon_color=ft.colors.RED,
                                        tooltip="Excluir",
                                        data=produto,
                                        on_click=self.excluir_produto
                                    )
                                ])
                            )
                        ]
                    )
                )
            
            self.update()
            
        except Exception as error:
            print(f"Erro ao carregar produtos: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao carregar produtos!"),
                    bgcolor=ft.colors.RED
                )
            )

    def editar_produto(self, e):
        produto = e.control.data
        self.produto_em_edicao = produto['id']
        
        self.codigo_field.value = produto['codigo']
        self.nome_field.value = produto['nome']
        self.descricao_field.value = produto['descricao'] or ""
        self.preco_custo_field.value = str(produto['preco_custo'])
        self.preco_kg_field.value = str(produto['preco_venda'])
        self.estoque_kg_field.value = str(produto['estoque'])
        
        self.update()

    def excluir_produto(self, e):
        produto = e.control.data
        
        def fechar_dialog(e):
            self.page.dialog.open = False
            self.page.update()
        
        def confirmar_exclusao(e):
            try:
                self.db.execute(
                    "DELETE FROM produtos WHERE id = ?",
                    (produto['id'],)
                )
                self.carregar_produtos()
                self.page.dialog.open = False
                self.page.update()
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Produto excluído com sucesso!"),
                        bgcolor=ft.colors.GREEN
                    )
                )
            except Exception as error:
                print(f"Erro ao excluir produto: {error}")
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Erro ao excluir produto!"),
                        bgcolor=ft.colors.RED
                    )
                )
        
        # Diálogo de confirmação
        self.page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Deseja realmente excluir o produto '{produto['nome']}'?"),
            actions=[
                ft.ElevatedButton(
                    "Cancelar",
                    icon=ft.icons.CANCEL,
                    on_click=fechar_dialog,
                    bgcolor=ft.colors.BLUE_400,
                    color=ft.colors.WHITE
                ),
                ft.ElevatedButton(
                    "Excluir",
                    icon=ft.icons.DELETE,
                    on_click=confirmar_exclusao,
                    bgcolor=ft.colors.RED_400,
                    color=ft.colors.WHITE
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog.open = True
        self.page.update()

    def limpar_formulario(self, e=None):
        self.produto_em_edicao = None
        self.codigo_field.value = ""
        self.nome_field.value = ""
        self.descricao_field.value = ""
        self.preco_custo_field.value = ""
        self.preco_kg_field.value = ""
        self.estoque_kg_field.value = ""
        self.update()

    def did_mount(self):
        self.carregar_produtos()

    def validar_campos(self):
        """Valida os campos do formulário"""
        if not self.codigo_field.value:
            self.mostrar_erro("O código é obrigatório!")
            return False
        
        if not self.nome_field.value:
            self.mostrar_erro("O nome é obrigatório!")
            return False
        
        try:
            preco_custo = float(self.preco_custo_field.value or 0)
            if preco_custo < 0:
                self.mostrar_erro("O preço de custo não pode ser negativo!")
                return False
        except ValueError:
            self.mostrar_erro("Preço de custo inválido!")
            return False
        
        try:
            preco_venda = float(self.preco_kg_field.value or 0)
            if preco_venda <= 0:
                self.mostrar_erro("O preço de venda deve ser maior que zero!")
                return False
        except ValueError:
            self.mostrar_erro("Preço de venda inválido!")
            return False
        
        try:
            estoque = float(self.estoque_kg_field.value or 0)
            if estoque < 0:
                self.mostrar_erro("O estoque não pode ser negativo!")
                return False
        except ValueError:
            self.mostrar_erro("Estoque inválido!")
            return False
        
        return True

    def mostrar_erro(self, mensagem):
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(mensagem),
                bgcolor=ft.colors.RED_600
            )
        ) 