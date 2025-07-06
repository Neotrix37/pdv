import flet as ft
from database.database import Database
from models.produto import Produto
from utils.helpers import formatar_moeda
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style

class ProdutosView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        self.produto_model = Produto()
        
        # Inicializa produto_em_edicao
        self.produto_em_edicao = None
        
        # Inicializa todos os campos e controles
        self.inicializar_campos()
        self.inicializar_tabela()

    def inicializar_campos(self):
        # Campo de busca
        self.busca_field = ft.TextField(
            label="Buscar produto",
            width=300,
            height=50,
            prefix_icon=ft.icons.SEARCH,
            on_change=self.filtrar_produtos,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Campos do formulário
        self.codigo_field = ft.TextField(
            label="Código",
            width=200,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Campo de categoria
        self.categoria_field = ft.Dropdown(
            label="Categoria",
            width=300,
            height=50,
            color=ft.colors.WHITE,
            text_style=ft.TextStyle(color=ft.colors.WHITE),
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            border_color=ft.colors.BLUE_200,
            focused_border_color=ft.colors.BLUE_100,
            bgcolor=ft.colors.BLUE_900,
            focused_bgcolor=ft.colors.BLUE_800,
            content_padding=10,
            options=[
                ft.dropdown.Option(
                    key="",
                    text="Selecione uma categoria"
                )
            ]
        )
        
        # Estilizar o menu dropdown
        self.categoria_field.style = ft.ButtonStyle(
            bgcolor={
                ft.MaterialState.DEFAULT: ft.colors.BLUE_900,
                ft.MaterialState.SELECTED: ft.colors.WHITE,
            },
            color={
                ft.MaterialState.DEFAULT: ft.colors.WHITE,
                ft.MaterialState.SELECTED: ft.colors.BLACK,
            }
        )
        
        # Campo de tipo de venda
        self.venda_por_peso_switch = ft.Switch(
            label="Vender por Peso",
            value=False,
            on_change=self.alterar_tipo_venda
        )
        
        self.nome_field = ft.TextField(
            label=self.t("product_name"),
            width=400,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.descricao_field = ft.TextField(
            label=self.t("description"),
            width=400,
            height=50,
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.preco_custo_field = ft.TextField(
            label=self.t("cost_price"),
            width=200,
            height=50,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.preco_venda_field = ft.TextField(
            label=self.t("sale_price"),
            width=200,
            height=50,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.estoque_field = ft.TextField(
            label=self.t("stock"),
            width=200,
            height=50,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.estoque_minimo_field = ft.TextField(
            label=self.t("min_stock"),
            width=200,
            height=50,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )

    def inicializar_tabela(self):
        # Tabela de produtos
        self.produtos_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Nome", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Descrição", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Preço Custo", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Preço Venda", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Estoque/Mín", color=ft.colors.GREY_900)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.GREY_900))
            ],
            rows=[]
        )
        apply_table_style(self.produtos_table)
        # Carrega os produtos iniciais
        self.carregar_produtos()

    def build(self):
        return ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/dashboard")
                    ),
                    ft.Icon(
                        name=ft.icons.INVENTORY,
                        size=30,
                        color=ft.colors.WHITE
                    ),
                    ft.Text(
                        self.t("products"),
                        size=20,
                        color=ft.colors.WHITE
                    )
                ]),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
                ),
                padding=20,
                border_radius=10
            ),
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        self.codigo_field,
                        self.categoria_field,
                    ]),
                    ft.Row([
                        self.nome_field,
                        self.venda_por_peso_switch
                    ]),
                    self.descricao_field,
                    ft.Row([
                        self.preco_custo_field,
                        self.preco_venda_field,
                        self.estoque_field,
                        self.estoque_minimo_field
                    ]),
                    ft.Row([
                        ft.ElevatedButton(
                            "Salvar",
                            icon=ft.icons.SAVE,
                            on_click=self.salvar_produto
                        ),
                        ft.OutlinedButton(
                            "Limpar",
                            icon=ft.icons.CLEAR,
                            on_click=self.limpar_formulario
                        )
                    ])
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10
            ),
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        self.busca_field
                    ]),
                    ft.Container(
                        content=ft.Column(
                            [self.produtos_table],
                            scroll=ft.ScrollMode.AUTO
                        ),
                        height=500,  # Altura ajustável conforme necessidade
                        border=ft.border.all(1, ft.colors.BLACK26),
                        border_radius=10,
                        padding=10
                    )
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

    def carregar_produtos(self, busca=""):
        try:
            produtos = self.db.fetchall("""
                SELECT 
                    id, 
                    codigo, 
                    nome, 
                    descricao,
                    preco_custo,
                    preco_venda,
                    estoque,
                    estoque_minimo,
                    ativo,
                    categoria_id,
                    venda_por_peso
                FROM produtos 
                WHERE (LOWER(codigo) LIKE ? OR LOWER(nome) LIKE ?) 
                AND ativo = 1
                ORDER BY nome
            """, (f"%{busca.lower()}%", f"%{busca.lower()}%"))

            self.produtos_table.rows.clear()
            for p in produtos:
                self.produtos_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(p['codigo'])),
                            ft.DataCell(ft.Text(p['nome'])),
                            ft.DataCell(ft.Text(p['descricao'] or "-")),
                            ft.DataCell(ft.Text(f"MT {p['preco_custo']:.2f}")),
                            ft.DataCell(ft.Text(f"MT {p['preco_venda']:.2f}")),
                            ft.DataCell(
                                ft.Row([
                                    ft.Icon(
                                        name=ft.icons.WARNING_AMBER_ROUNDED,
                                        color=ft.colors.RED_500,
                                        visible=p['estoque'] <= p['estoque_minimo']
                                    ),
                                    ft.Text(
                                        str(p['estoque']),
                                        color=ft.colors.RED if p['estoque'] <= p['estoque_minimo'] else None,
                                        weight=ft.FontWeight.BOLD if p['estoque'] <= p['estoque_minimo'] else None
                                    ),
                                    ft.Text(f" / {p['estoque_minimo']}")
                                ])
                            ),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.EDIT,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Editar",
                                        data=p,
                                        on_click=self.editar_produto
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        icon_color=ft.colors.RED,
                                        tooltip="Excluir",
                                        data=p,
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

    def salvar_produto(self, e):
        try:
            # Validações dos campos
            if not self.codigo_field.value:
                self.mostrar_erro("Digite o código do produto!")
                return

            if not self.nome_field.value:
                self.mostrar_erro("Digite o nome do produto!")
                return
            
            if not self.categoria_field.value or self.categoria_field.value == "":
                self.mostrar_erro("Selecione uma categoria!")
                return

            # Verificar se o código já existe
            produto_existente = self.db.fetchone(
                """
                SELECT id, ativo 
                FROM produtos 
                WHERE codigo = ? AND id != ?
                """,
                (self.codigo_field.value, self.produto_em_edicao or 0)
            )

            if produto_existente:
                status = "inativo" if not produto_existente['ativo'] else "ativo"
                self.mostrar_erro(f"Já existe um produto {status} com este código!")
                return

            # Converter valores com tratamento para nulos
            try:
                preco_custo = float(self.preco_custo_field.value or 0)
                preco_venda = float(self.preco_venda_field.value or 0)
                estoque = float(self.estoque_field.value or 0)
                estoque_minimo = float(self.estoque_minimo_field.value or 0)
                categoria_id = int(self.categoria_field.value) if self.categoria_field.value else None
            except ValueError as e:
                self.mostrar_erro("Por favor, verifique os valores numéricos informados!")
                return

            dados = {
                'codigo': self.codigo_field.value,
                'nome': self.nome_field.value,
                'descricao': self.descricao_field.value or "",
                'preco_custo': preco_custo,
                'preco_venda': preco_venda,
                'estoque': estoque,
                'estoque_minimo': estoque_minimo,
                'categoria_id': categoria_id,
                'venda_por_peso': 1 if self.venda_por_peso_switch.value else 0,
                'unidade_medida': 'kg' if self.venda_por_peso_switch.value else 'un'
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
                        estoque_minimo = :estoque_minimo,
                        categoria_id = :categoria_id,
                        venda_por_peso = :venda_por_peso,
                        unidade_medida = :unidade_medida,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """, {**dados, 'id': self.produto_em_edicao})
            else:
                # Inserir novo produto
                self.db.execute("""
                    INSERT INTO produtos (
                        codigo, nome, descricao,
                        preco_custo, preco_venda,
                        estoque, estoque_minimo,
                        categoria_id, venda_por_peso, unidade_medida,
                        ativo
                    ) VALUES (
                        :codigo, :nome, :descricao,
                        :preco_custo, :preco_venda,
                        :estoque, :estoque_minimo,
                        :categoria_id, :venda_por_peso, :unidade_medida,
                        1
                    )
                """, dados)

            self.mostrar_sucesso("Produto salvo com sucesso!")
            self.limpar_formulario(None)
            self.carregar_produtos()

        except Exception as error:
            print(f"Erro ao salvar produto: {error}")
            self.mostrar_erro("Erro ao salvar produto!")

    def editar_produto(self, e):
        try:
            produto = e.control.data
            self.produto_em_edicao = produto['id']
            
            # Preenche os campos com os dados do produto
            self.codigo_field.value = produto['codigo']
            self.nome_field.value = produto['nome']
            self.descricao_field.value = produto['descricao']
            self.preco_custo_field.value = str(produto['preco_custo'])
            self.preco_venda_field.value = str(produto['preco_venda'])
            self.estoque_field.value = str(produto['estoque'])
            self.estoque_minimo_field.value = str(produto['estoque_minimo'])
            self.categoria_field.value = str(produto['categoria_id'])
            self.venda_por_peso_switch.value = bool(produto['venda_por_peso'])
            
            # Atualizar labels baseado no tipo de venda
            if self.venda_por_peso_switch.value:  # Venda por peso
                self.estoque_field.label = "Estoque (KG)"
                self.preco_venda_field.label = "Preço por KG"
            else:  # Venda por unidade
                self.estoque_field.label = "Estoque (Unidades)"
                self.preco_venda_field.label = "Preço por Unidade"
            
            self.update()
            
        except Exception as error:
            print(f"Erro ao editar produto: {error}")
            self.mostrar_erro("Erro ao carregar dados do produto!")

    def excluir_produto(self, e):
        try:
            produto = e.control.data
            self.db.execute(
                "UPDATE produtos SET ativo = 0 WHERE id = ?",
                (produto['id'],)
            )
            
            # Atualizar a lista imediatamente após excluir
            self.carregar_produtos()
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Produto excluído com sucesso!"),
                    bgcolor=ft.colors.GREEN,
                    duration=3000
                )
            )
        except Exception as error:
            print(f"Erro ao excluir produto: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Erro ao excluir produto!"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

    def limpar_formulario(self, e):
        try:
            self.produto_em_edicao = None
            self.codigo_field.value = ""
            self.nome_field.value = ""
            self.descricao_field.value = ""
            self.preco_custo_field.value = ""
            self.preco_venda_field.value = ""
            self.estoque_field.value = ""
            self.estoque_minimo_field.value = ""
            self.categoria_field.value = None
            self.venda_por_peso_switch.value = False
            
            # Resetar labels para venda por unidade (padrão)
            self.estoque_field.label = "Estoque (Unidades)"
            self.preco_venda_field.label = "Preço por Unidade"
            
            self.update()
        except Exception as error:
            print(f"Erro ao limpar formulário: {error}")

    def filtrar_produtos(self, e):
        termo = e.control.value.lower()
        try:
            produtos = self.db.fetchall("""
                SELECT * FROM produtos 
                WHERE (LOWER(nome) LIKE ? OR LOWER(codigo) LIKE ?)
                    AND ativo = 1
                ORDER BY nome
            """, (f"%{termo}%", f"%{termo}%"))
            
            self.produtos_table.rows.clear()
            for produto in produtos:
                self.produtos_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(produto['codigo'], color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(produto['nome'], color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(produto['descricao'] or "-", color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(f"MT {produto['preco_custo']:.2f}", color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(f"MT {produto['preco_venda']:.2f}", color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(f"{produto['estoque']}/{produto['estoque_minimo']}", color=ft.colors.GREY_900)),
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
        except Exception as e:
            print(f"Erro ao filtrar produtos: {e}")

    def did_mount(self):
        """Método chamado quando a view é montada"""
        try:
            print("\n=== Debug did_mount() ===")
            # Primeiro carregar as categorias
            self.carregar_categorias()
            # Depois carregar os produtos
            self.carregar_produtos()
            print("=== Fim did_mount() ===\n")
        except Exception as e:
            print(f"Erro no did_mount: {e}")

    def carregar_categorias(self):
        """Carrega as categorias no dropdown"""
        try:
            print("\n=== Carregando categorias ===")
            # Buscar todas as categorias
            categorias = self.db.fetchall("""
                SELECT id, nome FROM categorias 
                ORDER BY 
                    CASE 
                        WHEN nome = 'Outros' THEN 2 
                        ELSE 1 
                    END,
                    nome
            """)
            
            print(f"Categorias encontradas: {len(categorias)}")
            
            # Limpar opções existentes
            self.categoria_field.options = []
            
            # Adicionar opção padrão
            self.categoria_field.options.append(
                ft.dropdown.Option(
                    key="",
                    text="Selecione uma categoria"
                )
            )
            
            # Adicionar categorias do banco
            for cat in categorias:
                print(f"Adicionando categoria: {cat['nome']} (ID: {cat['id']})")
                self.categoria_field.options.append(
                    ft.dropdown.Option(
                        key=str(cat['id']),
                        text=cat['nome']
                    )
                )
            
            print("=== Categorias carregadas com sucesso ===\n")
            self.update()
            
        except Exception as error:
            print(f"Erro ao carregar categorias: {error}")
            self.mostrar_erro("Erro ao carregar categorias!")

    def alterar_tipo_venda(self, e):
        """Altera labels e comportamento baseado no tipo de venda"""
        if e.control.value:  # Venda por peso
            self.estoque_field.label = "Estoque (KG)"
            self.preco_venda_field.label = "Preço por KG"
        else:  # Venda por unidade
            self.estoque_field.label = "Estoque (Unidades)"
            self.preco_venda_field.label = "Preço por Unidade"
        self.update()

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