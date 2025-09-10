import flet as ft
import traceback
from database.database import Database
from views.generic_header import create_header
import os
import httpx
if os.getenv('WEB_MODE') == 'true':
    from utils.rongta_printer_web import RongtaPrinter
else:
    from utils.rongta_printer import RongtaPrinter
from datetime import datetime

class PDVView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.BLUE_50  # Adicionar fundo claro
        self.usuario = usuario
        self.db = Database()
        self.printer = RongtaPrinter()
        self.ultima_venda_id = None
        
        # Inicializar vendas ativas
        self.vendas_ativas = []
        self.venda_atual_index = -1
        
        # Botões para gerenciar múltiplas vendas
        self.btn_nova_venda = ft.ElevatedButton(
            "Nova Venda",
            icon=ft.icons.ADD_SHOPPING_CART,
            on_click=self.iniciar_nova_venda,
            style=ft.ButtonStyle(
                color=ft.colors.BLACK,  # Texto preto
                bgcolor=ft.colors.GREEN
            )
        )
        
        self.vendas_tabs = ft.Tabs(
            selected_index=0,
            on_change=self.mudar_venda,
            tabs=[]
        )
        
        # Carregar configurações da impressora
        self.printer_config = self.db.get_printer_config() or {}
        self.imprimir_automatico = bool(self.printer_config.get('imprimir_automatico', 0))
        
        self.itens = []
        self.total_venda = 0.0
        # Cache de produtos (especialmente para modo web)
        self._produtos_cache = []

        # Campo de busca
        self.busca_field = ft.TextField(
            label="Buscar produto",
            width=200,
            prefix_icon=ft.icons.SEARCH,
            on_change=self.filtrar_produtos,
            bgcolor=ft.colors.WHITE,
            color=ft.colors.BLACK,
            label_style=ft.TextStyle(color=ft.colors.BLACK)
        )

        # Tabela de produtos disponíveis
        self.produtos_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Produto", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Descrição", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Preço", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Estoque", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK))
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.BLACK26),
            border_radius=10,
            heading_row_height=50,
            column_spacing=20,
            width=700
        )

        # Tabela do carrinho
        self.carrinho_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Produto", color=ft.colors.BLACK)),
                ft.DataColumn(ft.Text("Ações", color=ft.colors.BLACK))
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.BLACK26),
            border_radius=10,
            heading_row_height=50,
            column_spacing=20
        )

        # Total e pagamento
        self.total_text = ft.Text(
            "Total: MT 0,00", 
            size=20, 
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_900
        )
        
        self.forma_pagamento = ft.Dropdown(
            label="Forma de Pagamento",
            width=200,
            height=50,  # Altura fixa para o campo
            content_padding=ft.padding.only(left=10, right=30),  # Padding para a seta
            text_size=14,
            border_color=ft.colors.GREY_400,
            focused_border_color=ft.colors.BLUE,
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            options=[
                ft.dropdown.Option("Dinheiro"),
                ft.dropdown.Option("M-PESA"),
                ft.dropdown.Option("E-Mola"),
                ft.dropdown.Option("Cartão POS"),
                ft.dropdown.Option("Transferência Bancária"),
                ft.dropdown.Option("Millennium BIM"),
                ft.dropdown.Option("BCI"),
                ft.dropdown.Option("Standard Bank"),
                ft.dropdown.Option("Absa Bank"),
                ft.dropdown.Option("Letshego"),
                ft.dropdown.Option("MyBucks"),
            ],
            on_change=self.forma_pagamento_changed
        )

        # Campo valor recebido
        self.valor_recebido_field = ft.TextField(
            label="Valor Recebido",
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_style=ft.TextStyle(color=ft.colors.BLACK),
            label_style=ft.TextStyle(color=ft.colors.BLACK),
            cursor_color=ft.colors.BLACK,
            focused_border_color=ft.colors.BLUE,
            border_color=ft.colors.GREY_400,
            on_change=self.calcular_troco
        )

        # Campo de troco
        self.troco_text = ft.Container(
            content=ft.Text(
                "Troco: MT 0.00",
                size=18,  
                color=ft.colors.GREEN_800,  
                weight=ft.FontWeight.BOLD,
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=8),  
            margin=ft.margin.only(left=10),  
            bgcolor=ft.colors.GREEN_50,  
            border_radius=5,  
            visible=False  
        )

        # Botão finalizar
        self.btn_finalizar = ft.ElevatedButton(
            "Finalizar Venda",
            icon=ft.icons.SHOPPING_CART_CHECKOUT,
            on_click=self.finalizar_venda,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN
            )
        )

        # Botão de imprimir recibo acoplado ao último ID de venda
        self.btn_imprimir_recibo = ft.ElevatedButton(
            "Imprimir Recibo",
            icon=ft.icons.PRINT,
            on_click=lambda _: self.imprimir_recibo(self.ultima_venda_id),
            disabled=True
        )

        # Inicializa o diálogo de conclusão
        self.dialog_concluir = ft.AlertDialog(
            title=ft.Text("Venda Concluída!"),
            content=ft.Column([
                ft.Text("Venda finalizada com sucesso!"),
                self.btn_imprimir_recibo
            ], spacing=10),
            actions=[
                ft.TextButton("Editar Venda", on_click=self.editar_venda),
                ft.TextButton("Concluir", on_click=self.concluir_venda),
                ft.TextButton("Nova Venda", on_click=self.nova_venda),
                ft.TextButton("Fechar", on_click=self.fechar_venda_atual)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        # Adicionar alertas de estoque baixo
        self.estoque_minimo_alert = ft.Banner(
            bgcolor=ft.colors.AMBER_100,
            leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.ORANGE, size=40),
            content=ft.Text(
                "Existem produtos com estoque baixo!",
                color=ft.colors.ORANGE_900
            ),
            actions=[
                ft.TextButton("Ver Produtos", on_click=self.mostrar_produtos_estoque_baixo),
                ft.TextButton("Fechar", on_click=lambda e: setattr(self.estoque_minimo_alert, 'open', False))
            ]
        )

    def build(self):
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/dashboard"),
                    icon_color=ft.colors.WHITE
                ),
                ft.Icon(
                    name=ft.icons.POINT_OF_SALE,  # Adicionado ícone de PDV
                    size=30,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "PDV",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Ponto de Venda",
                    size=16,
                    color=ft.colors.WHITE  # Alterado para branco
                )
            ]),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
            ),
            padding=20,
            border_radius=10
        )

        return ft.Column(
            controls=[
                header,
                ft.Row(
                    [
                        self.btn_nova_venda,
                        self.vendas_tabs
                    ],
                    alignment=ft.MainAxisAlignment.START
                ),
                ft.Row([
                    # Seção de produtos disponíveis (lado esquerdo)
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Produtos Disponíveis",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLUE_900
                            ),
                            ft.Row(
                                [self.busca_field],
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [self.produtos_table],
                                    scroll=ft.ScrollMode.AUTO
                                ),
                                padding=10,
                                height=400,
                                width=750,
                                border=ft.border.all(1, ft.colors.BLACK26),
                                border_radius=10
                            )
                        ]),
                        padding=20,
                        bgcolor=ft.colors.WHITE,
                        border_radius=10,
                        margin=ft.margin.only(left=20, right=20),
                        width=750
                    ),
                    
                    # Seção do carrinho (lado direito)
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Carrinho",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLUE_900
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Container(
                                            content=self.carrinho_table,
                                        )
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=10,
                                    expand=True
                                ),
                                padding=10,
                                height=250,
                                width=400,
                                margin=ft.margin.only(left=20, right=20),
                                border=ft.border.all(1, ft.colors.BLACK26),
                                border_radius=10
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.Divider(height=1, color=ft.colors.BLACK26),
                                    ft.Row([
                                        ft.Container(
                                            content=ft.Column([
                                                self.forma_pagamento,
                                                self.valor_recebido_field
                                            ],
                                            spacing=10,
                                            ),
                                            expand=True
                                        ),
                                        ft.Container(
                                            content=ft.Column([
                                                self.total_text,
                                                self.troco_text,
                                                self.btn_finalizar
                                            ],
                                            spacing=10,
                                            horizontal_alignment=ft.CrossAxisAlignment.END
                                            ),
                                            expand=True
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.START
                                    )
                                ]),
                                padding=ft.padding.only(top=10, bottom=10),
                                margin=ft.margin.only(top=10)
                            )
                        ],
                        spacing=10
                        ),
                        padding=10,
                        bgcolor=ft.colors.WHITE,
                        border_radius=10,
                        margin=ft.margin.only(left=20, right=20),
                        width=400
                    )
                ], 
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=40
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    def did_mount(self):
        self.page.bgcolor = ft.colors.BLUE_GREY_50
        self.page.update()
        self.carregar_produtos()
        
        # Configurar evento para salvar vendas antes de sair (somente desktop)
        try:
            if not self._is_web():
                self.page.on_window_event = self.handle_window_event
        except Exception as e:
            print(f"[PDV] Ignorando on_window_event no modo web: {e}")

    def handle_window_event(self, e):
        """Manipula eventos da janela"""
        if e.data == "close":
            # Salvar todas as vendas pendentes
            for i in range(len(self.vendas_ativas)):
                self.venda_atual_index = i
                self.carregar_venda_atual()
                self.salvar_venda_pendente()

    def _is_web(self) -> bool:
        try:
            return os.getenv('WEB_MODE', '').lower() == 'true'
        except Exception:
            return False

    def _get_backend_url(self) -> str:
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    conf = json.load(f)
                    return conf.get('server_url', os.getenv('BACKEND_URL', 'http://localhost:8000'))
        except Exception:
            pass
        return os.getenv('BACKEND_URL', 'http://localhost:8000')

    def _get_api_base(self) -> str:
        base = (self._get_backend_url() or '').rstrip('/')
        if base.endswith('/api'):
            return base
        if base.endswith('/api/'):
            return base[:-1]
        return base + '/api'

    def filtrar_produtos(self, e):
        try:
            busca = self.busca_field.value.lower() if self.busca_field.value else ""
            
            # Fonte de produtos: cache (web) ou banco local
            if self._is_web():
                produtos = [p for p in self._produtos_cache if (
                    (p.get('estoque', 0) or 0) > 0 and (
                        (p.get('codigo') or '').lower().find(busca) >= 0 or
                        (p.get('nome') or '').lower().find(busca) >= 0 or
                        (p.get('descricao') or '').lower().find(busca) >= 0
                    )
                )] if busca else self._produtos_cache
            else:
                # Se a busca estiver vazia, recarregar todos os produtos
                if not busca:
                    self.carregar_produtos()
                    return
                produtos = self.db.fetchall(
                    """
                    SELECT 
                        id, 
                        codigo, 
                        nome, 
                        descricao,
                        preco_venda,
                        estoque,
                        venda_por_peso,
                        unidade_medida
                    FROM produtos 
                    WHERE ativo = 1 
                    AND estoque > 0
                    AND (
                        LOWER(codigo) LIKE ? 
                        OR LOWER(nome) LIKE ? 
                        OR LOWER(descricao) LIKE ?
                    )
                    ORDER BY nome
                    """,
                    (f"%{busca}%", f"%{busca}%", f"%{busca}%")
                )
            
            self.produtos_table.rows.clear()
            
            for produto in produtos:
                # Ajustar exibição do preço e estoque baseado no tipo de venda
                venda_por_peso_val = produto['venda_por_peso'] if isinstance(produto, dict) else produto['venda_por_peso']
                preco_base = produto['preco_venda'] if isinstance(produto, dict) else produto['preco_venda']
                estoque_base = produto['estoque'] if isinstance(produto, dict) else produto['estoque']
                if int(venda_por_peso_val) == 1:
                    preco_display = f"MT {float(preco_base):.2f}/KG"
                    estoque_display = f"{float(estoque_base):.3f} KG"
                else:
                    preco_display = f"MT {float(preco_base):.2f}"
                    estoque_display = str(estoque_base)
                
                self.produtos_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text((produto['codigo'] if isinstance(produto, dict) else produto['codigo']), color=ft.colors.BLACK)),
                            ft.DataCell(
                                ft.TextButton(
                                    text=(produto['nome'] if isinstance(produto, dict) else produto['nome']),
                                    style=ft.ButtonStyle(color=ft.colors.BLACK),
                                    data=(produto if isinstance(produto, dict) else dict(produto)),
                                    on_click=self.mostrar_detalhes_produto
                                )
                            ),
                            ft.DataCell(ft.Text((produto.get('descricao') if isinstance(produto, dict) else (produto['descricao'] or '')), color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(preco_display, color=ft.colors.BLACK)),
                            ft.DataCell(ft.Text(estoque_display, color=ft.colors.BLACK)),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.ADD_SHOPPING_CART,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Adicionar ao Carrinho",
                                        data=(produto if isinstance(produto, dict) else dict(produto)),
                                        on_click=self.adicionar_ao_carrinho
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.INFO_OUTLINE,
                                        icon_color=ft.colors.BLUE_900,
                                        tooltip="Ver detalhes",
                                        data=(produto if isinstance(produto, dict) else dict(produto)),
                                        on_click=self.mostrar_detalhes_produto
                                    )
                                ])
                            )
                        ]
                    )
                )
            
            self.update()
            
        except Exception as error:
            print(f"Erro ao filtrar produtos: {error}")
            self.mostrar_erro("Erro ao filtrar produtos!")

    def carregar_produtos(self):
        """Carrega a lista de produtos"""
        try:
            if self._is_web():
                # Buscar produtos do backend e preencher cache
                base = self._get_api_base()
                produtos = []
                try:
                    url1 = f"{base}/produtos/"
                    url2 = f"{base}/produtos"
                    print(f"[WEB] Buscando produtos em: {url1}")
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.get(url1)
                        if resp.status_code == 404:
                            print(f"[WEB] 404 em {url1}, tentando {url2}")
                            resp = client.get(url2)
                        if resp.status_code == 200:
                            dados = resp.json() or []
                            for p in dados:
                                try:
                                    produtos.append({
                                        'id': p.get('id'),
                                        'codigo': p.get('codigo') or '',
                                        'nome': p.get('nome') or '',
                                        'descricao': p.get('descricao') or '',
                                        'preco_venda': float(p.get('preco_venda') or 0),
                                        'estoque': float(p.get('estoque') or 0),
                                        'venda_por_peso': 1 if p.get('venda_por_peso') in (1, True, '1', 'true', 'True') else 0,
                                        'unidade_medida': p.get('unidade_medida') or 'un'
                                    })
                                except Exception:
                                    pass
                        else:
                            print(f"[WEB] Falha ao buscar produtos ({resp.status_code}) em {url1} e {url2}")
                except Exception as ex:
                    print(f"[WEB] Erro ao buscar produtos: {ex}")

                # Armazena no cache e continua fluxo de UI
                self._produtos_cache = [p for p in produtos if p.get('estoque', 0) > 0]
            else:
                # Verificar se a tabela produtos existe
                tabela_existe = self.db.fetchone("""SELECT name FROM sqlite_master WHERE type='table' AND name='produtos'""")
                if not tabela_existe:
                    print("Tabela de produtos não existe!")
                    self.mostrar_erro("Erro: Tabela de produtos não encontrada!")
                    return
                
                # Verificar estrutura da tabela
                try:
                    colunas = self.db.fetchall("PRAGMA table_info(produtos)")
                    colunas_nomes = [coluna['name'] for coluna in colunas]
                    colunas_necessarias = ['id', 'codigo', 'nome', 'descricao', 'preco_venda', 'estoque', 'venda_por_peso', 'unidade_medida']
                    for coluna in colunas_necessarias:
                        if coluna not in colunas_nomes:
                            print(f"Coluna {coluna} não encontrada na tabela produtos")
                            self.mostrar_erro(f"Erro: Coluna {coluna} não encontrada na tabela produtos")
                            return
                except Exception as e:
                    print(f"Erro ao verificar estrutura da tabela: {e}")
                
                # Consulta com tratamento de tipo de dados e join com categorias/fornecedores
                produtos = self.db.fetchall(
                    """
                    SELECT 
                        p.id, 
                        p.codigo, 
                        p.nome, 
                        p.descricao,
                        CAST(p.preco_venda AS REAL) as preco_venda,
                        CAST(p.estoque AS REAL) as estoque,
                        CAST(p.venda_por_peso AS INTEGER) as venda_por_peso,
                        p.unidade_medida,
                        c.nome as categoria_nome,
                        f.nome as fornecedor_nome
                    FROM produtos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
                    WHERE p.ativo = 1 
                    AND CAST(p.estoque AS REAL) > 0
                    ORDER BY p.nome
                    """
                )
            
            self.produtos_table.rows.clear()
            
            if not produtos:
                print("Nenhum produto encontrado ou erro na consulta")
                return
                
            for produto in (self._produtos_cache if self._is_web() else produtos):
                try:
                    # Ajustar exibição do preço e estoque baseado no tipo de venda
                    venda_por_peso = int((produto['venda_por_peso'] if isinstance(produto, dict) else produto['venda_por_peso']) or 0)
                    preco_venda = float((produto['preco_venda'] if isinstance(produto, dict) else produto['preco_venda']) or 0)
                    estoque = float((produto['estoque'] if isinstance(produto, dict) else produto['estoque']) or 0)
                    
                    if venda_por_peso == 1:
                        preco_display = f"MT {preco_venda:.2f}/KG"
                        estoque_display = f"{estoque:.3f} KG"
                    else:
                        preco_display = f"MT {preco_venda:.2f}"
                        estoque_display = str(estoque)
                    
                    self.produtos_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text((produto['codigo'] if isinstance(produto, dict) else produto['codigo']), color=ft.colors.BLACK)),
                                ft.DataCell(
                                    ft.TextButton(
                                        text=(produto['nome'] if isinstance(produto, dict) else produto['nome']),
                                        style=ft.ButtonStyle(color=ft.colors.BLACK),
                                        data=(produto if isinstance(produto, dict) else dict(produto)),
                                        on_click=self.mostrar_detalhes_produto
                                    )
                                ),
                                ft.DataCell(ft.Text((produto.get('descricao') if isinstance(produto, dict) else (produto['descricao'] or '')), color=ft.colors.BLACK)),
                                ft.DataCell(ft.Text(preco_display, color=ft.colors.BLACK)),
                                ft.DataCell(ft.Text(estoque_display, color=ft.colors.BLACK)),
                                ft.DataCell(
                                    ft.Row([
                                        ft.IconButton(
                                            icon=ft.icons.ADD_SHOPPING_CART,
                                            icon_color=ft.colors.BLUE,
                                            tooltip="Adicionar ao Carrinho",
                                            data=(produto if isinstance(produto, dict) else dict(produto)),
                                            on_click=self.adicionar_ao_carrinho
                                        ),
                                        ft.IconButton(
                                            icon=ft.icons.INFO_OUTLINE,
                                            icon_color=ft.colors.BLUE_900,
                                            tooltip="Ver detalhes",
                                            data=(produto if isinstance(produto, dict) else dict(produto)),
                                            on_click=self.mostrar_detalhes_produto
                                        )
                                    ])
                                )
                            ]
                        )
                    )
                except Exception as item_error:
                    try:
                        produto_nome = produto['nome'] if 'nome' in produto else 'desconhecido'
                    except:
                        produto_nome = 'desconhecido'
                    print(f"Erro ao processar produto {produto_nome}: {item_error}")
            
            self.update()
            
        except Exception as error:
            print(f"Erro ao carregar produtos: {error}")
            self.mostrar_erro("Erro ao carregar produtos!")
            import traceback
            traceback.print_exc()

    def verificar_estoque_baixo(self):
        """Verifica produtos com estoque abaixo do mínimo"""
        try:
            produtos_baixos = self.db.fetchall("""
                SELECT id, codigo, nome, estoque, estoque_minimo
                FROM produtos
                WHERE estoque <= estoque_minimo
                AND ativo = 1
                ORDER BY nome
            """)
            
            if produtos_baixos:
                self.estoque_minimo_alert.open = True
                self.update()
            
        except Exception as e:
            print(f"Erro ao verificar estoque baixo: {e}")

    def mostrar_produtos_estoque_baixo(self, e):
        """Mostra diálogo com produtos em estoque baixo"""
        try:
            produtos = self.db.fetchall("""
                SELECT codigo, nome, estoque, estoque_minimo
                FROM produtos
                WHERE estoque <= estoque_minimo
                AND ativo = 1
                ORDER BY nome
            """)
            
            conteudo = ft.Column(
                controls=[
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Código")),
                            ft.DataColumn(ft.Text("Produto")),
                            ft.DataColumn(ft.Text("Estoque")),
                            ft.DataColumn(ft.Text("Mínimo"))
                        ],
                        rows=[
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(p['codigo'])),
                                    ft.DataCell(ft.Text(p['nome'])),
                                    ft.DataCell(ft.Text(str(p['estoque']))),
                                    ft.DataCell(ft.Text(str(p['estoque_minimo'])))
                                ]
                            ) for p in produtos
                        ]
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                height=300
            )
            
            self.page.dialog = ft.AlertDialog(
                title=ft.Text("Produtos com Estoque Baixo"),
                content=conteudo,
                actions=[
                    ft.TextButton("Fechar", on_click=lambda e: setattr(self.page.dialog, 'open', False))
                ]
            )
            
            self.page.dialog.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao mostrar produtos com estoque baixo: {e}")
            
    def fechar_dialogo(self, dialog):
        """Fecha o diálogo modal"""
        dialog.open = False
        self.page.update()

    def mostrar_erro(self, mensagem):
        """Método centralizado para exibir erros"""
        dialog = ft.AlertDialog(
            title=ft.Text("Erro", color=ft.colors.RED),
            content=ft.Text(mensagem, color=ft.colors.BLACK),
            actions=[
                ft.TextButton(
                    "OK",
                    on_click=lambda e: self.fechar_dialogo(dialog)
                )
            ]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def mostrar_detalhes_produto(self, e):
        """Mostra um modal com detalhes do produto"""
        try:
            produto = e.control.data
            produto_id = produto['id']
            
            # Buscar informações detalhadas do produto
            produto_detalhes = self.db.fetchone("""
                SELECT p.*, c.nome as categoria_nome, f.nome as fornecedor_nome
                FROM produtos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
                WHERE p.id = ?
            """, (produto_id,))
            
            if not produto_detalhes:
                produto_detalhes = produto  # Usar dados básicos se não encontrar detalhes
                
            # Converter sqlite3.Row para dicionário se necessário
            if hasattr(produto, 'keys'):
                produto = dict(produto)
            if hasattr(produto_detalhes, 'keys'):
                produto_detalhes = dict(produto_detalhes)
                
            # Formatar preço e estoque baseado no tipo de venda
            venda_por_peso = produto.get('venda_por_peso', 0) if isinstance(produto, dict) else (produto['venda_por_peso'] if 'venda_por_peso' in produto else 0)
            
            if venda_por_peso == 1:
                preco_display = f"MT {float(produto.get('preco_venda', 0)):.2f}/KG"
                estoque_display = f"{float(produto.get('estoque', 0)):.3f} KG"
            else:
                preco_display = f"MT {float(produto.get('preco_venda', 0)):.2f}"
                estoque_display = str(produto.get('estoque', 0))
                
            # Criar conteúdo do modal
            conteudo = ft.Column([
                # Cabeçalho com nome do produto
                ft.Container(
                    content=ft.Text(
                        produto['nome'],
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    ),
                    padding=15,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
                    ),
                    border_radius=ft.border_radius.only(top_left=10, top_right=10)
                ),
                
                # Informações principais
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Código:", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                            ft.Text(produto['codigo'], color=ft.colors.BLACK)
                        ]),
                        ft.Row([
                            ft.Text("Preço:", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                            ft.Text(preco_display, color=ft.colors.GREEN)
                        ]),
                        ft.Row([
                            ft.Text("Estoque:", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                            ft.Text(estoque_display, color=ft.colors.BLUE)
                        ]),
                        ft.Divider(),
                        ft.Text("Descrição:", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                        ft.Text(produto['descricao'] or "Sem descrição", color=ft.colors.BLACK)
                    ], spacing=10),
                    padding=20,
                    bgcolor=ft.colors.WHITE
                ),
                
                # Informações adicionais
                ft.Container(
                    content=ft.Column([
                        ft.Text("Informações Adicionais", weight=ft.FontWeight.BOLD, size=16, color=ft.colors.BLACK),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Categoria:", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                            ft.Text(str(produto_detalhes.get('categoria_nome', 'Não categorizado')), color=ft.colors.BLACK)
                        ]),
                        ft.Row([
                            ft.Text("Fornecedor:", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                            ft.Text(str(produto_detalhes.get('fornecedor_nome', 'Não especificado')), color=ft.colors.BLACK)
                        ]),
                        ft.Row([
                            ft.Text("Tipo de Venda:", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                            ft.Text("Por Peso" if produto.get('venda_por_peso', 0) == 1 else "Unitário", color=ft.colors.BLACK)
                        ]),
                        ft.Row([
                            ft.Text("Unidade de Medida:", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                            ft.Text(produto.get('unidade_medida', "un").upper(), color=ft.colors.BLACK)
                        ])
                    ], spacing=10),
                    padding=20,
                    bgcolor=ft.colors.BLUE_50
                ),
                
                # Container de espaçamento inferior
                ft.Container(
                    content=ft.Row([], alignment=ft.MainAxisAlignment.END),
                    padding=15,
                    bgcolor=ft.colors.WHITE,
                    border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
                )
            ], spacing=0)
            
            # Criar e mostrar o modal
            dialog = ft.AlertDialog(
                content=conteudo,
                actions=[
                    ft.TextButton(
                        "Fechar",
                        on_click=lambda e: self.fechar_dialogo(dialog)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao mostrar detalhes do produto: {e}")
            self.mostrar_erro("Erro ao mostrar detalhes do produto!")
            
    def adicionar_ao_carrinho_e_fechar(self, produto, e):
        """Adiciona produto ao carrinho e fecha o modal"""
        try:
            # Adicionar ao carrinho
            self.adicionar_ao_carrinho(ft.ControlEvent(control=ft.IconButton(data=produto)))
            
            # Fechar o modal
            self.page.dialog.open = False
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao adicionar ao carrinho e fechar: {e}")
            self.mostrar_erro("Erro ao adicionar produto ao carrinho!")

    def adicionar_ao_carrinho(self, e):
        """Adiciona produto ao carrinho"""
        try:
            produto = dict(e.control.data)  # Converter sqlite3.Row para dicionário
            
            if self.venda_atual_index < 0:
                self.iniciar_nova_venda()
            
            # Se for produto vendido por peso, mostrar diálogo melhorado
            if produto['venda_por_peso'] == 1:
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
                            self.mostrar_erro("Valor ou peso inválido!")
                            return
                            
                        if peso > produto['estoque']:
                            self.mostrar_erro(f"Estoque insuficiente! Disponível: {produto['estoque']:.3f} KG")
                            return
                            
                        # Adicionar ao carrinho
                        self.itens.append({
                            'id': produto['id'],
                            'codigo': produto['codigo'],
                            'nome': produto['nome'],
                            'quantidade': peso,  # Peso em KG
                            'preco': produto['preco_venda'],  # Preço por KG
                            'subtotal': valor,
                            'venda_por_peso': True,
                            'unidade_medida': 'kg'
                        })
                        
                        self.atualizar_carrinho()
                        close_dialog(None)
                        
                    except ValueError:
                        self.mostrar_erro("Valores inválidos!")
                
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
                            on_click=lambda e: confirmar_venda(e),
                            style=ft.ButtonStyle(
                                color=ft.colors.GREEN
                            )
                        )
                    ],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                self.page.dialog.open = True
                self.page.update()
                return
                
            # Continua com o fluxo normal para produtos não vendidos por peso
            # Verificar estoque disponível
            produto_db = self.db.fetchone("""
                SELECT estoque FROM produtos WHERE id = ?
            """, (produto['id'],))
            
            if not produto_db:
                # Produto não encontrado no banco local, usar estoque do cache
                estoque_atual = produto.get('estoque', 0)
            else:
                estoque_atual = produto_db['estoque']
            
            # Procurar se o produto já existe no carrinho
            produto_existente = None
            for item in self.itens:
                if item['id'] == produto['id']:
                    produto_existente = item
                    break
            
            # Se o produto já existe, apenas aumenta a quantidade
            if produto_existente:
                # Verificar se há estoque suficiente
                if produto_existente['quantidade'] + 1 > estoque_atual:
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text("Produto sem estoque disponível!"),
                            bgcolor=ft.colors.RED_700
                        )
                    )
                    return
                    
                produto_existente['quantidade'] += 1
                produto_existente['subtotal'] = produto_existente['quantidade'] * produto_existente['preco']
            else:
                # Se não existe, adiciona novo item
                self.itens.append({
                    'id': produto['id'],
                    'codigo': produto['codigo'],
                    'nome': produto['nome'],
                    'quantidade': 1,
                    'preco': produto['preco_venda'],
                    'subtotal': produto['preco_venda'],
                    'venda_por_peso': False,
                    'unidade_medida': produto.get('unidade_medida', 'un')
                })
            
            # Atualizar interface
            self.atualizar_carrinho()
            
            # Atualizar quantidade do produto na tabela
            self.atualizar_quantidade_produto(produto['id'])
            
            self.update()
            
        except Exception as e:
            print(f"Erro ao adicionar ao carrinho: {e}")
            print(f"Produto: {produto}")  # Debug

    def atualizar_quantidade_produto(self, produto_id):
        """Atualiza a quantidade exibida do produto baseado no carrinho"""
        try:
            # Buscar produto completo
            produto = self.db.fetchone("""
                SELECT id, codigo, estoque FROM produtos WHERE id = ?
            """, (produto_id,))
            
            if not produto:
                # Se não encontrou no banco local, buscar no cache (modo web)
                if hasattr(self, '_produtos_cache'):
                    produto_cache = next((p for p in self._produtos_cache if p['id'] == produto_id), None)
                    if produto_cache:
                        produto = produto_cache
                    else:
                        return
                else:
                    return
            
            # Calcular quantidade no carrinho
            qtd_carrinho = sum(
                item['quantidade'] for item in self.itens 
                if item['id'] == produto_id
            )
            
            # Atualizar exibição na tabela
            for row in self.produtos_table.rows:
                if row.cells[0].content.value == produto['codigo']:
                    estoque_disponivel = produto['estoque'] - qtd_carrinho
                    row.cells[4].content.value = str(estoque_disponivel)
                    row.cells[4].content.color = ft.colors.RED if estoque_disponivel < 10 else ft.colors.BLACK
                    self.produtos_table.update()  # Forçar atualização da tabela
                    break
                
        except Exception as e:
            print(f"Erro ao atualizar quantidade do produto: {e}")

    def atualizar_carrinho(self):
        """Atualiza a exibição do carrinho e totais"""
        try:
            # Limpar linhas existentes
            self.carrinho_table.rows.clear()
            
            # Adicionar todos os itens
            for item in self.itens:
                self.carrinho_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.TextButton(
                                text=item['nome'],
                                on_click=lambda e, item=item: self.mostrar_detalhes_produto_carrinho(item)
                            )),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.icons.INFO_OUTLINE,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Detalhes",
                                        data=item,
                                        on_click=lambda e, item=item: self.mostrar_detalhes_produto_carrinho(item),
                                        icon_size=20
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.EDIT,
                                        icon_color=ft.colors.BLUE,
                                        tooltip="Editar",
                                        data=item,
                                        on_click=self.editar_item,
                                        icon_size=20
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        icon_color=ft.colors.RED,
                                        tooltip="Remover",
                                        data=item,
                                        on_click=self.remover_item,
                                        icon_size=20
                                    )
                                ])
                            )
                        ]
                    )
                )
            
            # Atualizar total
            self.total_venda = sum(item['subtotal'] for item in self.itens)
            self.total_text.value = f"Total: MT {self.total_venda:.2f}"
            
            # Habilitar/desabilitar botão finalizar
            self.btn_finalizar.disabled = len(self.itens) == 0 or (
                self.forma_pagamento.value == "Dinheiro" and 
                (not self.valor_recebido_field.value or float(self.valor_recebido_field.value or 0) < self.total_venda)
            )
            
            # Atualizar exibição do estoque para todos os produtos
            for item in self.itens:
                self.atualizar_quantidade_produto(item['id'])
            
            self.update()
        except Exception as e:
            print(f"Erro ao atualizar carrinho: {e}")

    def mostrar_detalhes_produto_carrinho(self, item):
        """Mostra detalhes do produto do carrinho em um modal"""
        try:
            # Converter para dicionário se for um sqlite3.Row
            if hasattr(item, 'keys'):
                item = dict(item)
                
            # Buscar informações completas do produto no banco de dados
            produto_id = item.get('id')
            if not produto_id:
                self.mostrar_erro("ID do produto não encontrado!")
                return
                
            produto = self.db.fetchone("""
                SELECT p.*, c.nome as categoria, f.nome as fornecedor
                FROM produtos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
                WHERE p.id = ?
            """, (produto_id,))
            
            if not produto:
                self.mostrar_erro("Produto não encontrado!")
                return
                
            # Converter para dicionário se for um sqlite3.Row
            if hasattr(produto, 'keys'):
                produto = dict(produto)
            
            # Determinar tipo de venda e formatação de preço/estoque
            venda_por_peso = produto.get('venda_por_peso', 0)
            if venda_por_peso == 1:
                tipo_venda = "Por Peso"
                preco_display = f"MT {float(produto.get('preco_venda', 0)):.2f}/KG"
                estoque_display = f"{float(produto.get('estoque', 0)):.3f} KG"
                quantidade_display = f"{float(item.get('quantidade', 0)):.3f} KG"
            else:
                tipo_venda = "Unitário"
                preco_display = f"MT {float(produto.get('preco_venda', 0)):.2f}"
                estoque = float(produto.get('estoque', 0))
                quantidade = float(item.get('quantidade', 0))
                estoque_display = str(int(estoque)) if estoque == int(estoque) else str(estoque)
                quantidade_display = str(int(quantidade)) if quantidade == int(quantidade) else str(quantidade)
            
            # Calcular subtotal
            subtotal = float(item.get('subtotal', 0))
            
            # Criar e mostrar o modal
            def close_dialog(e):
                self.page.dialog.open = False
                self.page.update()

            # Criar linhas de informação com melhor formatação
            info_rows = [
                # Cabeçalho com nome do produto
                ft.Container(
                    content=ft.Text(
                        str(produto.get('nome', 'Produto sem nome')).upper(),
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_900,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.only(bottom=15)
                ),
                
                # Seção de informações principais
                ft.Container(
                    content=ft.Column([
                        # Primeira linha: Código e Preço
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        "CÓDIGO",
                                        size=12,
                                        color=ft.colors.GREY_600,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        str(produto.get('codigo', 'N/A')),
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.BLACK
                                    )
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=100,
                                padding=5,
                                border_radius=5,
                                bgcolor=ft.colors.GREY_100
                            ),
                            ft.VerticalDivider(width=20, color=ft.colors.TRANSPARENT),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        "PREÇO",
                                        size=12,
                                        color=ft.colors.GREY_600,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        preco_display,
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.GREEN_800
                                    )
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=120,
                                padding=5,
                                border_radius=5,
                                bgcolor=ft.colors.GREY_100
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        
                        # Segunda linha: Quantidade e Estoque
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        "QUANTIDADE",
                                        size=12,
                                        color=ft.colors.GREY_600,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        quantidade_display,
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.BLUE_800
                                    )
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=120,
                                padding=5,
                                border_radius=5,
                                bgcolor=ft.colors.BLUE_50
                            ),
                            ft.VerticalDivider(width=20, color=ft.colors.TRANSPARENT),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        "ESTOQUE DISPONÍVEL",
                                        size=12,
                                        color=ft.colors.GREY_600,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        estoque_display,
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.ORANGE_800
                                    )
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=150,
                                padding=5,
                                border_radius=5,
                                bgcolor=ft.colors.ORANGE_50
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        
                        # Valor total
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    "VALOR TOTAL",
                                    size=12,
                                    color=ft.colors.GREY_600,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(
                                    f"MT {subtotal:.2f}",
                                    size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.GREEN_800
                                )
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            margin=ft.margin.only(top=15, bottom=5),
                            padding=15,
                            border_radius=10,
                            bgcolor=ft.colors.GREEN_50,
                            border=ft.border.all(1, ft.colors.GREEN_100)
                        ),
                        
                        # Seção de informações adicionais
                        ft.Container(
                            content=ft.Column([
                                # Cabeçalho da seção
                                ft.Container(
                                    content=ft.Text(
                                        "INFORMAÇÕES ADICIONAIS",
                                        size=12,
                                        color=ft.colors.WHITE,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=5,
                                    bgcolor=ft.colors.BLUE_700,
                                    margin=ft.margin.only(bottom=10)
                                ),
                                
                                # Linhas de informação
                                ft.Column([
                                    self._create_info_row("Descrição", str(produto.get('descricao', 'Sem descrição'))),
                                    self._create_info_row("Categoria", str(produto.get('categoria', 'Sem categoria'))),
                                    self._create_info_row("Fornecedor", str(produto.get('fornecedor', 'Sem fornecedor'))),
                                    self._create_info_row("Tipo de venda", tipo_venda),
                                    self._create_info_row("Unidade de medida", str(produto.get('unidade_medida', 'Unidade')))
                                ], spacing=8)
                            ], spacing=5),
                            margin=ft.margin.only(top=10),
                            padding=15,
                            border_radius=10,
                            bgcolor=ft.colors.WHITE,
                            border=ft.border.all(1, ft.colors.GREY_200)
                        )
                    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
                )
            ]
            
            # Criar conteúdo principal
            content = ft.Container(
                width=450,  
                padding=20,
                bgcolor=ft.colors.WHITE,
                border_radius=10,
                content=ft.Column(
                    controls=info_rows,
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                )
            )
            
            # Criar e exibir o diálogo
            dialog = ft.AlertDialog(
                modal=True,
                content=content,
                actions_alignment=ft.MainAxisAlignment.END,
                actions=[
                    ft.ElevatedButton(
                        "FECHAR",
                        on_click=close_dialog,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_700,
                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                            shape=ft.RoundedRectangleBorder(radius=5)
                        )
                    )
                ]
            )
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao mostrar detalhes do produto: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            self.mostrar_erro(f"Erro ao carregar detalhes do produto: {str(e)}")
    
    def _create_info_row(self, label, value):
        """Cria uma linha de informação formatada para o modal de detalhes"""
        return ft.Container(
            content=ft.Row([
                ft.Text(
                    f"{label}:",
                    size=14,
                    color=ft.colors.GREY_700,
                    weight=ft.FontWeight.BOLD,
                    width=150
                ),
                ft.Container(
                    content=ft.Text(
                        value if value else "-",
                        size=14,
                        color=ft.colors.BLACK,
                        weight=ft.FontWeight.W_400
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=ft.colors.GREY_100,
                    border_radius=5,
                    expand=True
                )
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
            margin=ft.margin.only(bottom=5)
        )
        
    def remover_item(self, e):
        """Remove um item específico do carrinho"""
        try:
            item = e.control.data
            produto_id = item['id']
            
            # Encontrar o índice exato do item a ser removido
            for i, carrinho_item in enumerate(self.itens):
                if (carrinho_item['id'] == item['id'] and 
                    carrinho_item['quantidade'] == item['quantidade'] and
                    carrinho_item['subtotal'] == item['subtotal']):
                    # Remover apenas este item específico
                    self.itens.pop(i)
                    break
            
            # Atualizar carrinho
            self.atualizar_carrinho()
            
            # Restaurar quantidade do produto na tabela
            self.atualizar_quantidade_produto(produto_id)
            
            # Forçar atualização da interface
            self.update()
            
        except Exception as e:
            print(f"Erro ao remover item: {e}")

    def finalizar_venda(self, e):
        """Finaliza a venda atual"""
        try:
            if not self.itens:
                self.mostrar_erro("Adicione produtos ao carrinho!")
                return
            
            if not self.forma_pagamento.value:
                self.mostrar_erro("Selecione a forma de pagamento!")
                return
            
            if self.forma_pagamento.value == "Dinheiro":
                if not self.valor_recebido_field.value:
                    self.mostrar_erro("Digite o valor recebido!")
                    return
                    
                valor_recebido = float(self.valor_recebido_field.value)
                if valor_recebido < self.total_venda:
                    self.mostrar_erro("Valor recebido menor que o total!")
                    return
            
            # Iniciar transação
            self.db.conn.execute("BEGIN TRANSACTION")
            
            try:
                # Inserir venda
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    INSERT INTO vendas (
                        usuario_id, total, forma_pagamento,
                        valor_recebido, troco, data_venda
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    self.usuario['id'],
                    self.total_venda,
                    self.forma_pagamento.value,
                    float(self.valor_recebido_field.value or 0),
                    float(self.valor_recebido_field.value or 0) - self.total_venda
                ))
                
                venda_id = cursor.lastrowid
                
                # Inserir itens e atualizar estoque
                for item in self.itens:
                    # Buscar preço de custo atual
                    produto = self.db.fetchone("""
                        SELECT preco_custo FROM produtos WHERE id = ?
                    """, (item['id'],))
                    
                    # Inserir item
                    cursor.execute("""
                        INSERT INTO itens_venda (
                            venda_id, produto_id, quantidade,
                            preco_unitario, preco_custo_unitario,
                            subtotal
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        venda_id,
                        item['id'],
                        item['quantidade'],
                        item['preco'],
                        produto['preco_custo'],
                        item['subtotal']
                    ))
                    
                    # Atualizar estoque
                    cursor.execute("""
                        UPDATE produtos 
                        SET estoque = estoque - ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (item['quantidade'], item['id']))
                
                # Commit da transação
                self.db.conn.commit()
                
                # Guardar último ID de venda para impressão posterior
                self.ultima_venda_id = venda_id
                self.btn_imprimir_recibo.disabled = False
                self.page.update()

                # Imprimir comprovante automaticamente se configurado
                if self.imprimir_automatico:
                    self.imprimir_recibo(venda_id)
                
                # Limpar carrinho e campos
                self.itens.clear()
                self.valor_recebido_field.value = ""
                self.forma_pagamento.value = None
                self.atualizar_carrinho()
                
                # Recarregar produtos
                self.carregar_produtos()
                
                # Mostrar mensagem de sucesso
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Venda finalizada com sucesso!", color=ft.colors.WHITE),
                        bgcolor=ft.colors.GREEN_700,
                        duration=3000
                    )
                )
                
                # Mostrar diálogo de conclusão
                self.dialog_concluir.open = True
                self.page.update()
                
            except Exception as error:
                self.db.conn.rollback()
                print(f"Erro ao finalizar venda: {error}")
                self.mostrar_erro("Erro ao finalizar venda!")
                return False
            
        except Exception as error:
            print(f"Erro ao finalizar venda: {error}")
            self.mostrar_erro("Erro ao finalizar venda!")
            return False

    def editar_venda(self, e):
        """Permite editar a venda atual"""
        # Fecha o diálogo de conclusão
        self.dialog_concluir.open = False
        
        # Mostra mensagem informativa
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Você pode continuar editando a venda!", color=ft.colors.WHITE),
                bgcolor=ft.colors.BLUE_700,
                duration=3000
            )
        )
        self.page.update()

    def fechar_venda_atual(self, e):
        """Fecha o diálogo sem salvar a venda"""
        try:
            # Apenas fecha o diálogo
            if hasattr(self, 'dialog_concluir'):
                self.dialog_concluir.open = False
            self.page.update()
            
        except Exception as e:
            print(f"Erro ao fechar diálogo: {e}")

    def mudar_venda(self, e):
        """Chamado quando muda de tab"""
        try:
            if e.data == "":  # Evitar erro quando não há tabs
                return
            
            # Salvar estado da venda anterior
            if self.venda_atual_index >= 0:
                self.salvar_venda_pendente()
            
            # Atualizar índice atual
            self.venda_atual_index = int(e.data)
            
            # Carregar estado da venda selecionada
            self.carregar_venda_atual()
            
            self.update()
        except Exception as e:
            print(f"Erro ao mudar de venda: {e}")

    def salvar_venda_pendente(self):
        """Salva o estado atual da venda na memória"""
        try:
            if self.venda_atual_index >= 0:
                self.vendas_ativas[self.venda_atual_index] = {
                    'itens': self.itens.copy(),
                    'total_venda': self.total_venda,
                    'forma_pagamento': self.forma_pagamento.value,
                    'valor_recebido': self.valor_recebido_field.value,
                    'troco': self.troco_text.value if self.troco_text.visible else None
                }
        except Exception as e:
            print(f"Erro ao salvar venda pendente: {e}")

    def carregar_venda_atual(self):
        """Carrega o estado da venda selecionada"""
        try:
            if 0 <= self.venda_atual_index < len(self.vendas_ativas):
                venda = self.vendas_ativas[self.venda_atual_index]
                self.itens = venda.get('itens', []).copy()
                self.total_venda = venda.get('total_venda', 0)
                self.forma_pagamento.value = venda.get('forma_pagamento')
                self.valor_recebido_field.value = venda.get('valor_recebido', '')
                
                if venda.get('troco'):
                    self.troco_text.value = venda['troco']
                    self.troco_text.visible = True
                else:
                    self.troco_text.visible = False
                    
                self.valor_recebido_field.visible = self.forma_pagamento.value == "Dinheiro"
                self.atualizar_carrinho()
            else:
                self.limpar_venda()
        except Exception as e:
            print(f"Erro ao carregar venda atual: {e}")

    def limpar_venda(self):
        """Limpa os dados da venda atual"""
        self.itens = []
        self.total_venda = 0
        self.atualizar_lista_items()
        self.atualizar_total()
        if hasattr(self, 'busca_field'):
            self.busca_field.value = ""
            self.busca_field.focus()
        self.update()

    def atualizar_lista_items(self):
        """Atualiza a lista de itens na interface"""
        self.carrinho_table.rows.clear()
        
        for item in self.itens:
            self.carrinho_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item['codigo'], color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(item['nome'], color=ft.colors.BLACK)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.REMOVE,
                                    icon_color=ft.colors.RED,
                                    data=item,
                                    on_click=self.diminuir_quantidade
                                ),
                                ft.Text(str(item['quantidade']), color=ft.colors.BLACK),
                                ft.IconButton(
                                    icon=ft.icons.ADD,
                                    icon_color=ft.colors.GREEN,
                                    data=item,
                                    on_click=self.aumentar_quantidade
                                )
                            ], alignment=ft.MainAxisAlignment.CENTER)
                        ),
                        ft.DataCell(ft.Text(f"MT {item['preco']:.2f}", color=ft.colors.BLACK)),
                        ft.DataCell(ft.Text(f"MT {item['subtotal']:.2f}", color=ft.colors.BLACK)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    icon_color=ft.colors.BLUE,
                                    tooltip="Editar",
                                    data=item,
                                    on_click=self.editar_item,
                                    icon_size=20
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=ft.colors.RED,
                                    tooltip="Remover",
                                    data=item,
                                    on_click=self.remover_item,
                                    icon_size=20
                                )
                            ])
                        )
                    ]
                )
            )
        self.update()

    def atualizar_total(self):
        """Atualiza o valor total na interface"""
        self.total_venda = sum(item['subtotal'] for item in self.itens)
        self.total_text.value = f"Total: MT {self.total_venda:.2f}"
        self.btn_finalizar.disabled = len(self.itens) == 0
        self.update()

    def salvar_venda(self):
        """Salva a venda no banco de dados"""
        try:
            if not self.forma_pagamento.value:
                raise ValueError("Forma de pagamento não selecionada")
            
            # Verificar estoque antes de salvar
            for item in self.itens:
                # Buscar estoque atual e tipo de venda
                produto = self.db.fetchone("""
                    SELECT estoque, venda_por_peso FROM produtos WHERE id = ?
                """, (item['id'],))
                
                if not produto:
                    raise ValueError(f"Produto {item['nome']} não encontrado")
                    
                if produto['venda_por_peso'] == 1:
                    # Para produtos vendidos por peso
                    if item['quantidade'] > produto['estoque']:
                        raise ValueError(f"Estoque insuficiente para o produto {item['nome']}. Disponível: {produto['estoque']:.3f} KG")
                else:
                    # Para produtos vendidos por unidade
                    if item['quantidade'] > produto['estoque']:
                        raise ValueError(f"Estoque insuficiente para o produto {item['nome']}. Disponível: {produto['estoque']}")
            
            # Extrai o valor numérico do troco
            troco_texto = self.troco_text.value.replace("Troco: MT ", "") if self.troco_text.visible else "0"
            troco = float(troco_texto) if troco_texto and troco_texto != "Valor insuficiente" else 0
            
            # Dados da venda
            venda_data = {
                'usuario_id': self.usuario['id'],
                'total': self.total_venda,
                'forma_pagamento': self.forma_pagamento.value,
                'valor_recebido': float(self.valor_recebido_field.value) if self.valor_recebido_field.visible else None,
                'troco': troco if self.forma_pagamento.value == "Dinheiro" else None
            }
            
            # Insere a venda
            venda_id = self.db.insert_venda(venda_data)
            
            # Insere os itens e atualiza estoque
            for item in self.itens:
                # Buscar preço de custo atual do produto
                produto = self.db.fetchone("""
                    SELECT preco_custo FROM produtos WHERE id = ?
                """, (item['id'],))
                
                if not produto:
                    raise ValueError(f"Produto {item['nome']} não encontrado")
                
                # Inserir item
                item_data = {
                    'venda_id': venda_id,
                    'produto_id': item['id'],
                    'quantidade': item['quantidade'],
                    'preco_unitario': item['preco'],
                    'subtotal': item['subtotal']
                }
                self.db.insert_item_venda(item_data)
                
                # Atualizar estoque
                self.db.execute("""
                    UPDATE produtos 
                    SET estoque = estoque - ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (item['quantidade'], item['id']))
            
            # Commit da transação
            self.db.conn.commit()
            return venda_id
            
        except ValueError as e:
            print(f"Erro de validação ao salvar venda: {e}")
            self.mostrar_erro(str(e))
            self.db.conn.rollback()
            return None
        except Exception as e:
            print(f"Erro ao salvar venda: {e}")
            self.mostrar_erro("Erro ao salvar venda")
            self.db.conn.rollback()
            return None

    def iniciar_nova_venda(self, e=None):
        """Inicia uma nova venda"""
        try:
            # Salvar venda atual antes de criar nova
            if self.venda_atual_index >= 0:
                self.salvar_venda_pendente()
            
            # Limpar venda atual
            self.limpar_venda()
            
            # Criar nova tab
            nova_venda_index = len(self.vendas_tabs.tabs)
            self.vendas_tabs.tabs.append(
                ft.Tab(
                    text=f"Venda {nova_venda_index + 1}",
                    icon=ft.icons.SHOPPING_CART
                )
            )
            
            # Adicionar venda vazia à lista de vendas ativas
            self.vendas_ativas.append({
                'itens': [],
                'total_venda': 0,
                'forma_pagamento': None,
                'valor_recebido': None,
                'troco': None
            })
            
            # Selecionar nova venda
            self.venda_atual_index = nova_venda_index
            self.vendas_tabs.selected_index = nova_venda_index
            
            self.update()
        except Exception as e:
            print(f"Erro ao iniciar nova venda: {e}")

    def forma_pagamento_changed(self, e):
        """Atualiza a visibilidade do campo de valor recebido baseado na forma de pagamento"""
        try:
            if e.control.value == "Dinheiro":
                self.valor_recebido_field.visible = True
                self.valor_recebido_field.value = ""  # Limpa o campo
                self.troco_text.visible = False  # Só mostra quando tiver valor
                self.btn_finalizar.disabled = True  # Desabilita até ter valor válido
            else:
                # Para outras formas de pagamento, não precisa informar valor recebido
                self.valor_recebido_field.visible = False
                self.troco_text.visible = False
                self.btn_finalizar.disabled = len(self.itens) == 0  # Habilita se tiver itens
            
            self.update()
        except Exception as e:
            print(f"Erro ao mudar forma de pagamento: {e}")

    def calcular_troco(self, e):
        """Calcula o troco quando valor recebido é alterado"""
        try:
            if not self.valor_recebido_field.value or not self.valor_recebido_field.visible:
                self.troco_text.visible = False
                self.btn_finalizar.disabled = True
                self.update()
                return
            
            try:
                valor_recebido = float(self.valor_recebido_field.value)
                if valor_recebido >= self.total_venda:
                    troco = valor_recebido - self.total_venda
                    self.troco_text.content.value = f"Troco: MT {troco:.2f}"
                    self.troco_text.bgcolor = ft.colors.GREEN_50
                    self.troco_text.content.color = ft.colors.GREEN_800
                    self.btn_finalizar.disabled = False
                else:
                    falta = self.total_venda - valor_recebido
                    self.troco_text.content.value = f"Falta: MT {falta:.2f}"
                    self.troco_text.bgcolor = ft.colors.RED_50
                    self.troco_text.content.color = ft.colors.RED_800
                    self.btn_finalizar.disabled = True
                
                # Forçar a visibilidade do troco_text
                self.troco_text.visible = True
                
            except ValueError:
                self.troco_text.visible = False
                self.btn_finalizar.disabled = True
                
            self.update()
            
        except Exception as e:
            print(f"Erro ao calcular troco: {e}")
            self.troco_text.visible = False
            self.update()

    def aumentar_quantidade(self, e):
        """Aumenta a quantidade de um item no carrinho"""
        try:
            item = e.control.data
            # Verificar estoque disponível
            estoque_atual = self.db.fetchone("""
                SELECT estoque FROM produtos WHERE id = ?
            """, (item['id'],))['estoque']
            
            # Calcular quantidade total no carrinho
            qtd_carrinho = sum(
                i['quantidade'] for i in self.itens 
                if i['id'] == item['id']
            )
            
            if qtd_carrinho < estoque_atual:
                item['quantidade'] += 1
                item['subtotal'] = item['quantidade'] * item['preco']
                self.atualizar_carrinho()
                # Atualizar quantidade do produto
                self.atualizar_quantidade_produto(item['id'])
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Estoque insuficiente!"),
                        bgcolor=ft.colors.RED_700
                    )
                )
        except Exception as e:
            print(f"Erro ao aumentar quantidade: {e}")

    def diminuir_quantidade(self, e):
        """Diminui a quantidade de um item no carrinho"""
        try:
            item = e.control.data
            if item['quantidade'] > 1:
                item['quantidade'] -= 1
                item['subtotal'] = item['quantidade'] * item['preco']
                self.atualizar_carrinho()
                # Atualizar quantidade do produto
                self.atualizar_quantidade_produto(item['id'])
        except Exception as e:
            print(f"Erro ao diminuir quantidade: {e}")

    def imprimir_recibo(self, venda_id):
        """Imprime o recibo da venda usando RongtaPrinter.print_receipt"""
        try:
            if not venda_id:
                self.mostrar_erro("Nenhuma venda para imprimir")
                return

            # Buscar dados da venda e vendedor
            venda = self.db.fetchone(
                """
                SELECT v.*, u.nome as vendedor
                FROM vendas v
                JOIN usuarios u ON u.id = v.usuario_id
                WHERE v.id = ?
                """,
                (venda_id,)
            )

            if not venda:
                self.mostrar_erro("Venda não encontrada")
                return

            # Buscar itens
            itens = self.db.fetchall(
                """
                SELECT i.*, p.nome, p.codigo, p.venda_por_peso
                FROM itens_venda i
                JOIN produtos p ON p.id = i.produto_id
                WHERE i.venda_id = ?
                """,
                (venda_id,)
            )

            # Carregar config (fallbacks seguros)
            config = self.printer_config or {}

            # Montar payload no formato esperado pelo driver
            payload = {
                'empresa': config.get('empresa', 'Empresa'),
                'endereco': config.get('endereco', ''),
                'telefone': config.get('telefone', ''),
                'nuit': config.get('nuit', ''),
                'numero': venda['id'],
                'data': str(venda['data_venda']),
                'operador': venda['vendedor'],
                'items': [
                    {
                        'nome': item['nome'],
                        'qtd': float(item['quantidade']) if item['venda_por_peso'] else int(item['quantidade']),
                        'preco': float(item['preco_unitario']),
                        'total': float(item['subtotal'])
                    }
                    for item in itens
                ],
                'total': float(venda['total']),
                'pagamento': venda['forma_pagamento'],
                'valor_pago': float(venda['valor_recebido'] or 0),
                'troco': float(venda['troco'] or 0),
                'rodape': config.get('rodape', 'Obrigado pela preferência!')
            }

            # Se houver impressora padrão, tenta conectar antes de imprimir
            impressora_padrao = config.get('impressora_padrao')
            if impressora_padrao and not self.printer.is_connected():
                # Tenta conexão USB primeiro
                self.printer.connect_usb(impressora_padrao)

            if not self.printer.is_connected():
                self.mostrar_erro("Impressora não conectada nas Configurações")
                return

            if self.printer.print_receipt(payload):
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Recibo enviado para impressão"),
                        bgcolor=ft.colors.GREEN_700
                    )
                )
            else:
                self.mostrar_erro("Falha ao imprimir o recibo")
            
        except Exception as error:
            print(f"Erro ao imprimir recibo: {error}")
            self.mostrar_erro("Erro ao imprimir recibo!")

    def mostrar_erro(self, mensagem):
        """Método centralizado para exibir erros"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(mensagem, color=ft.colors.WHITE),
                bgcolor=ft.colors.RED_700,
                duration=5000
            )
        )

    def nova_venda(self, e=None):
        """Inicia uma nova venda após fechar o diálogo"""
        self.dialog_concluir.open = False
        self.page.update()
        self.limpar_venda()
        # Recarregar produtos novamente para garantir dados atualizados
        self.carregar_produtos()
        self.update()

    def concluir_venda(self, e):
        """Conclui a venda atual verificando o estoque"""
        try:
            # Tenta salvar a venda
            venda_id = self.salvar_venda()
            if not venda_id:
                return False

            # Se impressão automática estiver ativada
            if self.imprimir_automatico:
                self.imprimir_recibo(venda_id)

            # Fecha o diálogo
            self.dialog_concluir.open = False
            
            # Remove a venda atual
            if self.venda_atual_index >= 0:
                self.vendas_ativas.pop(self.venda_atual_index)
                self.vendas_tabs.tabs.pop(self.venda_atual_index)
            
            # Ajusta o índice para a próxima venda
            if self.vendas_ativas:
                novo_index = min(self.venda_atual_index, len(self.vendas_ativas) - 1)
                self.venda_atual_index = novo_index
                self.vendas_tabs.selected_index = novo_index
                self.carregar_venda_atual()
            else:
                self.venda_atual_index = -1
                self.limpar_venda()
            
            # Atualiza a interface
            self.carregar_produtos()
            
            # Mostra mensagem de sucesso
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Venda concluída com sucesso!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.GREEN_700,
                    duration=3000
                )
            )
            
            self.page.update()
            return True
            
        except Exception as e:
            print(f"Erro ao concluir venda: {e}")
            self.mostrar_erro("Erro ao concluir venda!")
            return False

    def editar_item(self, e):
        """Edita a quantidade/peso de um item no carrinho"""
        try:
            item = e.control.data
            
            def close_dialog(e):
                self.page.dialog.open = False
                self.page.update()

            def confirmar_edicao(e):
                try:
                    if item.get('venda_por_peso', False):
                        novo_peso = float(quantidade_field.value or 0)
                        if novo_peso <= 0:
                            self.mostrar_erro("Peso inválido!")
                            return
                            
                        # Verificar estoque
                        estoque_atual = self.db.fetchone("""
                            SELECT estoque FROM produtos WHERE id = ?
                        """, (item['id'],))['estoque']
                        
                        if novo_peso > estoque_atual:
                            self.mostrar_erro(f"Estoque insuficiente! Disponível: {estoque_atual:.3f} KG")
                            return
                            
                        item['quantidade'] = novo_peso
                        item['subtotal'] = novo_peso * item['preco']
                    else:
                        nova_qtd = int(quantidade_field.value or 0)
                        if nova_qtd <= 0:
                            self.mostrar_erro("Quantidade inválida!")
                            return
                            
                        # Verificar estoque
                        estoque_atual = self.db.fetchone("""
                            SELECT estoque FROM produtos WHERE id = ?
                        """, (item['id'],))['estoque']
                        
                        if nova_qtd > estoque_atual:
                            self.mostrar_erro(f"Estoque insuficiente! Disponível: {estoque_atual}")
                            return
                            
                        item['quantidade'] = nova_qtd
                        item['subtotal'] = nova_qtd * item['preco']
                    
                    self.atualizar_carrinho()
                    close_dialog(None)
                    
                except ValueError:
                    self.mostrar_erro("Valor inválido!")
                    return
            
            # Campo de quantidade/peso
            quantidade_field = ft.TextField(
                label="Peso (KG)" if item.get('venda_por_peso', False) else "Quantidade",
                value=str(item['quantidade']),
                width=200,
                height=50,
                text_size=14,
                color=ft.colors.BLACK,
                suffix_text="KG" if item.get('venda_por_peso', False) else None,
                autofocus=True
            )
            
            self.page.dialog = ft.AlertDialog(
                title=ft.Text(
                    "Editar Quantidade" if not item.get('venda_por_peso', False) else "Editar Peso",
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
                                    item['nome'],
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLACK
                                ),
                                ft.Text(
                                    f"Código: {item['codigo']}",
                                    color=ft.colors.BLACK
                                ),
                            ]),
                            bgcolor=ft.colors.BLUE_50,
                            padding=10,
                            border_radius=5
                        ),
                        
                        # Preço
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    "Preço" + ("/KG" if item.get('venda_por_peso', False) else ""),
                                    color=ft.colors.BLACK,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(
                                    f"MT {item['preco']:.2f}",
                                    size=20,
                                    color=ft.colors.GREEN
                                )
                            ]),
                            bgcolor=ft.colors.BLUE_50,
                            padding=10,
                            border_radius=5
                        ),
                        
                        # Campo de entrada
                        quantidade_field
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
                        on_click=confirmar_edicao,
                        style=ft.ButtonStyle(
                            color=ft.colors.GREEN
                        )
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.dialog.open = True
            self.page.update()
            
        except Exception as error:
            print(f"Erro ao editar item: {error}")
            self.mostrar_erro("Erro ao editar item!")