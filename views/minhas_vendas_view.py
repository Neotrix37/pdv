import flet as ft
from database.database import Database
from repositories.venda_repository import VendaRepository
import locale
from datetime import datetime, timedelta
from utils.translation_mixin import TranslationMixin
from views.generic_table_style import apply_table_style
from pathlib import Path

class MinhasVendasView(ft.UserControl, TranslationMixin):
    def __init__(self, page: ft.Page, usuario):
        super().__init__()
        self.page = page
        self.page.bgcolor = ft.colors.BLUE_50  # Define cor de fundo
        self.usuario = usuario
        self.db = Database()
        self.venda_repo = VendaRepository()
        # Configurar locale com fallback para ambientes que não suportam pt_PT.UTF-8
        try:
            locale.setlocale(locale.LC_ALL, 'pt_PT.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
                except locale.Error:
                    # Fallback final - usar locale padrão do sistema
                    pass
        
        # Inicializar o texto de total
        self.total_text = ft.Text(
            "Total do Período: MT 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_900
        )
        
        # Data atual e 7 dias atrás
        self.data_atual = datetime.now()
        self.data_7_dias = self.data_atual - timedelta(days=7)
        
        # Campo de busca e filtros
        self.data_inicial = ft.TextField(
            label="Data Inicial",
            width=180,
            height=50,
            value=datetime.now().strftime("%Y-%m-%d"),
            color=ft.colors.GREY_900,
            bgcolor=ft.colors.WHITE
        )
        self.data_final = ft.TextField(
            label="Data Final",
            width=180,
            height=50,
            value=self.data_atual.strftime("%Y-%m-%d"),
            color=ft.colors.GREY_900,
            bgcolor=ft.colors.WHITE,
            read_only=not self.usuario.get('is_admin')  # Somente admin pode alterar
        )
        
        # Filtro de status
        self.filtro_status = ft.Dropdown(
            label="Filtrar por status",
            width=200,
            height=50,
            options=[
                ft.dropdown.Option("Todas"),
                ft.dropdown.Option("Não Fechadas"),
                ft.dropdown.Option("Fechadas")
            ],
            value="Não Fechadas",
            color=ft.colors.GREY_900,
            bgcolor=ft.colors.WHITE
        )
        
        # Tabela de vendas
        self.vendas_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Data")),
                ft.DataColumn(ft.Text("Hora")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("Forma Pagamento")),
                ft.DataColumn(ft.Text("Itens"))
            ],
            rows=[]
        )
        apply_table_style(self.vendas_table)
        
        # Carregar vendas iniciais
        self.carregar_vendas()

    def carregar_vendas(self, e=None):
        try:
            print(f"🔍 Carregando vendas híbridas do usuário {self.usuario['id']} para período {self.data_inicial.value} a {self.data_final.value}")
            
            # Usar repositório híbrido para buscar vendas do usuário
            vendas = self.venda_repo.get_vendas_usuario_com_itens(
                usuario_id=self.usuario['id'],
                data_inicio=self.data_inicial.value,
                data_fim=self.data_final.value,
                status_filter=self.filtro_status.value if self.filtro_status.value != "Todas" else None
            )

            # Calcular total do período
            total_periodo = sum(v['total'] for v in vendas)

            self.vendas_table.rows.clear()
            for v in vendas:
                cor = ft.colors.RED if v['status'] == 'Fechada' else ft.colors.GREY_900
                
                self.vendas_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(v['id']), color=cor)),
                            ft.DataCell(ft.Text(v['data'], color=cor)),
                            ft.DataCell(ft.Text(v['hora'], color=cor)),
                            ft.DataCell(ft.Text(f"MT {v['total']:.2f}", color=cor)),
                            ft.DataCell(ft.Text(v['forma_pagamento'], color=cor)),
                            ft.DataCell(ft.Text(v['itens'], color=cor))
                        ]
                    )
                )

            self.total_text.value = f"Total do Período: MT {total_periodo:.2f}"
            self.update()

        except Exception as error:
            print(f"Erro ao carregar vendas: {error}")

    def mostrar_fechamento_caixa(self, e):
        try:
            # Verificar se há vendas não fechadas de qualquer data
            vendas_abertas = self.db.fetchall("""
                SELECT COUNT(*) as total
                FROM vendas 
                WHERE usuario_id = ?
                AND (status IS NULL OR status != 'Anulada')
                AND (status IS NULL OR status != 'Fechada' OR status = '')
            """, (self.usuario['id'],))
            
            print(f"Total de vendas abertas: {vendas_abertas[0]['total']}")  # Debug

            # Buscar todas as vendas não fechadas agrupadas por forma de pagamento
            vendas_por_forma = self.db.fetchall("""
                SELECT 
                    forma_pagamento,
                    DATE(data_venda) as data,
                    COUNT(*) as quantidade,
                    SUM(total) as total,
                    GROUP_CONCAT(id) as venda_ids
                FROM vendas 
                WHERE usuario_id = ?
                AND (status IS NULL OR status != 'Anulada')
                AND (status IS NULL OR status != 'Fechada' OR status = '')
                GROUP BY forma_pagamento, DATE(data_venda)
                HAVING total > 0
                ORDER BY data
            """, (self.usuario['id'],))
            
            print(f"Vendas por forma encontradas: {len(vendas_por_forma)}")  # Debug
            for v in vendas_por_forma:
                print(f"Forma: {v['forma_pagamento']}, Quantidade: {v['quantidade']}, Total: {v['total']}")  # Debug
            
            # Se não encontrou vendas para fechar
            if not vendas_por_forma:
                # Verificar se existem vendas fechadas
                vendas_fechadas = self.db.fetchall("""
                    SELECT COUNT(*) as total
                    FROM vendas
                    WHERE usuario_id = ?
                    AND status = 'Fechada'
                """, (self.usuario['id'],))
                
                if vendas_fechadas[0]['total'] > 0:
                    mensagem = "Todas as vendas já foram fechadas!"
                else:
                    mensagem = "Não há vendas para fechar!"
                
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(mensagem),
                        bgcolor=ft.colors.ORANGE
                    )
                )
                return

            # Criar conteúdo do diálogo
            content = ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.POINT_OF_SALE, size=30, color=ft.colors.BLUE),
                    ft.Text(
                        "Fechamento de Caixa",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text(
                    f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    color=ft.colors.GREY_700
                ),
                ft.Text(
                    f"Funcionário: {self.usuario['nome']}",
                    color=ft.colors.GREY_700
                ),
                ft.Divider(),
            ], scroll=ft.ScrollMode.AUTO)

            total_sistema = 0
            campos_valores = {}
            
            # Adicionar resumo por forma de pagamento
            for v in vendas_por_forma:
                total_sistema += v['total']
                campo = ft.Container(
                    content=ft.Row([
                        ft.Text("MT ", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                        ft.Text(
                            f"{v['total']:.2f}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLUE_900
                        )
                    ]),
                    padding=ft.padding.only(top=10, bottom=5)
                )
                
                # Adicionar texto de ajuda abaixo
                helper_text = ft.Text(
                    f"{v['quantidade']} venda(s)",
                    size=12,
                    color=ft.colors.GREY_600
                )
                
                # Container para mostrar diferença
                diferenca_text = ft.Text(
                    "Diferença: MT 0.00",
                    color=ft.colors.GREY_700,
                    size=12
                )
                
                campos_valores[v['forma_pagamento']] = {
                    'campo': campo,
                    'sistema': v['total'],
                    'quantidade': v['quantidade'],
                    'venda_ids': v['venda_ids'],
                    'diferenca_text': diferenca_text
                }
                
                content.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(
                                    ft.icons.PAYMENTS,
                                    color=ft.colors.BLUE,
                                    size=20
                                ),
                                ft.Text(
                                    v['forma_pagamento'],
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE,
                                    size=16
                                )
                            ]),
                            campo,
                            ft.Text(
                                f"Total no sistema: MT {v['total']:.2f}",
                                color=ft.colors.GREY_700,
                                size=12
                            ),
                            diferenca_text
                        ]),
                        padding=10,
                        border=ft.border.all(1, ft.colors.BLUE_100),
                        border_radius=10,
                        margin=ft.margin.only(bottom=10)
                    )
                )

            # Texto para mostrar diferença total
            diferenca_total_text = ft.Text(
                "Diferença Total: MT 0.00",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE
            )
            content.controls.append(diferenca_total_text)

            def atualizar_diferenca(forma_pagamento):
                try:
                    # Como os valores não são mais editáveis, a diferença será sempre zero
                    diferenca = 0
                    dados = campos_valores[forma_pagamento]
                    
                    # Atualizar texto da diferença individual
                    cor = ft.colors.GREY_700  # Sem diferença pois não é mais editável
                    dados['diferenca_text'].value = f"Diferença: MT {diferenca:.2f}"
                    dados['diferenca_text'].color = cor
                    
                    # Calcular e atualizar diferença total (sempre zero agora)
                    diferenca_total = 0
                    
                    cor_total = ft.colors.RED if diferenca_total < 0 else ft.colors.GREEN if diferenca_total > 0 else ft.colors.BLUE
                    diferenca_total_text.value = f"Diferença Total: MT {diferenca_total:.2f}"
                    diferenca_total_text.color = cor_total
                    
                    self.page.update()
                except ValueError:
                    pass

            # Campo de observações
            observacoes = ft.TextField(
                label="Observações",
                multiline=True,
                min_lines=2,
                max_lines=4,
                color=ft.colors.BLACK,
                border_color=ft.colors.BLUE
            )
            content.controls.append(ft.Container(observacoes))
            
            # Botão de confirmar
            def confirmar_click(e):
                try:
                    # Preparar dados do fechamento
                    dados_fechamento = {
                        'usuario_id': self.usuario['id'],
                        'data_fechamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'total_sistema': total_sistema,
                        'total_informado': 0,
                        'diferenca': 0,
                        'observacoes': observacoes.value,
                        'detalhes': []
                    }
                    
                    # Registrar fechamento
                    fechamento_id = self.db.registrar_fechamento(dados_fechamento)
                    
                    # Atualizar status de todas as vendas não fechadas
                    self.db.execute("""
                        UPDATE vendas 
                        SET status = 'Fechada'
                        WHERE usuario_id = ?
                        AND (status IS NULL OR status != 'Anulada')
                        AND (status IS NULL OR status != 'Fechada' OR status = '')
                    """, (self.usuario['id'],))
                    
                    # Gerar PDF
                    if self.gerar_pdf_fechamento(dados_fechamento, fechamento_id):
                        self.db.conn.commit()  # Commit somente se tudo der certo
                        dlg.open = False
                        self.page.update()

                        self.page.show_snack_bar(
                            ft.SnackBar(
                                content=ft.Text("Fechamento realizado com sucesso! PDF gerado."),
                                bgcolor=ft.colors.GREEN
                            )
                        )
                        
                        # Atualizar a lista de vendas
                        self.carregar_vendas()
                    else:
                        self.db.conn.rollback()  # Rollback se falhar ao gerar PDF
                        raise Exception("Erro ao gerar PDF")
                except ValueError as ve:
                    self.db.conn.rollback()
                    error_msg = "Por favor, insira valores válidos!"
                    print(f"Erro de validação: {ve}")
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(error_msg),
                            bgcolor=ft.colors.RED
                        )
                    )
                except Exception as error:
                    self.db.conn.rollback()
                    error_msg = f"Erro ao realizar fechamento: {str(error)}"
                    print(error_msg)
                    self.page.show_snack_bar(
                        ft.SnackBar(
                            content=ft.Text(error_msg),
                            bgcolor=ft.colors.RED
                        )
                    )

            # Adicionar botões de ação
            content.controls.append(
                ft.Row([
                    ft.ElevatedButton(
                        "Confirmar",
                        icon=ft.icons.CHECK,
                        on_click=lambda e: self._confirmar_fechamento(e, dlg, campos_valores, total_sistema, observacoes),
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.GREEN,
                            color=ft.colors.WHITE
                        )
                    ),
                    ft.OutlinedButton(
                        "Cancelar",
                        icon=ft.icons.CANCEL,
                        on_click=lambda e: self._cancelar_fechamento(e, dlg)
                    )
                ], alignment=ft.MainAxisAlignment.END)
            )

            # Criar e mostrar diálogo
            dlg = ft.AlertDialog(
                content=content,
                shape=ft.RoundedRectangleBorder(radius=10),
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

        except Exception as error:
            print(f"Erro ao mostrar fechamento: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Erro ao preparar fechamento!"),
                    bgcolor=ft.colors.RED
                )
            )

    def gerar_pdf_fechamento(self, dados_fechamento, fechamento_id):
        """Gera um PDF profissional do fechamento de caixa"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from pathlib import Path
            from datetime import datetime
            
            # Criar diretório para PDFs se não existir
            pdf_dir = Path("pdfs")
            pdf_dir.mkdir(exist_ok=True)
            
            # Nome do arquivo com usuário e timestamp
            nome_usuario = self.usuario.get('nome', 'usuario').replace(' ', '_').lower()
            filename = pdf_dir / f"fechamento_caixa_{nome_usuario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Configurações do documento
            doc = SimpleDocTemplate(
                str(filename),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='TitleStyle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1a237e')
            ))
            
            styles.add(ParagraphStyle(
                name='SubtitleStyle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#283593')
            ))
            
            styles.add(ParagraphStyle(
                name='InfoStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=5,
                alignment=TA_LEFT
            ))
            
            # Inicializar elementos do PDF
            elements = []
            
            # Título
            elements.append(Paragraph("FECHAMENTO DE CAIXA", styles['TitleStyle']))
            elements.append(Spacer(1, 10))
            
            # Informações do fechamento em uma tabela
            info_data = [
                ['Data do Fechamento:', dados_fechamento['data_fechamento'].strftime('%d/%m/%Y %H:%M')],
                ['Funcionário:', self.usuario['nome']],
                ['Nº do Fechamento:', str(fechamento_id)]
            ]
            
            info_table = Table(info_data, colWidths=[150, 300])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#424242')),
            ]))
            elements.append(info_table)
            
            # Adicionar espaço
            elements.append(Spacer(1, 20))
            
            # Tabela de resumo de vendas
            elements.append(Paragraph("RESUMO DE VENDAS", styles['SubtitleStyle']))
            
            # Buscar produtos vendidos no dia
            produtos_vendidos = self.db.fetchall("""
                SELECT p.nome, SUM(iv.quantidade) as quantidade, 
                       p.preco_venda, SUM(iv.subtotal) as total
                FROM itens_venda iv
                JOIN produtos p ON iv.produto_id = p.id
                JOIN vendas v ON iv.venda_id = v.id
                WHERE DATE(v.data_venda) = DATE('now')
                AND v.status = 'Concluída'
                GROUP BY p.id, p.nome, p.preco_venda
                ORDER BY quantidade DESC
            """)
            
            # Dados da tabela com produtos vendidos
            data = [
                ['Forma de Pagamento', 'Qtd. Vendas', 'Total (MT)', 'Produtos Vendidos']
            ]
            
            # Calcular totais
            total_vendas = 0
            total_sistema = 0
            
            # Adicionar formas de pagamento
            for forma in dados_fechamento['formas_pagamento']:
                total_vendas += forma['quantidade_vendas']
                total_sistema += forma['valor_sistema']
                
                # Buscar produtos vendidos para esta forma de pagamento
                produtos_forma = self.db.fetchall("""
                    SELECT p.nome, SUM(iv.quantidade) as quantidade
                    FROM itens_venda iv
                    JOIN produtos p ON iv.produto_id = p.id
                    JOIN vendas v ON iv.venda_id = v.id
                    WHERE DATE(v.data_venda) = DATE('now')
                    AND v.status = 'Fechada'
                    AND v.forma_pagamento = ?
                    GROUP BY p.id, p.nome
                    ORDER BY quantidade DESC
                """, (forma['forma'],))
                
                # Formatar lista de produtos para esta forma de pagamento
                # Limitar o tamanho do texto e adicionar quebras de linha
                produtos_lista = []
                for p in produtos_forma:
                    # Limitar o nome do produto para evitar linhas muito longas
                    nome = (p['nome'][:15] + '...') if len(p['nome']) > 15 else p['nome']
                    produtos_lista.append(f"• {nome} ({p['quantidade']}x)")
                
                # Juntar com quebras de linha
                produtos_str = '\n'.join(produtos_lista) if produtos_lista else "-"
                
                # Adicionar à tabela com estilo que mantém o texto dentro da célula
                data.append([
                    forma['forma'],
                    str(forma['quantidade_vendas']),
                    f"{forma['valor_sistema']:.2f}",
                    produtos_str
                ])
            
            # Adicionar linha de total
            total_produtos = sum(p['quantidade'] for p in produtos_vendidos)
            data.append([
                'TOTAL',
                str(total_vendas),
                f"{total_sistema:.2f}",
                f"{total_produtos} itens"
            ])
            
            # Criar e estilizar a tabela com colunas ajustadas
            col_widths = [120, 60, 80, 280]  # Ajuste das larguras para dar mais espaço aos produtos
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # Tamanho de fonte menor
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Cabeçalho em negrito
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Espaçamento inferior do cabeçalho
                ('LEFTPADDING', (0, 0), (-1, -1), 4),  # Espaçamento interno
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),  # Espaçamento interno
                ('WORDWRAP', (3, 1), (3, -1), True),  # Quebra de linha para a coluna de produtos
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Primeira coluna alinhada à esquerda
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),  # Coluna de produtos alinhada à esquerda
                ('FONTSIZE', (3, 1), (3, -1), 7),  # Fonte menor para a coluna de produtos
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),  # Linhas da grade
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Alinha a primeira coluna à esquerda
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),  # Alinha a coluna de produtos à esquerda
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                # Corpo da tabela
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#424242')),
                ('ALIGN', (1, 1), (2, -1), 'CENTER'),  # Centraliza apenas quantidade e total
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),  # Fonte um pouco menor para caber mais conteúdo
                ('FONTSIZE', (3, 1), (3, -1), 8),  # Fonte ainda menor para a coluna de produtos
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
                # Linha de total
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 10)
            ]))
            
            elements.append(table)
            
            # Lista de produtos vendidos
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("PRODUTOS VENDIDOS", styles['SubtitleStyle']))
            
            # Buscar produtos vendidos no dia
            produtos_vendidos = self.db.fetchall("""
                SELECT p.nome, SUM(iv.quantidade) as quantidade, 
                       p.preco_venda, SUM(iv.subtotal) as total
                FROM itens_venda iv
                JOIN produtos p ON iv.produto_id = p.id
                JOIN vendas v ON iv.venda_id = v.id
                WHERE DATE(v.data_venda) = DATE('now')
                AND v.status = 'Concluída'
                GROUP BY p.id, p.nome, p.preco_venda
                ORDER BY quantidade DESC
            """)
            
            if produtos_vendidos:
                # Tabela de produtos vendidos
                produtos_data = [['Produto', 'Qtd', 'Preço Unit.', 'Total']]
                
                for produto in produtos_vendidos:
                    produtos_data.append([
                        produto['nome'],
                        str(produto['quantidade']),
                        f"{produto['preco_venda']:.2f}",
                        f"{produto['total']:.2f}"
                    ])
                
                # Calcular totais
                total_qtd = sum(p['quantidade'] for p in produtos_vendidos)
                total_geral = sum(p['total'] for p in produtos_vendidos)
                
                produtos_data.append([
                    'TOTAL',
                    str(total_qtd),
                    '',
                    f"{total_geral:.2f}"
                ])
                
                # Estilo da tabela de produtos
                col_widths = [250, 50, 100, 100]
                produtos_table = Table(produtos_data, colWidths=col_widths)
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),  # Cabeçalho azul
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texto do cabeçalho branco
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alinhamento centralizado
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Fonte do cabeçalho em negrito
                    ('FONTSIZE', (0, 0), (-1, 0), 10),  # Tamanho da fonte do cabeçalho
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espaçamento inferior do cabeçalho
                    ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#F2F2F2')),  # Cor de fundo das linhas
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),  # Cor do texto
                    ('FONTSIZE', (0, 1), (-1, -1), 8),  # Tamanho da fonte das células
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Alinhamento à esquerda para a primeira coluna
                    ('ALIGN', (-1, 0), (-1, -1), 'LEFT'),  # Alinhamento à esquerda para a última coluna
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D9D9D9')),  # Linhas da grade
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
                    ('LEFTPADDING', (0, 0), (-1, -1), 3),  # Espaçamento à esquerda
                    ('RIGHTPADDING', (0, 0), (-1, -1), 3),  # Espaçamento à direita
                    ('TOPPADDING', (0, 0), (-1, -1), 3),  # Espaçamento superior
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # Espaçamento inferior
                    ('WORDWRAP', (3, 0), (3, -1), True),  # Quebra de linha para a coluna de produtos
                    ('FONTSIZE', (3, 0), (3, -1), 7),  # Fonte menor para a coluna de produtos
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, -1), (-1, -1), 12)
                ]
                produtos_table.setStyle(TableStyle(table_style))
                
                elements.append(produtos_table)
            
            # Observações
            if 'observacoes' in dados_fechamento and dados_fechamento['observacoes']:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("OBSERVAÇÕES", styles['SubtitleStyle']))
                elements.append(Paragraph(dados_fechamento['observacoes'], styles['InfoStyle']))
            
            # Assinaturas
            elements.append(Spacer(1, 30))
            
            signatures = Table([
                ['_' * 30, '_' * 30],
                ['Assinatura do Funcionário', 'Assinatura do Supervisor'],
            ], colWidths=[250, 250])
            
            signatures.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('TOPPADDING', (0, 1), (-1, 1), 5),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#424242')),
            ]))
            elements.append(signatures)
            
            # Gerar o PDF
            doc.build(elements)
            print(f"PDF gerado com sucesso: {filename}")
            return True

        except Exception as error:
            print(f"Erro ao gerar PDF: {error}")
            import traceback
            traceback.print_exc()
            return False

    def _mostrar_dialogo_reset_cards(self, dlg, dados_fechamento):
        """Método mantido para compatibilidade, mas não é mais usado"""
        # Este método é mantido apenas para compatibilidade, mas não faz mais nada
        # O comportamento de reset de cards agora é gerenciado automaticamente
        pass

    def _confirmar_fechamento(self, e, dlg, campos_valores, total_sistema, observacoes):
        """Confirma o fechamento de caixa e gera o PDF"""
        try:
            # Calcular o total informado somando os valores do sistema
            total_informado = sum(dados['sistema'] for dados in campos_valores.values())
            
            dados_fechamento = {
                'usuario_id': self.usuario['id'],
                'data_fechamento': datetime.now(),
                'valor_sistema': total_sistema,
                'valor_informado': total_informado,
                'diferenca': 0,  # Sem diferença pois não é mais editável
                'observacoes': observacoes.value if hasattr(observacoes, 'value') else '',
                'formas_pagamento': []
            }

            for forma, dados in campos_valores.items():
                # Usar o valor do sistema já que não é mais editável
                valor_informado = dados['sistema']
                
                dados_fechamento['formas_pagamento'].append({
                    'forma': forma,
                    'valor_sistema': dados['sistema'],
                    'valor_informado': valor_informado,
                    'diferenca': 0,  # Sem diferença pois não é mais editável
                    'quantidade_vendas': dados['quantidade']
                })

            # Registrar fechamento
            fechamento_id = self.db.registrar_fechamento(dados_fechamento)
            
            # Atualizar status de todas as vendas não fechadas
            self.db.execute("""
                UPDATE vendas 
                SET status = 'Fechada'
                WHERE usuario_id = ?
                AND (status IS NULL OR status != 'Anulada')
                AND (status IS NULL OR status != 'Fechada')
            """, (self.usuario['id'],))
            
            # Fechar o diálogo de fechamento
            dlg.open = False
            self.page.update()
            
            # Gerar o PDF do fechamento
            if not self.gerar_pdf_fechamento(dados_fechamento, fechamento_id):
                raise Exception("Erro ao gerar PDF do fechamento")
            
            # Mostrar mensagem de sucesso
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Caixa fechado com sucesso!"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
            # Atualizar a lista de vendas
            self.carregar_vendas()

        except Exception as error:
            print(f"Erro ao confirmar fechamento: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao realizar fechamento: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )

    def _cancelar_fechamento(self, e, dlg):
        """Fecha o diálogo de fechamento"""
        dlg.open = False
        self.page.update()

    def build(self):
        # Cabeçalho com botão de fechamento
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
                    self.t("my_sales"),
                    size=20,
                    color=ft.colors.WHITE
                ),
                ft.Container(expand=True),  # Espaçador flexível
                ft.ElevatedButton(
                    "Fechar Caixa",
                    icon=ft.icons.POINT_OF_SALE,
                    on_click=self.mostrar_fechamento_caixa,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN
                    )
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

        # Filtros
        filtros = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.data_inicial,
                    self.data_final,
                    self.filtro_status,
                    ft.ElevatedButton(
                        "Atualizar",
                        icon=ft.icons.SEARCH,
                        on_click=self.carregar_vendas,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE_700
                        )
                    )
                ], spacing=10, scroll=ft.ScrollMode.ALWAYS, wrap=True),
                ft.Row([
                    ft.ElevatedButton(
                        "Atualizar",
                        icon=ft.icons.REFRESH,
                        on_click=self.carregar_vendas,
                        visible=self.usuario.get('is_admin')  # Botão visível apenas para admin
                    )
                ]),
                self.total_text
            ]),
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10
        )

        # Container da tabela
        table_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Últimos 7 dias de vendas" if not self.usuario.get('is_admin') else "Vendas no período",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE
                ),
                ft.Container(
                    content=ft.Column(
                        [self.vendas_table],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    height=300,  # Altura fixa para o container
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
    # End of MinhasVendasView class
