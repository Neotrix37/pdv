import flet as ft
import asyncio
from database.database import Database
from models.produto import Produto
from utils.helpers import formatar_moeda
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style
from repositories.produto_repository import ProdutoRepository

class ProdutosView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        self.produto_model = Produto()
        self.produto_repository = ProdutoRepository()
        
        # Inicializa produto_em_edicao
        self.produto_em_edicao = None
        
        # Inicializa filtro de estoque baixo
        self.filtrar_estoque_baixo = False
        
        # Inicializa todos os campos e controles
        self.inicializar_campos()
        self.inicializar_tabela()

    def _safe_update(self):
        """Atualiza a UI com segurança, evitando erro 'Control must be added to the page first'."""
        try:
            if hasattr(self, 'page') and self.page:
                super().update()
        except Exception as e:
            # Apenas loga; não interrompe o fluxo
            print(f"[UI] Aviso ao atualizar view: {e}")

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
            width=150,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        
        # Campo de categoria
        self.categoria_field = ft.Dropdown(
            label="Categoria",
            width=200,
            height=50,
            color=ft.colors.BLACK,
            text_style=ft.TextStyle(color=ft.colors.BLACK),
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            border_color=ft.colors.BLUE_200,
            focused_border_color=ft.colors.BLUE_100,
            bgcolor=ft.colors.WHITE,
            focused_bgcolor=ft.colors.WHITE,
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
            width=300,
            height=50,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.descricao_field = ft.TextField(
            label=self.t("description"),
            width=300,
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
            width=150,
            height=50,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.preco_venda_field = ft.TextField(
            label=self.t("sale_price"),
            width=150,
            height=50,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.estoque_field = ft.TextField(
            label=self.t("stock"),
            width=150,
            height=50,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )
        self.estoque_minimo_field = ft.TextField(
            label=self.t("min_stock"),
            width=150,
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
        return ft.Container(
            content=ft.Column([
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
            ft.Container(height=5),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        self.codigo_field,
                        self.categoria_field,
                        self.nome_field,
                        self.venda_por_peso_switch
                    ], spacing=5),
                    ft.Row([
                        self.descricao_field
                    ], spacing=5),
                    ft.Row([
                        self.preco_custo_field,
                        self.preco_venda_field,
                        self.estoque_field,
                        self.estoque_minimo_field,
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
                    ], spacing=5)
                ], spacing=5),
                bgcolor=ft.colors.WHITE,
                padding=10,
                border_radius=10
            ),
            ft.Container(height=5),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("PRODUTOS DISPONÍVEIS", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                        ft.Container(content=self.busca_field, margin=ft.margin.only(left=10)),
                        ft.Container(
                            content=ft.Row([
                                ft.Switch(
                                    label="Apenas estoque baixo",
                                    value=self.filtrar_estoque_baixo,
                                    on_change=self.alternar_filtro_estoque_baixo,
                                    active_color=ft.colors.RED_400,
                                    inactive_thumb_color=ft.colors.GREY_400
                                ),
                                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.RED_500, size=20)
                            ]),
                            margin=ft.margin.only(left=10)
                        )
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Container(
                        content=ft.Column(
                            [self.produtos_table],
                            scroll=ft.ScrollMode.AUTO
                        ),
                        height=300,  # Aumentando a altura da tabela para melhor visualização
                        border=ft.border.all(1, ft.colors.BLUE_200),
                        border_radius=10,
                        padding=10,
                        margin=ft.margin.only(bottom=50)  # Aumentando o espaço abaixo da tabela
                    )
                ]),
                bgcolor=ft.colors.WHITE,
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=5,
                    color=ft.colors.BLUE_GREY_100,
                    offset=ft.Offset(0, 2)
                )
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=5),
            padding=ft.padding.only(bottom=30),
            expand=True
        )

    def carregar_produtos(self, busca=""):
        """Carrega produtos usando o repositório híbrido (versão síncrona)."""
        try:
            # Usar repositório híbrido para listar produtos (versão síncrona)
            produtos = self.produto_repository.get_all()
            print(f"📦 Carregados {len(produtos)} produtos via repositório híbrido")
            
            # Filtrar produtos baseado na busca e filtros
            produtos_filtrados = []
            for produto in produtos:
                # Filtro de busca
                if busca:
                    if (busca.lower() not in produto.get('nome', '').lower() and 
                        busca.lower() not in produto.get('codigo', '').lower()):
                        continue
                
                # Filtro de estoque baixo
                if self.filtrar_estoque_baixo:
                    if produto.get('estoque', 0) > produto.get('estoque_minimo', 0):
                        continue
                
                # Apenas produtos ativos
                if produto.get('ativo', True):
                    produtos_filtrados.append(produto)
            
            # Limpar tabela e recarregar
            self.produtos_table.rows.clear()
            
            for produto in produtos_filtrados:
                # Verifica se o estoque está baixo
                estoque = produto.get('estoque', 0)
                estoque_minimo = produto.get('estoque_minimo', 0)
                estoque_baixo = estoque <= estoque_minimo
                
                # Define a cor do texto com base no estoque
                cor_estoque = ft.colors.RED_500 if estoque_baixo else ft.colors.GREY_900
                
                # Cria a célula de estoque com ícone de alerta se necessário
                celula_estoque = ft.DataCell(
                    ft.Row(
                        [   
                            ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.RED_500, size=16) if estoque_baixo else ft.Container(width=0),
                            ft.Text(f"{estoque}/{estoque_minimo}", color=cor_estoque)
                        ],
                        spacing=2
                    )
                )
                
                self.produtos_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(produto.get('codigo', ''), color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(produto.get('nome', ''), color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(produto.get('descricao', '') or "-", color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(f"MT {produto.get('preco_custo', 0):.2f}", color=ft.colors.GREY_900)),
                            ft.DataCell(ft.Text(f"MT {produto.get('preco_venda', 0):.2f}", color=ft.colors.GREY_900)),
                            celula_estoque,
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
            
            self._safe_update()
            
        except Exception as e:
            print(f"❌ Erro no repositório híbrido ao carregar produtos: {e}")
            # Fallback para método direto em caso de erro
            self.carregar_produtos_fallback(busca)
    
    def carregar_produtos_fallback(self, busca=""):
        """Método de fallback para carregar produtos diretamente do banco local."""
        try:
            query = """
                SELECT 
                    id, uuid, codigo, nome, descricao,
                    preco_custo, preco_venda, estoque, estoque_minimo,
                    ativo, categoria_id, venda_por_peso
                FROM produtos 
                WHERE (LOWER(nome) LIKE ? OR LOWER(codigo) LIKE ?)
                    AND ativo = 1
            """
            
            params = [f"%{busca.lower()}%", f"%{busca.lower()}%"]
            
            if self.filtrar_estoque_baixo:
                query += " AND estoque <= estoque_minimo"
                
            query += " ORDER BY nome"
            
            produtos = self.db.fetchall(query, params)
            
            self.produtos_table.rows.clear()
            for produto in produtos:
                estoque_baixo = produto['estoque'] <= produto['estoque_minimo']
                cor_estoque = ft.colors.RED_500 if estoque_baixo else ft.colors.GREY_900
                
                celula_estoque = ft.DataCell(
                    ft.Row([   
                        ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.RED_500, size=16) if estoque_baixo else ft.Container(width=0),
                        ft.Text(f"{produto['estoque']}/{produto['estoque_minimo']}", color=cor_estoque)
                    ], spacing=2)
                )
                
                self.produtos_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(produto['codigo'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(produto['nome'], color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(produto['descricao'] or "-", color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(f"MT {produto['preco_custo']:.2f}", color=ft.colors.GREY_900)),
                        ft.DataCell(ft.Text(f"MT {produto['preco_venda']:.2f}", color=ft.colors.GREY_900)),
                        celula_estoque,
                        ft.DataCell(ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT, icon_color=ft.colors.BLUE, tooltip="Editar", data=produto, on_click=self.editar_produto),
                            ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED, tooltip="Excluir", data=produto, on_click=self.excluir_produto)
                        ]))
                    ])
                )
            self._safe_update()
        except Exception as e:
            print(f"Erro no fallback ao carregar produtos: {e}")

    def salvar_produto(self, e):
        """Salva produto usando o repositório híbrido."""
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

            # Converter valores com tratamento para nulos
            try:
                preco_custo = float(self.preco_custo_field.value or 0)
                preco_venda = float(self.preco_venda_field.value or 0)
                estoque = int(float(self.estoque_field.value or 0))
                estoque_minimo = int(float(self.estoque_minimo_field.value or 0))
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
                'venda_por_peso': self.venda_por_peso_switch.value,
                'unidade_medida': 'kg' if self.venda_por_peso_switch.value else 'un'
            }

            # Usar repositório híbrido para salvar (versão síncrona)
            try:
                if self.produto_em_edicao:
                    # Deixar o repositório tratar UUID ausente (gera e persiste automaticamente)
                    resultado = self.produto_repository.update(self.produto_em_edicao, dados)
                    if not resultado:
                        raise ValueError("Falha ao atualizar: retorno vazio do repositório")
                    print(f"✅ Produto atualizado via repositório híbrido: {resultado.get('nome')}")
                else:
                    # Criar novo produto
                    resultado = self.produto_repository.create(dados)
                    if not resultado:
                        raise ValueError("Falha ao criar: retorno vazio do repositório")
                    print(f"✅ Produto criado via repositório híbrido: {resultado.get('nome')}")
                    print(f"   UUID: {resultado.get('uuid')}")
                    print(f"   Sincronizado: {'Sim' if resultado.get('synced') else 'Não'}")
                
                self.mostrar_sucesso("Produto salvo com sucesso!")
                self.limpar_formulario(None)
                
                # Aguardar um pouco antes de recarregar para evitar erro de UI
                try:
                    if hasattr(self, 'page') and self.page and hasattr(self, 'produtos_table'):
                        import time
                        time.sleep(0.2)
                        self.carregar_produtos()
                except Exception as ui_error:
                    print(f"⚠️ Erro ao recarregar produtos na UI: {ui_error}")
                    # Tentar recarregar após um delay maior
                    try:
                        import time
                        time.sleep(0.5)
                        if hasattr(self, 'page') and self.page:
                            self.page.update()
                    except:
                        pass
                
            except Exception as e:
                print(f"❌ Erro no repositório híbrido: {e}")
                self.mostrar_erro(f"Erro ao salvar produto: {str(e)}")

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
            # Excluir via repositório híbrido (faz soft delete local e tenta deletar no servidor)
            sucesso = False
            try:
                sucesso = self.produto_repository.delete(produto['id'])
            except Exception as repo_err:
                print(f"[EXCLUIR] Falha no repositório ao excluir produto ID {produto['id']}: {repo_err}")
            
            # Atualizar a lista imediatamente após excluir (tempo real)
            self.carregar_produtos()
            if hasattr(self, 'page') and self.page:
                try:
                    self.page.update()
                except Exception as ui_err:
                    print(f"[UI] Aviso ao atualizar após exclusão: {ui_err}")
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Produto excluído com sucesso!" if sucesso else "⚠️ Produto marcado como excluído localmente."),
                    bgcolor=ft.colors.GREEN if sucesso else ft.colors.AMBER,
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

    def alternar_filtro_estoque_baixo(self, e):
        """Alterna o filtro de produtos com estoque baixo"""
        self.filtrar_estoque_baixo = e.control.value
        self.carregar_produtos(self.busca_field.value)

    def filtrar_produtos(self, e):
        termo = e.control.value.lower()
        self.carregar_produtos(termo)

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