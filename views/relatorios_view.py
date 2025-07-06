import flet as ft
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import sys

# Ajustando o path para importar o Database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.database import Database

class RelatoriosView(ft.UserControl):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.WHITE
        self.usuario = usuario
        self.db = Database()
        
        # Diretório para salvar os relatórios
        self.relatorios_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "relatorios")
        if not os.path.exists(self.relatorios_dir):
            os.makedirs(self.relatorios_dir)
        
        # Campos de data
        self.data_inicial = ft.TextField(
            label="Data Inicial",
            width=200,
            height=50,
            value=datetime.now().strftime("%Y-%m-%d"),
            text_style=ft.TextStyle(color=ft.colors.WHITE),  # Texto em branco
            label_style=ft.TextStyle(color=ft.colors.WHITE),  # Label em branco
            bgcolor=ft.colors.BLACK,  # Fundo preto
            border_color=ft.colors.WHITE  # Borda branca
        )
        self.data_final = ft.TextField(
            label="Data Final",
            width=200,
            height=50,
            value=datetime.now().strftime("%Y-%m-%d"),
            text_style=ft.TextStyle(color=ft.colors.WHITE),  # Texto em branco
            label_style=ft.TextStyle(color=ft.colors.WHITE),  # Label em branco
            bgcolor=ft.colors.BLACK,  # Fundo preto
            border_color=ft.colors.WHITE  # Borda branca
        )

        # Dropdown de funcionários
        self.funcionario_dropdown = ft.Dropdown(
            label="Selecione o Funcionário",
            width=300,
            height=50,
            options=[
                ft.dropdown.Option("todos", "Todos os Funcionários")
            ],
            bgcolor=ft.colors.BLACK,    # Fundo preto
            label_style=ft.TextStyle(
                color=ft.colors.WHITE,  # Label em branco
                weight=ft.FontWeight.BOLD
            ),
            text_style=ft.TextStyle(    # Texto das opções em branco
                color=ft.colors.WHITE,
                size=14
            ),
            focused_bgcolor=ft.colors.BLUE_50,  # Cor suave quando selecionado
            focused_border_color=ft.colors.BLUE,   # Borda azul quando focado
            border_color=ft.colors.GREY_400,      # Borda cinza
            content_padding=10,
            border_width=2
        )
        self.carregar_funcionarios()

    def carregar_funcionarios(self):
        try:
            funcionarios = self.db.fetchall("""
                SELECT id, nome 
                FROM usuarios 
                WHERE ativo = 1 
                ORDER BY nome
            """)
            
            # Adiciona cada funcionário ao dropdown
            for f in funcionarios:
                self.funcionario_dropdown.options.append(
                    ft.dropdown.Option(str(f['id']), f['nome'])
                )
            
            # Seleciona "todos" por padrão
            self.funcionario_dropdown.value = "todos"
            self.update()
            
        except Exception as error:
            print(f"Erro ao carregar funcionários: {error}")

    def _add_page_number(self, canvas, doc):
        """Adiciona número de página ao rodapé de forma elegante"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#7F8C8D'))
        
        # Desenha linha superior
        canvas.line(
            doc.leftMargin,
            doc.bottomMargin - 20,
            doc.pagesize[0] - doc.rightMargin,
            doc.bottomMargin - 20
        )
        
        # Adiciona número da página
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.bottomMargin - 30,
            text
        )
        
        canvas.restoreState()

    def formatar_itens(self, itens_str):
        """Formata os itens para melhor apresentação na tabela"""
        try:
            itens_lista = []
            max_chars_por_linha = 35  # Reduzido para garantir que caiba
            
            for item in itens_str.split(','):
                item = item.strip()
                if '(' in item and ')' in item:
                    nome, info = item.split('(', 1)
                    nome = nome.strip()
                    info = info.rstrip(')')
                    
                    # Quebrar nome em partes menores
                    if len(nome) > max_chars_por_linha:
                        nome_partes = []
                        for i in range(0, len(nome), max_chars_por_linha):
                            parte = nome[i:i + max_chars_por_linha]
                            if i + max_chars_por_linha < len(nome):
                                # Procura o último espaço para quebrar a palavra
                                ultimo_espaco = parte.rfind(' ')
                                if ultimo_espaco > 0:
                                    parte = parte[:ultimo_espaco]
                                    i = i - (len(parte) - ultimo_espaco)
                            nome_partes.append(parte.strip())
                        nome_formatado = '\n'.join(nome_partes)
                    else:
                        nome_formatado = nome

                    # Formatar informações de preço em linhas separadas
                    info_parts = []
                    for part in info.split('MT'):
                        if part.strip():
                            info_formatado = f"MT{part.strip()}"
                            # Quebrar informação de preço se for muito longa
                            if len(info_formatado) > max_chars_por_linha:
                                for i in range(0, len(info_formatado), max_chars_por_linha):
                                    info_parts.append(info_formatado[i:i + max_chars_por_linha].strip())
                            else:
                                info_parts.append(info_formatado)

                    # Combinar nome e informações
                    item_formatado = nome_formatado + '\n' + '\n'.join(info_parts)
                    itens_lista.append(item_formatado)
                else:
                    itens_lista.append(item)
            
            return '\n'.join(itens_lista)
        except Exception as e:
            print(f"Erro ao formatar itens: {e}")
            return itens_str

    def _create_story(self, vendas_por_vendedor, config, total_geral, lucro_geral, total_vendas):
        """Cria o conteúdo do relatório com layout profissional"""
        styles = getSampleStyleSheet()
        elements = []
        
        # Estilos personalizados
        styles.add(ParagraphStyle(
            name='CompanyName',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=5,
            alignment=1,
            textColor=colors.HexColor('#1B4F72')
        ))
        
        styles.add(ParagraphStyle(
            name='CompanyInfo',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            spaceAfter=2,
            textColor=colors.HexColor('#34495E')
        ))
        
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=20,
            alignment=1,
            textColor=colors.HexColor('#2C3E50')
        ))
        
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.HexColor('#2980B9')
        ))
        
        # Cabeçalho com logo e informações da empresa
        header_data = [
            [
                Paragraph(config['empresa'], styles['CompanyName']),
                Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", styles['CompanyInfo'])
            ],
            [
                Paragraph(f"NUIT: {config['nuit']}", styles['CompanyInfo']),
                Paragraph(f"Hora: {datetime.now().strftime('%H:%M')}", styles['CompanyInfo'])
            ],
            [
                Paragraph(config['endereco'], styles['CompanyInfo']),
                ""
            ],
            [
                Paragraph(f"Tel: {config['telefone']}", styles['CompanyInfo']),
                ""
            ]
        ]
        
        header_table = Table(header_data, colWidths=[7*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, 1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(header_table)
        
        # Linha separadora
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#BDC3C7'),
            spaceBefore=5,
            spaceAfter=10
        ))
        
        # Título do relatório
        periodo = f"Relatório de Vendas\n{self.data_inicial.value} a {self.data_final.value}"
        elements.append(Paragraph(periodo, styles['ReportTitle']))
        
        # Resumo geral no topo
        media_venda = total_geral / total_vendas if total_vendas > 0 else 0
        resumo_data = [
            [
                Paragraph("Total de Vendas", styles['CompanyInfo']),
                Paragraph("Lucro Total", styles['CompanyInfo']),
                Paragraph("Média por Venda", styles['CompanyInfo']),
                Paragraph("Qtd. Vendas", styles['CompanyInfo'])
            ],
            [
                Paragraph(f"MT {total_geral:,.2f}", styles['SectionTitle']),
                Paragraph(f"MT {lucro_geral:,.2f}", styles['SectionTitle']),
                Paragraph(f"MT {media_venda:,.2f}", styles['SectionTitle']),
                Paragraph(f"{total_vendas}", styles['SectionTitle'])
            ]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[2*inch, 2*inch, 2*inch, 2*inch])
        resumo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#7F8C8D')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(resumo_table)
        elements.append(Spacer(1, 20))
        
        # Detalhes por vendedor
        for vendedor_id, dados in vendas_por_vendedor.items():
            # Cabeçalho do vendedor
            vendedor_header = [
                [
                    Paragraph(f"Vendedor: {dados['nome']}", styles['SectionTitle']),
                    Paragraph(f"Total: MT {dados['total']:,.2f}", styles['CompanyInfo']),
                    Paragraph(f"Lucro: MT {dados['lucro']:,.2f}", styles['CompanyInfo'])
                ]
            ]
            
            v_header = Table(vendedor_header, colWidths=[4*inch, 3*inch, 2*inch])
            v_header.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (-1, 0), 'RIGHT'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EBF5FB')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#AED6F1')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(v_header)
            elements.append(Spacer(1, 5))
            
            # Tabela de vendas do vendedor
            data = [[
                Paragraph("Nº", styles['CompanyInfo']),
                Paragraph("Data/Hora", styles['CompanyInfo']),
                Paragraph("Total", styles['CompanyInfo']),
                Paragraph("Forma Pgto.", styles['CompanyInfo']),
                Paragraph("Itens", styles['CompanyInfo'])
            ]]
            
            for venda in dados['vendas']:
                itens_formatados = self.formatar_itens(venda['itens'])
                
                data.append([
                    str(venda['id']),
                    datetime.strptime(venda['data_venda'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M'),
                    f"MT {venda['total']:,.2f}",
                    venda['forma_pagamento'],
                    Paragraph(itens_formatados, ParagraphStyle(
                        'ItensStyle',
                        fontSize=7,      # Fonte menor
                        leading=9,       # Espaçamento entre linhas
                        spaceBefore=0,
                        spaceAfter=0,
                        alignment=0      # Alinhamento à esquerda
                    ))
                ])
            
            # Ajustar larguras das colunas (em modo paisagem)
            table = Table(
                data,
                colWidths=[
                    0.3*inch,     # Nº (reduzido)
                    0.8*inch,     # Data/Hora (reduzido)
                    0.8*inch,     # Total (reduzido)
                    0.8*inch,     # Forma Pgto (reduzido)
                    6.3*inch      # Itens (aumentado)
                ],
                repeatRows=1
            )
            
            # Ajustar estilos da tabela
            table.setStyle(TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),  # Reduzido
                
                # Conteúdo
                ('ALIGN', (0, 1), (3, -1), 'CENTER'),
                ('ALIGN', (4, 1), (4, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (3, -1), 7),  # Reduzido
                ('FONTSIZE', (4, 1), (4, -1), 6),  # Ainda menor para itens
                ('LEADING', (4, 1), (4, -1), 7),   # Espaçamento entre linhas reduzido
                
                # Grades e bordas
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                
                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (3, -1), 2),
                ('RIGHTPADDING', (0, 0), (3, -1), 2),
                ('LEFTPADDING', (4, 1), (4, -1), 4),
                ('RIGHTPADDING', (4, 1), (4, -1), 4),
            ]))
            
            # Ajustar altura das linhas
            for i in range(1, len(data)):
                num_linhas = len(data[i][4].text.split('\n'))
                altura_linha = max(20, num_linhas * 7)  # Reduzido para 7 pixels por linha
                table._argH[i] = altura_linha
            
            elements.append(table)
            elements.append(Spacer(1, 15))
        
        # Rodapé
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#BDC3C7'),
            spaceBefore=5,
            spaceAfter=5
        ))
        elements.append(Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#7F8C8D'),
                alignment=1
            )
        ))
        
        return elements

    def gerar_relatorio_vendas(self, e):
        try:
            # Buscar configurações da empresa
            config = self.db.fetchone("SELECT * FROM printer_config LIMIT 1")
            if not config:
                raise Exception("Configurações da empresa não encontradas")

            # Construir a query base
            query = """
                SELECT 
                    v.id,
                    u.nome as vendedor,
                    u.id as vendedor_id,
                    v.total,
                    v.forma_pagamento,
                    v.data_venda,
                    GROUP_CONCAT(p.nome || ' (' || iv.quantidade || 'x - MT ' || 
                               ROUND(iv.preco_unitario, 2) || ')') as itens,
                    SUM(iv.quantidade * (iv.preco_unitario - iv.preco_custo_unitario)) as lucro
                FROM vendas v
                JOIN usuarios u ON u.id = v.usuario_id
                JOIN itens_venda iv ON iv.venda_id = v.id
                JOIN produtos p ON p.id = iv.produto_id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                AND (v.status IS NULL OR v.status != 'Anulada')
            """
            params = [self.data_inicial.value, self.data_final.value]

            if self.funcionario_dropdown.value != "todos":
                query += " AND u.id = ?"
                params.append(self.funcionario_dropdown.value)

            query += " GROUP BY v.id ORDER BY v.data_venda DESC"

            vendas = self.db.fetchall(query, tuple(params))
            total_vendas = len(vendas)

            if not vendas:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Nenhuma venda encontrada no período!"))
                )
                return

            # Criar PDF
            filename = os.path.join(
                self.relatorios_dir, 
                f"vendas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            doc = SimpleDocTemplate(
                filename,
                pagesize=landscape(letter),
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Agrupar vendas por vendedor
            vendas_por_vendedor = {}
            total_geral = 0
            lucro_geral = 0

            for v in vendas:
                if v['vendedor_id'] not in vendas_por_vendedor:
                    vendas_por_vendedor[v['vendedor_id']] = {
                        'nome': v['vendedor'],
                        'vendas': [],
                        'total': 0,
                        'lucro': 0
                    }
                vendas_por_vendedor[v['vendedor_id']]['vendas'].append(v)
                vendas_por_vendedor[v['vendedor_id']]['total'] += v['total']
                vendas_por_vendedor[v['vendedor_id']]['lucro'] += v['lucro']
                total_geral += v['total']
                lucro_geral += v['lucro']

            # Criar o conteúdo do relatório
            elements = self._create_story(
                vendas_por_vendedor,
                config,
                total_geral,
                lucro_geral,
                total_vendas
            )
            
            # Construir o documento com numeração de página
            doc.build(
                elements,
                onFirstPage=self._add_page_number,
                onLaterPages=self._add_page_number
            )

            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Relatório gerado com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
            # Abrir o arquivo
            os.startfile(filename)

        except Exception as error:
            print(f"Erro ao gerar relatório: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Erro ao gerar relatório!"),
                    bgcolor=ft.colors.RED
                )
            )

    def gerar_relatorio_produtos(self, e):
        try:
            # Buscar dados
            produtos = self.db.fetchall("""
                SELECT 
                    p.codigo,
                    p.nome,
                    p.descricao,
                    p.preco_custo,
                    p.preco_venda,
                    p.estoque,
                    p.estoque_minimo,
                    COALESCE(SUM(iv.quantidade), 0) as quantidade_vendida
                FROM produtos p
                LEFT JOIN itens_venda iv ON iv.produto_id = p.id
                LEFT JOIN vendas v ON v.id = iv.venda_id
                    AND DATE(v.data_venda) BETWEEN ? AND ?
                WHERE p.ativo = 1
                GROUP BY p.id
                ORDER BY quantidade_vendida DESC
            """, (self.data_inicial.value, self.data_final.value))

            # Criar PDF
            filename = os.path.join(
                self.relatorios_dir, 
                f"produtos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            doc = SimpleDocTemplate(
                filename,
                pagesize=landscape(letter),
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Estilo
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )

            # Elementos do PDF
            elements = []
            
            # Título
            title = Paragraph(
                f"Relatório de Produtos ({self.data_inicial.value} a {self.data_final.value})", 
                title_style
            )
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Tabela
            data = [['Código', 'Nome', 'Preço Custo', 'Preço Venda', 'Estoque', 'Mínimo', 'Vendas']]
            for p in produtos:
                data.append([
                    p['codigo'],
                    p['nome'],
                    f"MT {p['preco_custo']:.2f}",
                    f"MT {p['preco_venda']:.2f}",
                    str(p['estoque']),
                    str(p['estoque_minimo']),
                    str(p['quantidade_vendida'])
                ])

            table = Table(data, colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('BACKGROUND', (4, 1), (4, -1), colors.lightgrey),
            ]))
            
            elements.append(table)
            
            # Gerar PDF
            doc.build(elements)

            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("✅ Relatório gerado com sucesso!"),
                    bgcolor=ft.colors.GREEN,
                    duration=3000
                )
            )
            
            # Abrir o arquivo
            os.startfile(filename)

        except Exception as error:
            print(f"Erro ao gerar relatório: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("❌ Erro ao gerar relatório!"),
                    bgcolor=ft.colors.RED,
                    duration=3000
                )
            )

    def validar_datas(self):
        try:
            data_inicial = datetime.strptime(self.data_inicial.value, "%Y-%m-%d")
            data_final = datetime.strptime(self.data_final.value, "%Y-%m-%d")
            if data_final < data_inicial:
                raise ValueError("Data final não pode ser menor que a data inicial")
            return True
        except ValueError as e:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro nas datas: {str(e)}"),
                    bgcolor=ft.colors.RED
                )
            )
            return False

    def mostrar_progresso(self):
        return ft.ProgressBar(
            width=400,
            color=ft.colors.PURPLE,
            bgcolor=ft.colors.PURPLE_100
        )

    def gerar_relatorio_lucros(self, e):
        """Relatório de lucros por período"""
        try:
            if not self.validar_datas():
                return
            
            lucros = self.db.fetchall("""
                SELECT 
                    DATE(v.data_venda) as data,
                    SUM(v.total) as total_vendas,
                    SUM(iv.quantidade * (iv.preco_unitario - iv.preco_custo_unitario)) as lucro
                FROM vendas v
                JOIN itens_venda iv ON iv.venda_id = v.id
                WHERE DATE(v.data_venda) BETWEEN ? AND ?
                AND (v.status IS NULL OR v.status != 'Anulada')
                GROUP BY DATE(v.data_venda)
                ORDER BY data
            """, (self.data_inicial.value, self.data_final.value))
            
            # Implementar geração do PDF...
            
        except Exception as error:
            print(f"Erro ao gerar relatório de lucros: {error}")

    def build(self):
        return ft.Column([
            # Cabeçalho
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/dashboard")
                    ),
                    ft.Icon(
                        name=ft.icons.SUMMARIZE,
                        size=30,
                        color=ft.colors.WHITE
                    ),
                    ft.Text(
                        "Relatórios",
                        size=20,
                        color=ft.colors.WHITE
                    )
                ]),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[ft.colors.PURPLE_900, ft.colors.PURPLE_700]
                ),
                padding=20,
                border_radius=10
            ),
            
            ft.Container(height=20),
            
            # Filtros
            ft.Container(
                content=ft.Column([
                    ft.Text("Filtros", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),  # Texto em branco
                    ft.Row([
                        self.data_inicial,
                        self.data_final,
                        self.funcionario_dropdown
                    ])
                ]),
                bgcolor=ft.colors.BLACK,  # Fundo preto para o container
                padding=20,
                border_radius=10
            ),
            
            ft.Container(height=20),
            
            # Botões de relatórios
            ft.Container(
                content=ft.Column([
                    ft.Text("Relatórios Disponíveis", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                    ft.Row([
                        ft.ElevatedButton(
                            "Relatório de Vendas",
                            icon=ft.icons.POINT_OF_SALE,
                            on_click=self.gerar_relatorio_vendas,
                            style=ft.ButtonStyle(
                                bgcolor={"": ft.colors.BLUE},
                                color=ft.colors.WHITE
                            )
                        ),
                        ft.ElevatedButton(
                            "Relatório de Produtos",
                            icon=ft.icons.INVENTORY,
                            on_click=self.gerar_relatorio_produtos,
                            style=ft.ButtonStyle(
                                bgcolor={"": ft.colors.GREEN},
                                color=ft.colors.WHITE
                            )
                        )
                    ])
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10
            )
        ]) 