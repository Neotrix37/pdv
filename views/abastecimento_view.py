import flet as ft
from views.generic_header import create_header
from database.database import Database


class AbastecimentoView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.usuario = usuario or {}
        
        # Verificar permissão de abastecimento
        if not self.usuario.get('is_admin') and not self.usuario.get('pode_abastecer'):
            # Usuário não tem permissão
            self.sem_permissao = True
        else:
            self.sem_permissao = False
        
        self.header = create_header(
            page=self.page,
            title="Abastecimento",
            icon=ft.icons.LOCAL_SHIPPING,
            subtitle="Gestão de entrada de produtos"
        )
        
        # Estado em memória - recuperar da sessão se existir
        try:
            saved_items = self.page.session.get("itens_abastecimento")
            self.itens_abastecimento = saved_items if saved_items else []
            print(f"[DEBUG] Inicializando AbastecimentoView. Itens recuperados da sessão: {len(self.itens_abastecimento)}")
            
            # Se não há itens na sessão, tentar carregar da última compra
            if not self.itens_abastecimento:
                self._carregar_ultima_compra()
                
        except Exception as e:
            print(f"[DEBUG] Erro ao recuperar itens da sessão: {e}")
            self.itens_abastecimento = []
        
        # Flag para evitar cliques múltiplos
        self._adicionando_item = False

        # Controles (inicializados no método dedicado)
        self.fornecedor_dropdown = None
        self.busca_field = None
        self.produto_dropdown = None
        self.quantidade_field = None
        self.preco_custo_field = None
        self.preco_venda_field = None
        self.codigo_field = None
        self.categoria_dropdown = None
        self.descricao_field = None
        self.adicionar_button = None
        self.tabela_itens = None
        self.total_text = None
        self.lucro_text = None
        self.lucro_card = None

        # Inicializar controles
        self._inicializar_controles()
        # Carregar dados reais do banco
        self._carregar_dados()
        # Não atualizamos a tabela aqui - será feito no build()
        self._tabela_precisa_atualizar = True

    def build(self):
        # Verificar se o usuário tem permissão
        if self.sem_permissao:
            return ft.Container(
                content=ft.Column([
                    self.header,
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(
                                name=ft.icons.BLOCK,
                                size=80,
                                color=ft.colors.RED_500
                            ),
                            ft.Text(
                                "Acesso Negado",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.RED_700,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                "Você não tem permissão para acessar o módulo de Abastecimento.",
                                size=16, 
                                color=ft.colors.GREY_700,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Container(height=20),
                            ft.Text(
                                "Para obter acesso, entre em contato com o administrador do sistema.",
                                size=14,
                                color=ft.colors.GREY_600,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Container(height=30),
                            ft.ElevatedButton(
                                "Voltar ao Dashboard",
                                on_click=lambda e: self.page.go("/dashboard"),
                                bgcolor=ft.colors.BLUE,
                                color=ft.colors.WHITE
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        padding=ft.padding.all(40),
                        margin=ft.margin.all(20)
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True
            )
        
        # Layout principal (vertical, como em ProdutosView)
        if hasattr(self, '_tabela_precisa_atualizar') and self._tabela_precisa_atualizar:
            self._atualizar_tabela()
            self._tabela_precisa_atualizar = False
            
        formulario = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Text("Novo Abastecimento", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        self.lucro_card,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([self.fornecedor_dropdown, self.busca_field], spacing=10),
                    ft.Row([self.codigo_field, self.categoria_dropdown, self.produto_dropdown], spacing=10),
                    # (preview removido por solicitação)
                    ft.Row([
                        ft.Container(content=self.descricao_field, expand=1),
                        ft.Row([self.quantidade_field, self.preco_custo_field, self.preco_venda_field, self.adicionar_button, self.finalizar_button, self.historico_button], spacing=8)
                    ], spacing=10),
                ],
                spacing=8,
            ),
            padding=8,
            border_radius=8,
            bgcolor=ft.colors.BLUE_50,
            expand=False,
        )

        tabela = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("ITENS DO ABASTECIMENTO", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                    ft.Container(expand=True),
                    ft.Row([self.total_text], alignment=ft.MainAxisAlignment.END),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(
                    content=ft.Column([self.tabela_itens], scroll=ft.ScrollMode.AUTO),
                    height=300,
                    border=ft.border.all(1, ft.colors.BLUE_200),
                    border_radius=10,
                    padding=10,
                    margin=ft.margin.only(bottom=10)
                )
            ], spacing=8),
            bgcolor=ft.colors.WHITE,
            padding=10,
            border_radius=10
        )

        return ft.Container(
            content=ft.Column([
                self.header,
                ft.Container(height=5),
                formulario,
                ft.Container(height=5),
                tabela,
            ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=5),
            padding=ft.padding.only(bottom=30),
            expand=True
        )

    def _inicializar_controles(self):
        # Dropdown de fornecedor com valor padrão vazio
        self.fornecedor_dropdown = ft.Dropdown(
            label="Fornecedor",
            width=240,
            options=[],  # Será preenchido posteriormente
            hint_text="Selecione um fornecedor",
            border_color=ft.colors.BLUE_200,
            focused_border_color=ft.colors.BLUE_100,
            bgcolor=ft.colors.WHITE,
            focused_bgcolor=ft.colors.WHITE,
            content_padding=10,
        )

        # Campo de busca de produto (placeholder)
        self.busca_field = ft.TextField(
            label="Buscar produto",
            width=240,
            prefix_icon=ft.icons.SEARCH,
            on_change=self._on_busca_change,
        )

        # Dropdown de produto (placeholder)
        self.produto_dropdown = ft.Dropdown(
            label="Produto",
            width=240,
            options=[ft.dropdown.Option("0", "Selecione um produto")],
            value="0",
            on_change=self._on_produto_change,
            border_color=ft.colors.BLUE_200,
            focused_border_color=ft.colors.BLUE_100,
            bgcolor=ft.colors.WHITE,
            focused_bgcolor=ft.colors.WHITE,
            content_padding=10,
        )

        # Código, Categoria e Descrição
        self.codigo_field = ft.TextField(label="Código", width=140, on_change=self._on_codigo_change)
        self.categoria_dropdown = ft.Dropdown(
            label="Categoria",
            width=220,
            options=[
                ft.dropdown.Option("", "Selecione uma categoria"),
                ft.dropdown.Option("Alimentos", "Alimentos"),
                ft.dropdown.Option("Bebidas", "Bebidas"),
                ft.dropdown.Option("Limpeza", "Limpeza"),
                ft.dropdown.Option("Higiene", "Higiene"),
                ft.dropdown.Option("Outros", "Outros"),
            ],
            value="",
            on_change=self._on_categoria_change,
            border_color=ft.colors.BLUE_200,
            focused_border_color=ft.colors.BLUE_100,
            bgcolor=ft.colors.WHITE,
            focused_bgcolor=ft.colors.WHITE,
            content_padding=10,
        )
        self.descricao_field = ft.TextField(label="Descrição do Produto", width=400, multiline=True, min_lines=1, max_lines=2)

        # Campos numéricos
        self.quantidade_field = ft.TextField(label="Qtd", width=90, keyboard_type=ft.KeyboardType.NUMBER)
        self.preco_custo_field = ft.TextField(label="Preço Custo", width=120, keyboard_type=ft.KeyboardType.NUMBER)
        self.preco_venda_field = ft.TextField(label="Preço Venda", width=120, keyboard_type=ft.KeyboardType.NUMBER)

        # Botão adicionar
        self.adicionar_button = ft.ElevatedButton(text="Adicionar", icon=ft.icons.ADD, on_click=self._adicionar_item)
        # Botão finalizar
        self.finalizar_button = ft.ElevatedButton(
            text="Finalizar Abastecimento", 
            icon=ft.icons.CHECK_CIRCLE, 
            on_click=self._finalizar_abastecimento,
            bgcolor=ft.colors.GREEN,
            color=ft.colors.WHITE
        )
        
        # Botão para ver histórico de abastecimentos
        self.historico_button = ft.ElevatedButton(
            text="Ver Histórico", 
            icon=ft.icons.HISTORY, 
            on_click=self._ver_historico,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE
        )

        # Tabela
        self.tabela_itens = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Produto")),
                ft.DataColumn(ft.Text("Categoria")),
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Custo")),
                ft.DataColumn(ft.Text("Venda")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[],
            column_spacing=15,  # Espaçamento adequado
            heading_row_height=40,
            data_row_height=50,  # Altura maior para acomodar texto de descrição
        )

        # (preview removido)

        # Total
        self.total_text = ft.Text(self._calcular_total_formatado(), size=16, weight=ft.FontWeight.BOLD)
        # Lucro potencial (card)
        self.lucro_text = ft.Text(self._calcular_lucro_formatado()[0], size=16, weight=ft.FontWeight.BOLD)
        self.lucro_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Lucro potencial", size=12, color=ft.colors.BLACK54),
                    self.lucro_text,
                ],
                spacing=4,
            ),
            padding=10,
            border_radius=8,
        )
        # Inicializa estilo do card conforme margem
        self._atualizar_lucro_card()

    def _carregar_ultima_compra(self):
        """Carrega os itens da última compra para pré-preencher a tabela"""
        try:
            if not hasattr(self, 'db') or not self.db:
                print("[DEBUG] Banco de dados não inicializado, pulando carregamento da última compra")
                return
                
            # Buscar a última compra (mais recente)
            ultima_compra = self.db.fetchall(
                """
                SELECT c.id, c.fornecedor, ci.produto_id, ci.produto_nome, 
                       ci.quantidade, ci.preco_unitario as preco_custo, ci.preco_venda
                FROM compras c
                JOIN compra_itens ci ON c.id = ci.compra_id
                ORDER BY c.data_compra DESC
                LIMIT 1
                """,
                fetch_one=True
            )
            
            if not ultima_compra:
                print("[DEBUG] Nenhuma compra anterior encontrada")
                return
                
            print(f"[DEBUG] Última compra encontrada. ID: {ultima_compra['id']}")
            
            # Buscar itens da última compra
            itens_compra = self.db.fetchall(
                """
                SELECT ci.produto_id, ci.produto_nome, ci.quantidade, 
                       ci.preco_unitario as preco_custo, ci.preco_venda
                FROM compra_itens ci
                WHERE ci.compra_id = ?
                """,
                (ultima_compra['id'],)
            )
            
            if not itens_compra:
                print("[DEBUG] Nenhum item encontrado na última compra")
                return
            
            # Limpar itens atuais e adicionar os itens da última compra
            self.itens_abastecimento = []
            
            for item in itens_compra:
                item_formatado = {
                    "produto_id": item['produto_id'],
                    "produto_nome": item['produto_nome'],
                    "quantidade": float(item['quantidade']),
                    "preco_custo": float(item['preco_custo']),
                    "preco_venda": float(item['preco_venda']),
                    "total": float(item['quantidade']) * float(item['preco_custo']),
                }
                self.itens_abastecimento.append(item_formatado)
            
            # Salvar na sessão
            self.page.session.set("itens_abastecimento", self.itens_abastecimento)
            print(f"[DEBUG] {len(self.itens_abastecimento)} itens carregados da última compra")
            
        except Exception as e:
            print(f"[DEBUG] Erro ao carregar última compra: {e}")
            import traceback
            traceback.print_exc()
            
    def _carregar_dados(self):
        try:
            self.db = Database()
            # Garante que, mesmo após restaurar um backup antigo, o esquema necessário exista
            try:
                self.db.ensure_abastecimento_schema()
            except Exception:
                pass
            # Fornecedores
            fornecedores = self.db.fetchall(
                """
                SELECT id, nome
                FROM fornecedores
                WHERE ativo = 1
                ORDER BY nome
                """,
                dictionary=True,
            ) or []
            # Categorias
            categorias = self.db.fetchall(
                """
                SELECT id, nome
                FROM categorias
                ORDER BY nome
                """,
                dictionary=True,
            ) or []
            # Produtos
            produtos = self.db.fetchall(
                """
                SELECT p.id, p.codigo, p.nome, p.descricao, p.preco_custo, p.preco_venda, p.categoria_id,
                       COALESCE(c.nome, '') as categoria_nome
                FROM produtos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.ativo = 1
                ORDER BY p.nome
                """,
                dictionary=True,
            ) or []

            self._fornecedores = fornecedores
            self._categorias = categorias
            self._produtos = produtos
            self._categoria_por_id = {c["id"]: c["nome"] for c in categorias}

            # Popular dropdowns
            self._popular_categorias()
            self._popular_produtos(self._produtos)
            
            # Popular fornecedores e definir o primeiro como padrão, se existir
            if fornecedores:
                self.fornecedor_dropdown.options = [
                    ft.dropdown.Option(str(f['id']), f['nome']) 
                    for f in fornecedores
                ]
                # Definir o primeiro fornecedor como padrão
                if len(fornecedores) > 0:
                    self.fornecedor_dropdown.value = str(fornecedores[0]['id'])
            else:
                self.fornecedor_dropdown.options = [
                    ft.dropdown.Option("0", "Nenhum fornecedor cadastrado")
                ]
                self.fornecedor_dropdown.value = "0"
                
            self.page.update()
        except Exception as e:
            self._snack(f"Erro ao carregar dados: {e}")

    def _popular_fornecedores(self):
        self.fornecedor_dropdown.options = [ft.dropdown.Option("0", "Selecione um fornecedor")]
        for f in self._fornecedores:
            self.fornecedor_dropdown.options.append(
                ft.dropdown.Option(str(f["id"]), f["nome"])
            )
        self.fornecedor_dropdown.value = "0"

    def _popular_categorias(self):
        self.categoria_dropdown.options = [ft.dropdown.Option("", "Selecione uma categoria")]
        for c in self._categorias:
            self.categoria_dropdown.options.append(
                ft.dropdown.Option(c["nome"], c["nome"])  # usamos nome como valor
            )
        self.categoria_dropdown.value = ""

    def _popular_produtos(self, produtos):
        """Preenche o dropdown de produtos com a lista fornecida"""
        try:
            # Salvar o ID do produto atualmente selecionado
            produto_selecionado = self.produto_dropdown.value
            
            # Limpar as opções atuais e definir texto padrão
            if len(produtos) == len(self._produtos) or len(produtos) == 0:
                default_text = "Selecione um produto"
            else:
                default_text = f"{len(produtos)} produto(s) encontrado(s)"
            self.produto_dropdown.options = [ft.dropdown.Option(
                key="0", 
                text=default_text,
                disabled=True  # Impede que o texto de status seja selecionado
            )]
            
            # Adicionar cada produto à lista
            for p in produtos:
                # Formatar o rótulo com nome e código (se disponível)
                codigo = p.get("codigo", "")
                label = f"{p['nome']} ({codigo})" if codigo else p["nome"]
                
                self.produto_dropdown.options.append(
                    ft.dropdown.Option(
                        key=str(p["id"]), 
                        text=label,
                    )
                )
            
            # Restaurar a seleção anterior se ainda estiver disponível
            if produto_selecionado and produto_selecionado != "0":
                if any(opt.key == produto_selecionado for opt in self.produto_dropdown.options):
                    self.produto_dropdown.value = produto_selecionado
                else:
                    self.produto_dropdown.value = "0"
            else:
                self.produto_dropdown.value = "0"
                
        except Exception as e:
            print(f"[ERRO] Erro ao popular produtos: {e}")
            self.produto_dropdown.options = [ft.dropdown.Option(
                key="0", 
                text="Erro ao carregar produtos",
                disabled=True
            )]
            self.produto_dropdown.value = "0"

    # ===== Handlers =====
    def _on_busca_change(self, e):
        """Filtra a lista de produtos em tempo real conforme o usuário digita"""
        try:
            termo = (self.busca_field.value or "").strip().lower()
            
            # Se o campo estiver vazio, mostrar todos os produtos
            if not termo:
                self._popular_produtos(self._produtos)
                self.page.update()
                return
                
            # Filtrar produtos que correspondam ao termo de busca (nome ou código)
            filtrados = []
            for p in self._produtos:
                nome = (p.get("nome") or "").lower()
                codigo = (p.get("codigo") or "").lower()
                
                # Verifica se o termo está no nome ou no código
                if termo in nome or termo in codigo:
                    filtrados.append(p)
            
            # Atualiza a lista de produtos no dropdown
            self._popular_produtos(filtrados)
            
            # Não seleciona automaticamente, mas mantém o foco no campo de busca
            self.produto_dropdown.value = "0"
            self.page.update()
            
        except Exception as e:
            print(f"[ERRO] Erro ao filtrar produtos: {e}")
            import traceback
            traceback.print_exc()
            
    def _on_produto_change(self, e):
        if not self.produto_dropdown.value or self.produto_dropdown.value == "0":
            print("[DEBUG] Produto não selecionado ou valor inválido")
            return
        try:
            pid = int(self.produto_dropdown.value)
        except Exception as ex:
            print(f"[DEBUG] Erro ao converter produto ID: {ex}")
            return
        prod = next((p for p in self._produtos if p["id"] == pid), None)
        if not prod:
            print(f"[DEBUG] Produto com ID {pid} não encontrado")
            return
        
        print(f"[DEBUG] Preenchendo campos do produto: {prod.get('nome', 'N/A')}")
        
        # Preencher campos a partir do produto
        self.codigo_field.value = prod.get("codigo") or ""
        categoria_nome = prod.get("categoria_nome") or self._categoria_por_id.get(prod.get("categoria_id"), "")
        self.categoria_dropdown.value = categoria_nome or ""
        # Descrição (se existir no modelo)
        self.descricao_field.value = prod.get("descricao") or ""
        # Preços: sugerimos os atuais como default
        preco_venda = prod.get("preco_venda")
        preco_custo = prod.get("preco_custo")
        
        self.preco_venda_field.value = f"{float(preco_venda):.2f}" if preco_venda is not None and preco_venda > 0 else ""
        self.preco_custo_field.value = f"{float(preco_custo):.2f}" if preco_custo is not None and preco_custo > 0 else ""
        
        print(f"[DEBUG] Campos preenchidos:")
        print(f"  Código: '{self.codigo_field.value}'")
        print(f"  Categoria: '{self.categoria_dropdown.value}'")
        print(f"  Descrição: '{self.descricao_field.value}'")
        print(f"  Preço Venda: '{self.preco_venda_field.value}'")
        print(f"  Preço Custo: '{self.preco_custo_field.value}'")
        
        # Forçar atualização visual dos campos
        self.codigo_field.update()
        self.categoria_dropdown.update()
        self.descricao_field.update()
        self.preco_venda_field.update()
        self.preco_custo_field.update()
        
        print("[DEBUG] Forçando atualização visual dos campos...")
        self.page.update()

    def _on_codigo_change(self, e):
        codigo = (self.codigo_field.value or "").strip().lower()
        print(f"[Abastecimento] Digitou código: '{codigo}'")
        candidatos = [p for p in self._produtos if codigo in (p.get("codigo") or "").lower()]
        print(f"[Abastecimento] Candidatos ({len(candidatos)}): "
              f"{[ (p.get('codigo') or '') for p in candidatos[:10] ]}{' ...' if len(candidatos)>10 else ''}")
        self._aplicar_filtros(codigo=codigo)
        match = next((p for p in self._produtos if (p.get("codigo") or "").lower() == codigo), None)
        if match:
            print(f"[Abastecimento] Match exato: id={match['id']} codigo={match.get('codigo')} nome={match.get('nome')}")
            self.produto_dropdown.value = str(match["id"])
            self._on_produto_change(None)
            self.page.update()
            
    def _on_categoria_change(self, e):
        categoria = self.categoria_dropdown.value or ""
        self._aplicar_filtros(categoria=categoria)
        # Preenche preview
        # preview removido
        self.page.update()
    
    def _aplicar_filtros(self, termo: str = None, categoria: str = None, codigo: str = None):
        termo = (self.busca_field.value if termo is None else termo) or ""
        termo = termo.strip().lower()
        categoria = (self.categoria_dropdown.value if categoria is None else categoria) or ""
        codigo = (self.codigo_field.value if codigo is None else codigo) or ""
        codigo = codigo.strip().lower()

        base = list(self._produtos)
        if categoria:
            base = [p for p in base if (p.get("categoria_nome") or "") == categoria]
        if codigo:
            base = [p for p in base if codigo in (p.get("codigo") or "").lower()]
        if termo:
            base = [p for p in base if (termo in (p.get("nome") or "").lower() or termo in (p.get("codigo") or "").lower())]

        self._popular_produtos(base)
        if len(base) == 1:
            self.produto_dropdown.value = str(base[0]["id"])
            self._on_produto_change(None)
        # preview removido

    def _adicionar_item(self, e):
        # Evitar cliques múltiplos
        if self._adicionando_item:
            print("[DEBUG] Clique múltiplo detectado - ignorando")
            return
        
        self._adicionando_item = True
        print("[DEBUG] Iniciando adição/atualização de item...")
        
        # Verifica se está em modo de edição
        editando = hasattr(self, '_item_em_edicao') and self._item_em_edicao is not None
        
        try:
            # Validações simples
            if not self.fornecedor_dropdown.value or self.fornecedor_dropdown.value == "0":
                # Se não houver fornecedor selecionado, tenta usar o primeiro disponível
                if hasattr(self, '_fornecedores') and self._fornecedores:
                    self.fornecedor_dropdown.value = str(self._fornecedores[0]['id'])
                    self.fornecedor_dropdown.update()
                else:
                    self._snack("Nenhum fornecedor disponível. Cadastre um fornecedor primeiro.")
                    return
            if self.produto_dropdown.value == "0":
                self._snack("Selecione um produto")
                return
            
            # Validação mais detalhada dos campos numéricos
            quantidade_str = str(self.quantidade_field.value or "").strip().replace(",", ".")
            custo_str = str(self.preco_custo_field.value or "").strip().replace(",", ".")
            venda_str = str(self.preco_venda_field.value or "").strip().replace(",", ".")
        

        
            # Verificar se os campos estão preenchidos
            if not quantidade_str:
                self._snack(f"Preencha a quantidade (valor atual: '{self.quantidade_field.value}')")
                return
            if not custo_str:
                self._snack(f"Preencha o preço de custo (valor atual: '{self.preco_custo_field.value}')")
                return
            if not venda_str:
                self._snack(f"Preencha o preço de venda (valor atual: '{self.preco_venda_field.value}')")
                return
            
            # Tentar converter para números
            try:
                quantidade = float(quantidade_str)
            except ValueError:
                self._snack(f"Quantidade inválida: '{quantidade_str}'. Use apenas números")
                return
                
            try:
                custo = float(custo_str)
            except ValueError:
                self._snack(f"Preço de custo inválido: '{custo_str}'. Use apenas números")
                return
                
            try:
                venda = float(venda_str)
            except ValueError:
                self._snack(f"Preço de venda inválido: '{venda_str}'. Use apenas números")
                return
            
            # Verificar se os valores são positivos
            if quantidade <= 0:
                self._snack("A quantidade deve ser maior que zero")
                return
            if custo <= 0:
                self._snack("O preço de custo deve ser maior que zero")
                return
            if venda <= 0:
                self._snack("O preço de venda deve ser maior que zero")
                return

            produto_nome = next((o.text for o in self.produto_dropdown.options if o.key == self.produto_dropdown.value), "Produto")
            total = quantidade * custo
            
            # Criar o novo item
            novo_item = {
                "produto_id": self.produto_dropdown.value,
                "produto_nome": produto_nome,
                "codigo": (self.codigo_field.value or "").strip(),
                "categoria": self.categoria_dropdown.value or "",
                "descricao": (self.descricao_field.value or "").strip(),
                "quantidade": quantidade,
                "preco_custo": custo,
                "preco_venda": venda,
                "total": total,
            }
            
            # Se estiver editando, atualiza o item existente
            if editando:
                self.itens_abastecimento[self._item_em_edicao] = novo_item
                mensagem = "Item atualizado com sucesso!"
                # Limpa o modo de edição
                delattr(self, '_item_em_edicao')
                # Volta o texto do botão para o padrão
                self.adicionar_button.text = "Adicionar Item"
                self.adicionar_button.update()
            else:
                # Se não estiver editando, adiciona um novo item
                self.itens_abastecimento.append(novo_item)
                mensagem = "Item adicionado com sucesso!"
            
            # Salvar na sessão para manter entre navegações
            self.page.session.set("itens_abastecimento", self.itens_abastecimento)
            
            print(f"[DEBUG] Item adicionado! Total de itens: {len(self.itens_abastecimento)}")
            
            # Calcular lucro antes de atualizar a interface
            lucro_texto, _ = self._calcular_lucro_formatado()
            
            # Atualizar a tabela e o card de lucro
            self._atualizar_tabela()
            
            # Atualizar o texto de lucro diretamente para garantir que seja atualizado
            if hasattr(self, 'lucro_text') and self.lucro_text is not None:
                self.lucro_text.value = lucro_texto
            
            # Forçar atualização do card de lucro
            self._atualizar_lucro_card()
            
            # Limpar campos apenas após sucesso
            self.quantidade_field.value = ""
            self.preco_custo_field.value = ""
            self.preco_venda_field.value = ""
            self.codigo_field.value = ""
            self.categoria_dropdown.value = ""
            self.descricao_field.value = ""
            self.produto_dropdown.value = "0"
            
            # Forçar atualização dos campos
            self.quantidade_field.update()
            self.preco_custo_field.update()
            self.preco_venda_field.update()
            self.codigo_field.update()
            self.categoria_dropdown.update()
            self.descricao_field.update()
            self.produto_dropdown.update()
            
            print(f"[DEBUG] Campos limpos, atualizando página...")
            
            # Atualizar a interface
            if hasattr(self, 'page') and self.page is not None:
                # Atualizar apenas os controles necessários para melhor performance
                controls_to_update = [
                    self.tabela_itens,
                    self.lucro_text,
                    self.lucro_card,
                    self.quantidade_field,
                    self.preco_custo_field,
                    self.preco_venda_field
                ]
                
                # Filtrar controles válidos
                valid_controls = [c for c in controls_to_update if c is not None]
                
                # Atualizar página com os controles necessários
                for control in valid_controls:
                    if hasattr(control, 'update'):
                        control.update()
                
                # Garantir que a página seja atualizada
                self.page.update()
            
            # Mostrar mensagem de sucesso (verde)
            self._snack("Item adicionado com sucesso!", success=True)
            
            # Não focar automaticamente no campo de quantidade
            # O foco permanecerá no campo de busca
            
            # Atualizar a UI
            self.page.update()
            
        finally:
            # Sempre resetar a flag, mesmo em caso de erro
            self._adicionando_item = False
            print("[DEBUG] Flag de adição resetada")
            
    def _atualizar_tabela(self):
        if not hasattr(self, 'tabela_itens') or self.tabela_itens is None:
            print("[DEBUG] Tabela ainda não inicializada, pulando atualização")
            return
            
        print(f"[DEBUG] Atualizando tabela. Itens na lista: {len(self.itens_abastecimento)}")
        
        try:
            # Limpar linhas existentes
            self.tabela_itens.rows.clear()
            
            for idx, item in enumerate(self.itens_abastecimento):
                # Garantir que a descrição seja exibida, mesmo que vazia
                descricao = item.get("descricao", "") or "(sem descrição)"
                
                row = ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item.get("codigo", ""))),
                    ft.DataCell(ft.Text(item["produto_nome"])),
                    ft.DataCell(ft.Text(item.get("categoria", ""))),
                    ft.DataCell(ft.Text(descricao, 
                                     text_align=ft.TextAlign.LEFT,
                                     overflow=ft.TextOverflow.ELLIPSIS)),
                    ft.DataCell(ft.Text(f"{item['quantidade']:.2f}")),
                    ft.DataCell(ft.Text(f"{item['preco_custo']:.2f}")),
                    ft.DataCell(ft.Text(f"{item['preco_venda']:.2f}")),
                    ft.DataCell(ft.Text(f"{item['total']:.2f}")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar", data=idx, icon_color=ft.colors.BLUE, on_click=self._editar_item),
                            ft.IconButton(icon=ft.icons.DELETE, tooltip="Remover", data=idx, icon_color=ft.colors.RED, on_click=self._remover_item),
                        ], spacing=4)
                    ),
                ])
                
                self.tabela_itens.rows.append(row)
                
            if hasattr(self, 'total_text') and self.total_text is not None:
                self.total_text.value = self._calcular_total_formatado()
                
            self._atualizar_lucro_card()
            
            # Forçar atualização visual da tabela, se já estiver na página
            if hasattr(self.tabela_itens, 'update') and hasattr(self.tabela_itens, '_Control__page') and self.tabela_itens._Control__page is not None:
                self.tabela_itens.update()
                
        except Exception as e:
            print(f"[ERRO] Falha ao atualizar tabela: {e}")
            import traceback
            traceback.print_exc()

    def _calcular_total_formatado(self) -> str:
        total = sum(i["total"] for i in self.itens_abastecimento) if self.itens_abastecimento else 0.0
        return f"Total: {total:.2f} MT"

    def _calcular_lucro_formatado(self):
        if not self.itens_abastecimento:
            return ("MT 0.00 (0.0%)", 0.0)
        lucro_total = 0.0
        receita_total = 0.0
        for i in self.itens_abastecimento:
            lucro_total += (i["preco_venda"] - i["preco_custo"]) * i["quantidade"]
            receita_total += i["preco_venda"] * i["quantidade"]
        margem = (lucro_total / receita_total * 100.0) if receita_total > 0 else 0.0
        return (f"MT {lucro_total:.2f} ({margem:.1f}%)", margem)

    def _atualizar_lucro_card(self):
        texto, margem = self._calcular_lucro_formatado()
        self.lucro_text.value = texto
        # Definir cores por faixa de margem
        if margem < 10.0:
            self.lucro_text.color = ft.colors.RED_700
            self.lucro_card.bgcolor = ft.colors.RED_50
            self.lucro_card.border = ft.border.all(1, ft.colors.RED_200)
        elif margem < 20.0:
            self.lucro_text.color = ft.colors.AMBER_800
            self.lucro_card.bgcolor = ft.colors.AMBER_50
            self.lucro_card.border = ft.border.all(1, ft.colors.AMBER_200)
        else:
            self.lucro_text.color = ft.colors.GREEN_700
            self.lucro_card.bgcolor = ft.colors.GREEN_50
            self.lucro_card.border = ft.border.all(1, ft.colors.GREEN_200)

    def _snack(self, msg: str, success: bool = False):
        if success:
            # Snackbar verde para sucesso
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(msg, color=ft.colors.WHITE),
                bgcolor=ft.colors.GREEN_600,
                action="OK",
                action_color=ft.colors.WHITE
            )
        else:
            # Snackbar vermelho para erro
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(msg, color=ft.colors.WHITE),
                bgcolor=ft.colors.RED_600,
                action="OK", 
                action_color=ft.colors.WHITE
            )
        self.page.snack_bar.open = True
        self.page.update()
    
    # preview removido

    def _finalizar_abastecimento(self, e):
        try:
            print(f"[DEBUG] Finalizando abastecimento. Itens na lista: {len(self.itens_abastecimento)}")
            print(f"[DEBUG] Itens: {self.itens_abastecimento}")
            
            if not self.itens_abastecimento:
                self._snack("Adicione ao menos um item")
                return
            if self.fornecedor_dropdown.value == "0":
                self._snack("Selecione um fornecedor")
                return
            
            fornecedor_id = self.fornecedor_dropdown.value
            fornecedor_nome = next((f["nome"] for f in getattr(self, "_fornecedores", []) if str(f["id"]) == str(fornecedor_id)), None)
            if not fornecedor_nome:
                fornecedor_nome = "Fornecedor"
            
            # Ajustar estrutura dos itens para o banco
            itens_para_banco = []
            for item in self.itens_abastecimento:
                lucro_unitario = item['preco_venda'] - item['preco_custo']
                lucro_total = lucro_unitario * item['quantidade']
                
                item_banco = {
                    'produto_id': item['produto_id'],
                    'produto_nome': item['produto_nome'],
                    'quantidade': item['quantidade'],
                    'preco_unitario': item['preco_custo'],  # O banco espera 'preco_unitario'
                    'preco_venda': item['preco_venda'],
                    'lucro_unitario': lucro_unitario,
                    'lucro_total': lucro_total
                }
                itens_para_banco.append(item_banco)
            
            compra_id = self.db.adicionar_compra(
                fornecedor=fornecedor_nome,
                itens=itens_para_banco,
                usuario_id=self.usuario.get("id"),
                observacoes=None,
            )
            if not compra_id:
                self._snack("Erro ao salvar abastecimento")
                return
            
            for item in self.itens_abastecimento:
                try:
                    produto_id = int(item["produto_id"]) if isinstance(item["produto_id"], str) else item["produto_id"]
                except Exception:
                    produto_id = item["produto_id"]
                self.db.execute(
                    """
                    UPDATE produtos 
                    SET estoque = COALESCE(estoque, 0) + ?,
                        preco_custo = ?,
                        preco_venda = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        float(item["quantidade"]),
                        float(item["preco_custo"]),
                        float(item["preco_venda"]),
                        produto_id,
                    ),
                )

            self._snack("Abastecimento finalizado com sucesso!", success=True)
            self.itens_abastecimento.clear()
            # Limpar da sessão após finalizar
            self.page.session.remove("itens_abastecimento")
            self._atualizar_tabela()
            self.quantidade_field.value = ""
            self.preco_custo_field.value = ""
            self.preco_venda_field.value = ""
            self.page.update()
            
        except Exception as err:
            self._snack(f"Erro ao finalizar: {err}")

    def _ver_historico(self, e):
        """Mostra uma janela com o histórico de abastecimentos"""
        try:
            # Armazenar todas as compras para filtro
            self.todas_compras = []
            
            # Campo de busca por produto e usuário
            self.busca_historico_field = ft.TextField(
                label="Buscar produto ou usuário...",
                width=300,
                height=40,
                prefix_icon=ft.icons.SEARCH,
                on_change=self._filtrar_historico,
                color=ft.colors.BLACK,
                label_style=ft.TextStyle(color=ft.colors.BLACK)
            )
            
            # Criar tabela de histórico
            self.tabela_historico = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Data")),
                    ft.DataColumn(ft.Text("Hora")),
                    ft.DataColumn(ft.Text("Usuário")),
                    ft.DataColumn(ft.Text("Produto")),
                    ft.DataColumn(ft.Text("Qtd")),
                    ft.DataColumn(ft.Text("Custo")),
                    ft.DataColumn(ft.Text("Venda")),
                ],
                rows=[],
                column_spacing=10,
                heading_row_height=40,
                data_row_height=35,
            )
            
            # Carregar dados iniciais
            self._carregar_historico()
            
            # Criar diálogo
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Histórico de Abastecimentos"),
                content=ft.Container(
                    content=ft.Column([
                        self.busca_historico_field,
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Column([self.tabela_historico], scroll=ft.ScrollMode.AUTO),
                            height=400,
                            width=800,
                        )
                    ], spacing=10),
                    padding=10
                ),
                actions=[
                    ft.TextButton("Fechar", on_click=lambda e: self._fechar_dialog())
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as err:
            print(f"Erro ao mostrar histórico: {err}")
            self._snack(f"Erro ao carregar histórico: {err}")

    def _carregar_historico(self, filtro=""):
        """Carrega os dados do histórico de abastecimentos"""
        try:
            # Buscar compras recentes do banco com informações do usuário
            # Primeiro, configuramos o fuso horário para Maputo (UTC+2)
            self.db.execute("PRAGMA timezone = 'Africa/Maputo'")
            
            # Query base
            query = """
                SELECT 
                    c.id, 
                    c.valor_total, 
                    strftime('%d/%m/%Y', c.data_compra, 'localtime') as data_compra,
                    strftime('%H:%M', c.data_compra, 'localtime') as hora_compra,
                    ci.produto_nome, 
                    ci.quantidade, 
                    ci.preco_unitario, 
                    ci.preco_venda,
                    SUBSTR(u.nome, 1, INSTR(u.nome || ' ', ' ')) as usuario
                FROM compras c
                JOIN compra_itens ci ON c.id = ci.compra_id
                LEFT JOIN usuarios u ON c.usuario_id = u.id
            """
            
            # Adicionar filtro se fornecido
            if filtro:
                query += " WHERE (LOWER(ci.produto_nome) LIKE ? OR LOWER(u.nome) LIKE ?)"
                params = [f"%{filtro.lower()}%", f"%{filtro.lower()}%"]
            else:
                params = []
                
            query += " ORDER BY c.data_compra DESC LIMIT 50"
            
            compras = self.db.fetchall(query, params, dictionary=True) or []
            
            # Armazenar todas as compras para filtro
            if not filtro:  # Só armazena na primeira carga
                self.todas_compras = compras
            
            # Limpar tabela
            self.tabela_historico.rows.clear()
            
            if not compras:
                if filtro:
                    self.tabela_historico.rows.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text("Nenhum resultado encontrado")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                        ])
                    )
                else:
                    self._snack("Nenhum abastecimento encontrado")
                    return
            
            # Preencher tabela
            for compra in compras:
                row = ft.DataRow(cells=[
                    ft.DataCell(ft.Text(compra.get('data_compra', ''))),
                    ft.DataCell(ft.Text(compra.get('hora_compra', ''))),
                    ft.DataCell(ft.Text(compra.get('usuario', 'Sis'))),
                    ft.DataCell(ft.Text(compra.get('produto_nome', ''))),
                    ft.DataCell(ft.Text(str(compra.get('quantidade', '')))),
                    ft.DataCell(ft.Text(f"{float(compra.get('preco_unitario', 0)):,.2f}".replace('.', 'v').replace(',', '.').replace('v', ','))),
                    ft.DataCell(ft.Text(f"{float(compra.get('preco_venda', 0)):,.2f}".replace('.', 'v').replace(',', '.').replace('v', ','))),
                ])
                self.tabela_historico.rows.append(row)
            
            self.page.update()
            
        except Exception as err:
            print(f"Erro ao carregar histórico: {err}")
            self._snack(f"Erro ao carregar dados: {err}")

    def _filtrar_historico(self, e):
        """Filtra o histórico por nome do produto"""
        try:
            termo = e.control.value.strip()
            self._carregar_historico(termo)
        except Exception as err:
            print(f"Erro ao filtrar histórico: {err}")
    
    def _fechar_dialog(self):
        """Fecha o diálogo atual"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def _confirmar_remocao(self, e, idx):
        """Confirma a remoção de um item"""
        try:
            if not self.dialog_confirmar_remocao.open:
                return
                
            if e.control.text.lower() == 'sim':
                if 0 <= idx < len(self.itens_abastecimento):
                    print(f"[DEBUG] Confirmada remoção do item no índice {idx}")
                    # Remove o item da lista
                    item_removido = self.itens_abastecimento.pop(idx)
                    # Salvar na sessão após remoção
                    self.page.session.set("itens_abastecimento", self.itens_abastecimento)
                    
                    # Atualiza a tabela e o total
                    self._atualizar_tabela()
                    
                    # Calcular e atualizar o lucro em tempo real
                    texto_lucro, margem = self._calcular_lucro_formatado()
                    self.lucro_text.value = texto_lucro
                    
                    # Atualizar cores do card de lucro
                    if margem < 10.0:
                        self.lucro_text.color = ft.colors.RED_700
                        self.lucro_card.bgcolor = ft.colors.RED_50
                        self.lucro_card.border = ft.border.all(1, ft.colors.RED_200)
                    elif margem < 20.0:
                        self.lucro_text.color = ft.colors.AMBER_800
                        self.lucro_card.bgcolor = ft.colors.AMBER_50
                        self.lucro_card.border = ft.border.all(1, ft.colors.AMBER_200)
                    else:
                        self.lucro_text.color = ft.colors.GREEN_700
                        self.lucro_card.bgcolor = ft.colors.GREEN_50
                        self.lucro_card.border = ft.border.all(1, ft.colors.GREEN_200)
                    
                    # Forçar atualização imediata da UI
                    self.lucro_text.update()
                    self.lucro_card.update()
                    
                    # Mostrar mensagem de sucesso
                    self._snack("Item removido com sucesso!", success=True)
                    
                    print(f"[DEBUG] Item removido. Total de itens: {len(self.itens_abastecimento)}")
            
            # Fechar o diálogo e atualizar a página
            self.dialog_confirmar_remocao.open = False
            self.page.update()
            
        except Exception as err:
            print(f"[ERRO] Falha ao confirmar remoção: {err}")
            import traceback
            traceback.print_exc()
            self._snack(f"Erro ao remover: {err}")
            # Garantir que a UI seja atualizada mesmo em caso de erro
            self.page.update()
    
    def _remover_item(self, e):
        """Inicia o processo de remoção de um item com confirmação"""
        try:
            idx = e.control.data
            if idx is None or not (0 <= idx < len(self.itens_abastecimento)):
                return
                
            # Obter o nome do produto para exibição
            produto_nome = self.itens_abastecimento[idx].get('descricao', 'o item')
            
            # Criar diálogo de confirmação se não existir
            if not hasattr(self, 'dialog_confirmar_remocao'):
                self.dialog_confirmar_remocao = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Confirmar Remoção"),
                    content=ft.Text(f"Tem certeza que deseja remover {produto_nome}?", size=16),
                    actions=[
                        ft.TextButton("Sim", on_click=lambda e, i=idx: self._confirmar_remocao(e, i)),
                        ft.TextButton("Não", on_click=self._fechar_dialog_remocao),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            else:
                # Atualizar a mensagem do diálogo existente
                self.dialog_confirmar_remocao.content = ft.Text(
                    f"Tem certeza que deseja remover {produto_nome}?", 
                    size=16
                )
                # Atualizar a função de callback com o novo índice
                self.dialog_confirmar_remocao.actions[0].on_click = lambda e, i=idx: self._confirmar_remocao(e, i)
            
            # Mostrar o diálogo
            self.dialog_confirmar_remocao.open = True
            self.page.dialog = self.dialog_confirmar_remocao
            self.page.update()
            
        except Exception as err:
            print(f"[ERRO] Falha ao iniciar remoção: {err}")
            import traceback
            traceback.print_exc()
            self._snack(f"Erro ao tentar remover: {err}")
    
    def _fechar_dialog_remocao(self, e):
        """Fecha o diálogo de confirmação de remoção"""
        if hasattr(self, 'dialog_confirmar_remocao'):
            self.dialog_confirmar_remocao.open = False
            self.page.update()

    def _editar_item(self, e):
        try:
            idx = e.control.data
            if idx is None:
                return
            if 0 <= idx < len(self.itens_abastecimento):
                item = self.itens_abastecimento[idx]  # Não remove o item da lista ainda
                
                # Preencher formulário com o item
                self.codigo_field.value = item.get("codigo", "")
                self.categoria_dropdown.value = item.get("categoria", "")
                self.descricao_field.value = item.get("descricao", "")
                self.quantidade_field.value = str(item.get("quantidade", ""))
                self.preco_custo_field.value = f"{float(item.get('preco_custo', 0)):.2f}"
                self.preco_venda_field.value = f"{float(item.get('preco_venda', 0)):.2f}"
                
                # Selecionar o produto no dropdown, se possível
                pid = str(item.get("produto_id"))
                if any(opt.key == pid for opt in self.produto_dropdown.options):
                    self.produto_dropdown.value = pid
                
                # Atualizar interface
                self.produto_dropdown.update()
                self.codigo_field.update()
                self.categoria_dropdown.update()
                self.descricao_field.update()
                self.quantidade_field.update()
                self.preco_custo_field.update()
                self.preco_venda_field.update()
                
                # Remover o item da lista apenas quando o usuário clicar em adicionar
                # Isso será feito no _adicionar_item
                self._item_em_edicao = idx
                
                # Muda o texto do botão para indicar modo de edição
                self.adicionar_button.text = "Atualizar Item"
                self.adicionar_button.update()
                
        except Exception as err:
            self._snack(f"Erro ao editar: {err}")
            
                
        except Exception as err:
            self._snack(f"Erro ao editar: {err}")


