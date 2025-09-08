import flet as ft
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import sys
import json

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
            
            for item in itens_str.split(','):
                item = item.strip()
                if not item:
                    continue
                
                # Se o item já estiver formatado, adiciona como está
                if 'MT' in item and 'x' in item:
                    # Extrai o nome e as informações
                    if '(' in item and ')' in item:
                        nome = item.split('(')[0].strip()
                        info = item[item.find('(')+1:item.rfind(')')].strip()
                        
                        # Formata o nome (limite de 30 caracteres)
                        if len(nome) > 30:
                            nome = nome[:27] + '...'
                            
                        # Formata as informações (quantidade e preço)
                        partes = info.split('MT')
                        info_formatada = []
                        for part in partes:
                            part = part.strip()
                            if part and 'x' in part:
                                qtd = part.split('x')[0].strip()
                                if qtd.isdigit():
                                    info_formatada.append(f"{qtd}x")
                        
                        item_formatado = f"{nome} ({' '.join(info_formatada)})"
                    else:
                        item_formatado = nome
                        
                else:
                    # Para itens sem formatação especial
                    if len(item) > 30:
                        item_formatado = item[:27] + '...'
                    else:
                        item_formatado = item
                
                itens_lista.append(item_formatado)
            
            return '\n'.join(itens_lista)  # Espaço simples entre itens
            
        except Exception as e:
            print(f"Erro ao formatar itens: {e}")
            return itens_str
    
    def _add_summary_cards(self, elements, total_geral, lucro_geral, total_vendas, styles, 
                          primary_color, secondary_color, success_color, light_gray):
        """Adiciona cards de resumo no topo do relatório"""
        from reportlab.lib.pagesizes import letter
        
        # Estilo para os cards
        card_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),  # Cabeçalho do card
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Corpo do card
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E9ECEF')),  # Borda sutil
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E9ECEF')),  # Linhas internas
            ('PADDING', (0, 0), (-1, -1), 10),  # Espaçamento interno
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ])
        
        # Dados para os cards
        ticket_medio = total_geral/total_vendas if total_vendas > 0 else 0
        
        card_data = [
            ["💰 TOTAL VENDIDO", f"MT {total_geral:,.2f}"],
            ["📈 LUCRO TOTAL", f"MT {lucro_geral:,.2f}"],
            ["📊 TICKET MÉDIO", f"MT {ticket_medio:,.2f}" if total_vendas > 0 else "N/A"],
            ["🛒 TOTAL DE VENDAS", str(total_vendas)]
        ]
        
        # Criar tabela de cards (4 colunas)
        card_table = Table(card_data, colWidths=[letter[0]/4.5]*4, hAlign='CENTER')
        card_table.setStyle(card_style)
        
        # Adicionar cards ao relatório
        elements.append(Spacer(1, 10))
        elements.append(card_table)
        elements.append(Spacer(1, 20))
        
        # Adicionar linha divisória
        elements.append(HRFlowable(width="90%", thickness=1, lineCap='round', 
                                 color=colors.HexColor('#E9ECEF'), 
                                 spaceBefore=10, spaceAfter=10))

    def _quebrar_texto(self, texto, max_chars):
        """Quebra o texto em várias linhas respeitando o limite de caracteres"""
        if len(texto) <= max_chars:
            return texto
            
        linhas = []
        palavras = texto.split()
        linha_atual = []
        
        for palavra in palavras:
            # Se a palavra for muito grande, quebra ela
            if len(palavra) > max_chars:
                if linha_atual:
                    linhas.append(' '.join(linha_atual))
                    linha_atual = []
                # Quebra a palavra grande em partes
                for i in range(0, len(palavra), max_chars):
                    linhas.append(palavra[i:i+max_chars])
            else:
                # Testa se a palavra cabe na linha atual
                if sum(len(p) for p in linha_atual) + len(linha_atual) + len(palavra) <= max_chars:
                    linha_atual.append(palavra)
                else:
                    if linha_atual:
                        linhas.append(' '.join(linha_atual))
                    linha_atual = [palavra]
        
        # Adiciona a última linha se necessário
        if linha_atual:
            linhas.append(' '.join(linha_atual))
            
        return '\n'.join(linhas)

    def _create_story(self, vendas_por_vendedor, config, total_geral, lucro_geral, total_vendas):
        """Cria o conteúdo do relatório com layout profissional e moderno"""
        styles = getSampleStyleSheet()
        elements = []
        
        # Cores do tema
        primary_color = colors.HexColor('#2C3E50')  # Azul escuro
        secondary_color = colors.HexColor('#3498DB')  # Azul
        success_color = colors.HexColor('#2ECC71')  # Verde
        light_gray = colors.HexColor('#F8F9FA')
        dark_gray = colors.HexColor('#6C757D')
        
        # Estilos personalizados
        styles.add(ParagraphStyle(
            name='ReportHeader',
            parent=styles['Heading1'],
            fontSize=18,
            spaceBefore=20,
            spaceAfter=10,
            alignment=1,  # Center
            textColor=primary_color,
            fontName='Helvetica-Bold',
            leading=24
        ))
        
        styles.add(ParagraphStyle(
            name='ReportSubheader',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=20,
            alignment=1,  # Center
            textColor=dark_gray,
            fontName='Helvetica',
            leading=14
        ))
        
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=25,
            spaceAfter=10,
            textColor=primary_color,
            fontName='Helvetica-Bold',
            backColor=colors.lightgrey,
            borderWidth=1,
            borderColor=colors.grey,
            borderPadding=(5, 5, 5, 5)
        ))
        
        styles.add(ParagraphStyle(
            name='VendedorTitle',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=20,
            spaceAfter=8,
            textColor=secondary_color,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=secondary_color,
            borderPadding=(0, 0, 2, 0),
            leftIndent=10
        ))
        
        # Cabeçalho do relatório
        empresa = config.get('nome_empresa', 'Sistema de Vendas')
        data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Título principal
        elements.append(Paragraph("RELATÓRIO DE VENDAS", styles['ReportHeader']))
        
        # Subtítulo com período e data de geração
        periodo = f"Período: {self.data_inicial.value} a {self.data_final.value} • Gerado em: {data_geracao}"
        elements.append(Paragraph(periodo, styles['ReportSubheader']))
        
        # Linha decorativa
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', 
                                 color=colors.HexColor('#E9ECEF'), spaceBefore=5, spaceAfter=20))
        
        # Adicionar cards de resumo
        self._add_summary_cards(elements, total_geral, lucro_geral, total_vendas, styles, 
                              primary_color, secondary_color, success_color, light_gray)
                              
        # Adicionar seção de vendas por vendedor
        elements.append(Paragraph("VENDAS POR VENDEDOR", styles['SectionTitle']))
        
        for vendedor_id, dados in vendas_por_vendedor.items():
            # Cabeçalho do vendedor
            vendedor_header = [
                [
                    Paragraph(f"Vendedor: {dados['nome']}", styles['VendedorTitle']),
                    Paragraph(f"Total: MT {dados['total']:,.2f}", styles['SectionTitle']),
                    Paragraph(f"Lucro: MT {dados['lucro']:,.2f}", styles['SectionTitle'])
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
                Paragraph("Nº", styles['SectionTitle']),
                Paragraph("Data/Hora", styles['SectionTitle']),
                Paragraph("Total", styles['SectionTitle']),
                Paragraph("Forma Pgto.", styles['SectionTitle']),
                Paragraph("Itens", styles['SectionTitle'])
            ]]
            
            for venda_row in dados['vendas']:
                # Função auxiliar para obter valor de forma segura
                def get_venda_value(row, key, default=''):
                    try:
                        # Se for um SQLite Row
                        if hasattr(row, 'keys') and hasattr(row, '__getitem__'):
                            return row[key] if key in row.keys() else default
                        # Se for dicionário
                        elif isinstance(row, dict):
                            return row.get(key, default)
                        # Se for lista/tupla
                        elif isinstance(row, (list, tuple)):
                            idx = ['id', 'vendedor', 'vendedor_id', 'total', 'forma_pagamento', 'data_venda', 'itens', 'lucro'].index(key)
                            return row[idx] if idx < len(row) else default
                        return default
                    except (KeyError, ValueError, IndexError, AttributeError):
                        return default
                
                # Obter valores de forma segura
                venda_id = str(get_venda_value(venda_row, 'id', ''))
                data_venda = get_venda_value(venda_row, 'data_venda', '')
                total = float(str(get_venda_value(venda_row, 'total', '0')).replace(',', '.'))
                forma_pagamento = get_venda_value(venda_row, 'forma_pagamento', '')
                itens = get_venda_value(venda_row, 'itens', '')
                itens_formatados = self.formatar_itens(itens) if itens else ''
                
                data.append([
                    venda_id,
                    str(data_venda).split(' ')[0] if data_venda else '',  # Apenas a data
                    f"MT {total:.2f}",
                    forma_pagamento,
                    Paragraph(itens_formatados, ParagraphStyle(
                        'ItensStyle',
                        fontSize=7,      # Fonte menor
                        leading=9,       # Espaçamento entre linhas
                        spaceBefore=0,
                        spaceAfter=0,
                        alignment=0      # Alinhamento à esquerda
                    ))
                ])
            
            # Ajustar larguras das colunas (em modo paisagem) com mais espaço
            table = Table(
                data,
                colWidths=[
                    0.5*inch,     # Nº
                    1.2*inch,     # Data/Hora
                    1.0*inch,     # Total
                    1.2*inch,     # Forma Pgto
                    5.1*inch      # Itens (mais espaço para os itens)
                ],
                repeatRows=1,
                hAlign='LEFT',
                style=[
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('WORDWRAP', (0, 0), (-1, -1), 1),  # Quebra de linha automática
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alinhamento no topo
                    ('FONTSIZE', (0, 0), (-1, -1), 8),  # Fonte um pouco menor
                ]
            )
            
            # Ajustar estilos da tabela
            table.setStyle(TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),  # Fundo branco
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Texto preto
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),  # Fonte um pouco menor
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Conteúdo
                ('ALIGN', (0, 1), (3, -1), 'CENTER'),
                ('ALIGN', (4, 1), (4, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alinhamento no topo
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (3, -1), 8),  # Fonte um pouco menor
                ('FONTSIZE', (4, 1), (4, -1), 8),  # Fonte um pouco menor
                ('LEADING', (0, 1), (-1, -1), 9),   # Espaçamento entre linhas reduzido
                ('WORDWRAP', (0, 0), (-1, -1), 1),  # Quebra de linha automática
                ('TOPPADDING', (0, 0), (-1, -1), 2),  # Menos espaço no topo
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),  # Menos espaço em baixo
                
                # Grades e bordas - apenas linhas horizontais
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),  # Linha abaixo de cada linha
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#2C3E50')),  # Linha acima do cabeçalho
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#2C3E50')),  # Linha abaixo do cabeçalho
                
                # Padding e espaçamento
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f0f0f0')),  # Grade clara para guia visual
            ]))
            
            # Ajustar altura das linhas (máximo de 3 linhas por item)
            for i in range(1, len(data)):
                num_linhas = len(data[i][4].text.split('\n'))
                altura_linha = min(30, max(15, num_linhas * 8))  # Altura entre 15 e 30
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
                alignment=2,  # Alinhado à direita
                fontName='Helvetica-Oblique'
            )
        ))
        
        return elements

    def _get_formas_pagamento(self):
        """Retorna um dicionário com as formas de pagamento disponíveis"""
        return {
            'dinheiro': 'Dinheiro',
            'multicaixa': 'Multicaixa',
            'transferencia': 'Transferência',
            'mbway': 'MB Way',
            'outro': 'Outro'
        }

    def _get_estatisticas_vendas(self, vendas):
        """Calcula estatísticas das vendas"""
        if not vendas:
            return {}
            
        totais_por_forma = {}
        total_geral = 0
        total_itens = 0
        lucro_bruto = 0
        
        formas_pagamento = self._get_formas_pagamento()
        
        # Inicializa totais por forma de pagamento
        for forma in formas_pagamento.values():
            totais_por_forma[forma] = 0
        
        # Processa cada venda
        for venda in vendas:
            total = float(str(venda['total']).replace(',', '.'))
            forma_pagamento = venda['forma_pagamento'] if 'forma_pagamento' in venda and venda['forma_pagamento'] else 'outro'
            forma_pagamento = formas_pagamento[forma_pagamento] if forma_pagamento in formas_pagamento else 'Outro'
            
            # Atualiza totais
            totais_por_forma[forma_pagamento] += total
            total_geral += total
            
            # Calcula lucro bruto
            lucro = float(str(venda['lucro']).replace(',', '.')) if 'lucro' in venda and venda['lucro'] else 0.0
            lucro_bruto += lucro
            
            # Conta itens
            itens = venda['itens'].split(',') if 'itens' in venda and venda['itens'] else []
            for item in itens:
                if 'x' in item:
                    try:
                        qtd = int(item.split('x')[0].strip().split('(')[-1].strip())
                        total_itens += qtd
                    except (ValueError, IndexError):
                        continue
        
        # Calcula ticket médio
        ticket_medio = total_geral / len(vendas) if vendas else 0
        
        # Ordena formas de pagamento por valor (maior para menor)
        formas_ordenadas = sorted(
            totais_por_forma.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Encontra a melhor venda
        melhor_venda = {'total': 0, 'id': 0}
        for venda in vendas:
            try:
                total = float(str(venda['total']).replace(',', '.'))
                if total > melhor_venda['total']:
                    melhor_venda = {
                        'total': total,
                        'id': venda['id'] if 'id' in venda else 0
                    }
            except (KeyError, ValueError):
                continue
        
        return {
            'total_geral': total_geral,
            'lucro_bruto': lucro_bruto,
            'ticket_medio': ticket_medio,
            'total_vendas': len(vendas),
            'total_itens': total_itens,
            'formas_pagamento': dict(formas_ordenadas),
            'melhor_venda': melhor_venda
        }

    def _get_vendas_por_periodo(self, vendas):
        """Agrupa vendas por período (dia, semana, mês)"""
        if not vendas:
            return {}
            
        vendas_por_dia = {}
        
        for venda in vendas:
            try:
                data_venda = datetime.strptime(str(venda['data_venda']).split('.')[0], '%Y-%m-%d %H:%M:%S')
                data_str = data_venda.strftime('%Y-%m-%d')
                
                if data_str not in vendas_por_dia:
                    vendas_por_dia[data_str] = {
                        'total': 0,
                        'vendas': 0,
                        'itens': 0,
                        'lucro': 0
                    }
                
                total = float(str(venda['total']).replace(',', '.'))
                lucro = float(str(venda.get('lucro', '0')).replace(',', '.'))
                
                vendas_por_dia[data_str]['total'] += total
                vendas_por_dia[data_str]['vendas'] += 1
                vendas_por_dia[data_str]['lucro'] += lucro
                
                # Conta itens
                itens = venda['itens'].split(',') if venda['itens'] else []
                for item in itens:
                    if 'x' in item:
                        try:
                            qtd = int(item.split('x')[0].strip().split('(')[-1].strip())
                            vendas_por_dia[data_str]['itens'] += qtd
                        except (ValueError, IndexError):
                            continue
                            
            except Exception as e:
                print(f"Erro ao processar venda {venda['id'] if 'id' in venda else 'N/A'}: {e}")
                continue
        
        return vendas_por_dia

    def _get_produtos_mais_vendidos(self, vendas, limite=10):
        """Retorna os produtos mais vendidos"""
        produtos = {}
        
        for venda in vendas:
            itens = venda['itens'].split(',') if 'itens' in venda and venda['itens'] else []
            for item in itens:
                try:
                    if 'x' not in item:
                        continue
                        
                    # Extrai nome e quantidade do item
                    partes = item.split('x')
                    qtd = int(partes[0].strip().split('(')[-1].strip())
                    nome = item.split('(')[0].strip()
                    
                    if nome in produtos:
                        produtos[nome] += qtd
                    else:
                        produtos[nome] = qtd
                        
                except (ValueError, IndexError, AttributeError):
                    continue
        
        # Ordena por quantidade (mais vendidos primeiro)
        return dict(sorted(produtos.items(), key=lambda x: x[1], reverse=True)[:limite])

    def gerar_relatorio_vendas(self, e):
        try:
            # Validar datas
            if not self.validar_datas():
                return
                
            # Buscar configurações da empresa do arquivo config.json
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                # Configurações padrão se o arquivo não existir
                config = {
                    'nome_empresa': 'Minha Empresa',
                    'endereco': 'Endereço não configurado',
                    'telefone': '',
                    'email': '',
                    'cnpj': ''
                }

            # Construir a query base
            query = """
                SELECT 
                    v.id,
                    u.nome as vendedor,
                    u.id as vendedor_id,
                    v.total,
                    v.forma_pagamento,
                    v.data_venda,
                    v.status,
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

            # Filtro por vendedor
            if self.funcionario_dropdown.value != "todos":
                query += " AND u.id = ?"
                params.append(self.funcionario_dropdown.value)

            query += " GROUP BY v.id ORDER BY v.data_venda DESC"

            # Executar consulta
            vendas = self.db.fetchall(query, tuple(params))
            
            if not vendas:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Nenhuma venda encontrada no período selecionado!"),
                        bgcolor=ft.colors.ORANGE
                    )
                )
                return

            # Calcular estatísticas
            estatisticas = self._get_estatisticas_vendas(vendas)
            vendas_por_dia = self._get_vendas_por_periodo(vendas)
            produtos_mais_vendidos = self._get_produtos_mais_vendidos(vendas)

            # Criar PDF
            filename = os.path.join(
                self.relatorios_dir, 
                f"relatorio_vendas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            doc = SimpleDocTemplate(
                filename,
                pagesize=landscape(letter),
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            
            # Configurações de estilo
            styles = getSampleStyleSheet()
            
            # Estilo para o título
            styles.add(ParagraphStyle(
                name='TituloRelatorio',
                parent=styles['Title'],
                fontSize=18,
                textColor=colors.HexColor('#2C3E50'),
                alignment=1,  # Center
                spaceAfter=20
            ))
            
            # Estilo para subtítulos
            styles.add(ParagraphStyle(
                name='Subtitulo',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#34495E'),
                spaceBefore=20,
                spaceAfter=10,
                backColor=colors.HexColor('#EBF5FB'),
                borderPadding=(5, 5, 5, 5),
                borderWidth=1,
                borderColor=colors.HexColor('#D6EAF8')
            ))
            
            # Estilo para métricas
            styles.add(ParagraphStyle(
                name='Metrica',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#2C3E50'),
                leading=14,
                spaceAfter=5
            ))
            
            # Elementos do relatório
            elements = []
            
            # Cabeçalho
            header_table = Table([
                [
                    Paragraph("<b>RELATÓRIO DE VENDAS</b>", 
                             style=ParagraphStyle(
                                 name='HeaderTitle',
                                 fontSize=16,
                                 textColor=colors.HexColor('#2C3E50'),
                                 alignment=0,
                                 spaceAfter=5
                             )),
                    Paragraph(
                        f"<b>Período:</b> {self.data_inicial.value} a {self.data_final.value}<br/>"
                        f"<b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        style=ParagraphStyle(
                            name='HeaderInfo',
                            fontSize=9,
                            textColor=colors.HexColor('#7F8C8D'),
                            alignment=2,
                            leading=12
                        )
                    )
                ]
            ], colWidths=[doc.width*0.6, doc.width*0.4])
            
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            elements.append(header_table)
            
            # Linha divisória
            elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#E0E0E0'), spaceAfter=20))
            
            # Seção de resumo
            elements.append(Paragraph("VISÃO GERAL", style=ParagraphStyle(
                name='SectionTitle',
                fontSize=12,
                textColor=colors.HexColor('#2C3E50'),
                fontName='Helvetica-Bold',
                spaceAfter=10,
                backColor=colors.HexColor('#F8F9FA'),
                borderWidth=1,
                borderColor=colors.HexColor('#E0E0E0'),
                borderPadding=(5, 5, 5, 5),
                borderRadius=3
            )))
            
            # Métricas principais - Layout em cards
            metrics_style = TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#2C3E50')),  # Cabeçalho coluna 1
                ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#27AE60')),  # Cabeçalho coluna 2
                ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#3498DB')),  # Cabeçalho coluna 3
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Cor do texto do cabeçalho
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
            ])

            # Métricas principais
            metricas_data = [
                [
                    Paragraph("<b>VENDAS TOTAIS</b>", styles['Normal']),
                    Paragraph("<b>LUCRO BRUTO</b>", styles['Normal']),
                    Paragraph("<b>TICKET MÉDIO</b>", styles['Normal'])
                ],
                [
                    Paragraph(f"<font size='14' color='#2C3E50'><b>MT {estatisticas['total_geral']:,.2f}</b></font>", styles['Normal']),
                    Paragraph(f"<font size='14' color='#27AE60'><b>MT {estatisticas['lucro_bruto']:,.2f}</b></font>", styles['Normal']),
                    Paragraph(f"<font size='14' color='#3498DB'><b>MT {estatisticas['ticket_medio']:,.2f}</b></font>", styles['Normal'])
                ],
                [
                    Paragraph(f"{estatisticas['total_vendas']} vendas", styles['Normal']),
                    Paragraph(f"{estatisticas['total_itens']} itens vendidos", styles['Normal']),
                    Paragraph(f"Melhor venda: MT {float(str(estatisticas['melhor_venda'].get('total', 0)).replace(',', '.')):,.2f}", styles['Normal'])
                ]
            ]
            
            # Tabela de métricas
            t = Table(metricas_data, colWidths=[doc.width/3.0]*3)
            t.setStyle(metrics_style)
            
            elements.append(t)
            elements.append(Spacer(1, 20))
            
            # Seção de vendas por dia
            if vendas_por_dia:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("VENDAS POR DIA", style=ParagraphStyle(
                    name='SectionTitle',
                    fontSize=12,
                    textColor=colors.HexColor('#2C3E50'),
                    fontName='Helvetica-Bold',
                    spaceAfter=10,
                    backColor=colors.HexColor('#F8F9FA'),
                    borderWidth=1,
                    borderColor=colors.HexColor('#E0E0E0'),
                    borderPadding=(5, 5, 5, 5),
                    borderRadius=3
                )))
                
                # Preparar dados para o gráfico
                dias = sorted(vendas_por_dia.keys())
                totais = [vendas_por_dia[dia]['total'] for dia in dias]
                lucros = [vendas_por_dia[dia]['lucro'] for dia in dias]
                
                # Tabela de vendas por dia
                data = [['Data', 'Vendas', 'Total (MT)', 'Lucro (MT)', 'Itens']]
                
                for dia in sorted(dias, reverse=True):
                    data.append([
                        dia,
                        vendas_por_dia[dia]['vendas'],
                        f"{vendas_por_dia[dia]['total']:,.2f}",
                        f"{vendas_por_dia[dia]['lucro']:,.2f}",
                        vendas_por_dia[dia]['itens']
                    ])
                
                t = Table(data, colWidths=[doc.width/5.0]*5)
                t.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    # Destaque para o dia com maior venda
                    ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#27AE60')),
                    ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
                ]))
                
                elements.append(t)
                elements.append(Spacer(1, 20))
            
            # Seção de produtos mais vendidos
            if produtos_mais_vendidos:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("PRODUTOS MAIS VENDIDOS", style=ParagraphStyle(
                    name='SectionTitle',
                    fontSize=12,
                    textColor=colors.HexColor('#2C3E50'),
                    fontName='Helvetica-Bold',
                    spaceAfter=10,
                    backColor=colors.HexColor('#F8F9FA'),
                    borderWidth=1,
                    borderColor=colors.HexColor('#E0E0E0'),
                    borderPadding=(5, 5, 5, 5),
                    borderRadius=3
                )))
                
                data = [['Posição', 'Produto', 'Quantidade', 'Participação']]
                total_itens = sum(produtos_mais_vendidos.values())
                
                for i, (produto, qtd) in enumerate(produtos_mais_vendidos.items(), 1):
                    participacao = (qtd / total_itens) * 100
                    data.append([
                        str(i),
                        produto,
                        str(qtd),
                        f"{participacao:.1f}%"
                    ])
                
                t = Table(data, colWidths=[doc.width*0.1, doc.width*0.5, doc.width*0.2, doc.width*0.2])
                t.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    # Destaque para o top 3
                    ('FONTNAME', (0, 1), (0, 3), 'Helvetica-Bold'),
                    ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#F1C40F')),  # Ouro
                    ('TEXTCOLOR', (0, 2), (0, 2), colors.HexColor('#95A5A6')),  # Prata
                    ('TEXTCOLOR', (0, 3), (0, 3), colors.HexColor('#D35400')),  # Bronze
                ]))
                
                elements.append(t)
                elements.append(Spacer(1, 20))
            
            # Seção de formas de pagamento
            if estatisticas.get('formas_pagamento'):
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("FORMA DE PAGAMENTO", style=ParagraphStyle(
                    name='SectionTitle',
                    fontSize=12,
                    textColor=colors.HexColor('#2C3E50'),
                    fontName='Helvetica-Bold',
                    spaceAfter=10,
                    backColor=colors.HexColor('#F8F9FA'),
                    borderWidth=1,
                    borderColor=colors.HexColor('#E0E0E0'),
                    borderPadding=(5, 5, 5, 5),
                    borderRadius=3
                )))
                
                data = [['Forma de Pagamento', 'Total (MT)', 'Participação']]
                total_geral = estatisticas['total_geral']
                
                for forma, total in estatisticas['formas_pagamento'].items():
                    if total > 0:  # Mostrar apenas formas de pagamento utilizadas
                        participacao = (total / total_geral) * 100 if total_geral > 0 else 0
                        data.append([
                            forma,
                            f"{total:,.2f}",
                            f"{participacao:.1f}%"
                        ])
                
                t = Table(data, colWidths=[doc.width*0.5, doc.width*0.25, doc.width*0.25])
                t.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    # Destaque para a forma de pagamento mais usada
                    ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#27AE60')),
                    ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
                ]))
                
                elements.append(t)
                elements.append(Spacer(1, 20))
            
            # Rodapé
            elements.append(Spacer(1, 20))
            elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#E0E0E0'), spaceBefore=10, spaceAfter=10))
            
            footer_text = (
                f"{config.get('nome_empresa', 'Sistema de Vendas')} • "
                f"{config.get('endereco', '')} • "
                f"Tel: {config.get('telefone', '')} • "
                f"{config.get('email', '')}"
            )
            
            elements.append(Paragraph(
                footer_text,
                style=ParagraphStyle(
                    name='Footer',
                    fontSize=7,
                    textColor=colors.HexColor('#7F8C8D'),
                    alignment=1,  # Center
                    spaceBefore=5,
                    spaceAfter=5
                )
            ))
            
            elements.append(Paragraph(
                f"Página <page> de <total>",
                style=ParagraphStyle(
                    name='PageNumber',
                    fontSize=7,
                    textColor=colors.HexColor('#95A5A6'),
                    alignment=2,  # Right
                    spaceBefore=5,
                    spaceAfter=5
                )
            ))
            
            # Gerar o PDF
            doc.build(elements, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            
            # Mostrar mensagem de sucesso
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Relatório gerado com sucesso: {filename}"),
                    bgcolor=ft.colors.GREEN
                )
            )
            
            # Abrir o arquivo
            os.startfile(filename)
            
        except Exception as error:
            print(f"Erro ao gerar relatório de vendas: {error}")
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Erro ao gerar relatório: {str(error)}"),
                    bgcolor=ft.colors.RED
                )
            )
            return  # Exit the function after handling the error

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
                    content=ft.Text(f"❌ Erro ao gerar relatório: {str(error)}"),
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
            elements.append(Spacer(1, 20))
            
            # Tabela de produtos
            data = [
                ['Código', 'Nome', 'Preço Custo', 'Preço Venda', 'Estoque', 'Mínimo', 'Vendas']
            ]
            
            # Adicionar linhas de dados
            for p in produtos:
                data.append([
                    p['codigo'],
                    p['nome'][:30] if p['nome'] else '',  # Limita o tamanho do nome para 30 caracteres
                    f"MT {p['preco_custo']:,.2f}",
                    f"MT {p['preco_venda']:,.2f}",
                    f"{int(p['estoque']):d}",
                    f"{int(p['estoque_minimo']):d}",
                    f"{int(p['quantidade_vendida']):d}"
                ])
            
            # Ajustar larguras das colunas (em polegadas)
            col_widths = [
                0.8 * inch,  # Código
                2.2 * inch,  # Nome (aumentado para 2.2)
                1.0 * inch,  # Preço Custo
                1.0 * inch,  # Preço Venda
                0.7 * inch,  # Estoque
                0.7 * inch,  # Mínimo
                0.7 * inch   # Vendas
            ]
            
            # Criar tabela com as novas larguras
            table = Table(data, colWidths=col_widths, repeatRows=1)
            
            # Estilo da tabela
            table.setStyle(TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),  # Azul escuro
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # Linhas de dados
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),  # Linhas mais suaves
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a237e')),     # Borda azul
                
                # Destaque para estoque abaixo do mínimo
                ('TEXTCOLOR', (4, 1), (4, -1), 
                    lambda r, c=4: colors.red if r < len(data) and r > 0 and 
                    int(data[r][c]) < int(data[r][5]) else colors.black),
                
                # Padding
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))
            
            elements.append(table)
            
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
            
            # Construir o documento
            doc.build(elements)
            
            # Mostrar mensagem de sucesso
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

    def gerar_relatorio_baixo_estoque(self, e):
        """Gera relatório de produtos com estoque abaixo do mínimo"""
        try:
            # Buscar produtos com estoque abaixo do mínimo
            produtos = self.db.fetchall("""
                SELECT 
                    p.codigo,
                    p.nome,
                    p.descricao,
                    p.preco_custo,
                    p.preco_venda,
                    p.estoque,
                    p.estoque_minimo,
                    c.nome as categoria
                FROM produtos p
                LEFT JOIN categorias c ON c.id = p.categoria_id
                WHERE p.ativo = 1 
                AND p.estoque <= p.estoque_minimo
                ORDER BY p.estoque ASC, p.nome
            """)

            if not produtos:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Nenhum produto com estoque baixo encontrado."),
                    bgcolor=ft.colors.GREEN
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            # Criar PDF
            filename = os.path.join(
                self.relatorios_dir, 
                f"baixo_estoque_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
            title = Paragraph("Relatório de Produtos com Estoque Baixo", title_style)
            elements.append(title)
            elements.append(Spacer(1, 20))
            
            # Data de geração
            elements.append(Paragraph(
                f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles['Italic']
            ))
            elements.append(Spacer(1, 20))
            
            # Tabela de produtos
            data = [
                ['Código', 'Produto', 'Categoria', 'Estoque', 'Mínimo', 'Status']
            ]
            
            # Adicionar linhas de dados
            for p in produtos:
                status = "CRÍTICO" if p['estoque'] <= 0 else "Alerta"
                data.append([
                    p['codigo'],
                    p['nome'],
                    p['categoria'] or 'Sem Categoria',
                    str(p['estoque']),
                    str(p['estoque_minimo']),
                    status
                ])
            
            # Estilo da tabela
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A148C')),  # Cabeçalho roxo
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            
            # Aplicar estilos condicionais
            for i, row in enumerate(data[1:], 1):  # Pular cabeçalho
                if row[5] == 'CRÍTICO':
                    table_style.add('TEXTCOLOR', (0, i), (-1, i), colors.red)
                    table_style.add('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold')
                elif row[5] == 'Alerta':
                    table_style.add('TEXTCOLOR', (0, i), (-1, i), colors.orange)
            
            # Criar tabela
            table = Table(data)
            table.setStyle(table_style)
            elements.append(table)
            
            # Rodapé
            elements.append(Spacer(1, 20))
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
            elements.append(Paragraph(
                f"Total de produtos com estoque baixo: {len(produtos)}",
                styles['Italic']
            ))
            
            # Gerar PDF
            doc.build(elements, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            
            # Mostrar mensagem de sucesso
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Relatório gerado com sucesso: {filename}"),
                bgcolor=ft.colors.GREEN
            )
            self.page.snack_bar.open = True
            self.page.update()
            
            # Abrir o arquivo
            os.startfile(filename)
            
        except Exception as error:
            print(f"Erro ao gerar relatório de estoque baixo: {error}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao gerar relatório: {str(error)}"),
                bgcolor=ft.colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()

    def gerar_relatorio_lucros(self, e):
        """Relatório de lucros por período"""
        try:
            if not self.validar_datas():
                return
                
            # Buscar configurações da empresa do arquivo config.json
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                # Configurações padrão se o arquivo não existir
                config = {
                    'nome_empresa': 'Minha Empresa',
                    'endereco': 'Endereço não configurado',
                    'telefone': '',
                    'email': '',
                    'cnpj': ''
                }
            
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
                            "Relatório de Produtos",
                            icon=ft.icons.INVENTORY,
                            on_click=self.gerar_relatorio_produtos,
                            style=ft.ButtonStyle(
                                bgcolor={"": ft.colors.GREEN},
                                color=ft.colors.WHITE,
                                padding=15
                            ),
                            tooltip="Gerar relatório de produtos"
                        ),
                        ft.ElevatedButton(
                            "Produtos com Estoque Baixo",
                            icon=ft.icons.WARNING_AMBER,
                            on_click=self.gerar_relatorio_baixo_estoque,
                            style=ft.ButtonStyle(
                                bgcolor={"": ft.colors.ORANGE_700},
                                color=ft.colors.WHITE,
                                padding=15
                            ),
                            tooltip="Ver produtos com estoque abaixo do mínimo"
                        )
                    ], spacing=10, wrap=True)
                ]),
                bgcolor=ft.colors.WHITE,
                padding=20,
                border_radius=10
            )
        ]) 