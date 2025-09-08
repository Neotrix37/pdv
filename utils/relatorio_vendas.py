import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from datetime import datetime
import locale

class RelatorioVendas:
    def __init__(self, titulo="Relatório de Vendas", orientacao='landscape'):
        self.titulo = titulo
        self.orientacao = orientacao
        self.pagina = A4
        self.margens = (1*cm, 1*cm, 1*cm, 1*cm)  # esquerda, direita, cima, baixo
        self.estilos = getSampleStyleSheet()
        self.configurar_estilos()
        
    def configurar_estilos(self):
        """Configura os estilos para o relatório de vendas"""
        # Estilo para o título principal
        self.estilos.add(ParagraphStyle(
            name='Titulo',
            parent=self.estilos['Heading1'],
            fontSize=16,
            leading=22,
            alignment=1,  # centralizado
            spaceAfter=15,
            spaceBefore=10,
            textColor=colors.HexColor('#2C3E50'),
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para os cabeçalhos da tabela
        self.estilos.add(ParagraphStyle(
            name='Cabecalho',
            parent=self.estilos['Normal'],
            fontSize=9,
            leading=11,
            alignment=1,  # centralizado
            textColor=colors.white,
            fontName='Helvetica-Bold',
            spaceBefore=5,
            spaceAfter=5
        ))
        
        # Estilo para as células de dados
        self.estilos.add(ParagraphStyle(
            name='Dados',
            parent=self.estilos['Normal'],
            fontSize=8,
            leading=10,
            alignment=0,  # alinhado à esquerda
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica',
            spaceBefore=2,
            spaceAfter=2
        ))
        
        # Estilo para valores numéricos
        self.estilos.add(ParagraphStyle(
            name='Numerico',
            parent=self.estilos['Dados'],
            alignment=2,  # alinhado à direita
            fontName='Helvetica'
        ))
        
        # Estilo para datas
        self.estilos.add(ParagraphStyle(
            name='Data',
            parent=self.estilos['Dados'],
            alignment=1,  # centralizado
            fontSize=8,
            fontName='Helvetica'
        ))
        
        # Estilo para o rodapé
        self.estilos.add(ParagraphStyle(
            name='Rodape',
            parent=self.estilos['Italic'],
            fontSize=7,
            alignment=2,  # alinhado à direita
            textColor=colors.HexColor('#666666'),
            spaceBefore=10
        ))
        
    def formatar_itens(self, itens_str):
        """Formata a string de itens para exibição no relatório"""
        if not itens_str:
            return ""
            
        itens = []
        for item in itens_str.split(','):
            item = item.strip()
            if '(' in item and ')' in item:
                # Formato: Nome (Qtd x Preço = Total)
                nome, resto = item.split('(', 1)
                itens.append(f"• {nome.strip()}: {resto.strip(')')}")
            else:
                itens.append(f"• {item}")
                
        return '<br/>'.join(itens)
        
    def gerar_relatorio(self, dados, cabecalhos, caminho_arquivo, filtros=None):
        """Gera o relatório de vendas em PDF"""
        if self.orientacao == 'landscape':
            self.pagina = landscape(A4)
            largura_util = self.pagina[0] - self.margens[0] - self.margens[1]
        else:
            largura_util = self.pagina[0] - self.margens[0] - self.margens[1]
        
        # Configura o documento
        doc = SimpleDocTemplate(
            caminho_arquivo,
            pagesize=self.pagina,
            leftMargin=self.margens[0],
            rightMargin=self.margens[1],
            topMargin=self.margens[2],
            bottomMargin=self.margens[3]
        )
        
        # Lista de elementos do relatório
        elementos = []
        
        # Adiciona o título com destaque
        elementos.append(Paragraph(f"<u>{self.titulo}</u>", self.estilos['Titulo']))
        
        # Adiciona os filtros, se fornecidos
        if filtros:
            filtros_texto = []
            if 'periodo' in filtros and filtros['periodo']:
                filtros_texto.append(f"<b>Período:</b> {filtros['periodo']}")
            if 'vendedor' in filtros and filtros['vendedor']:
                filtros_texto.append(f"<b>Vendedor:</b> {filtros['vendedor']}")
            if 'cliente' in filtros and filtros['cliente']:
                filtros_texto.append(f"<b>Cliente:</b> {filtros['cliente']}")
            if 'categoria' in filtros and filtros['categoria']:
                filtros_texto.append(f"<b>Categoria:</b> {filtros['categoria']}")
                
            if filtros_texto:
                filtros_html = " | ".join(filtros_texto)
                elementos.append(Paragraph(filtros_html, self.estilos['Normal']))
                elementos.append(Spacer(1, 12))
        
        # Adiciona a data de geração no rodapé
        data_geracao = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        # Adiciona espaço antes da tabela
        elementos.append(Spacer(1, 15))
        
        # Adiciona a data de geração no rodapé do documento
        def add_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 7)
            canvas.setFillColor(colors.HexColor('#666666'))
            
            # Nome do sistema e número da página
            texto_rodape = f"Sistema PDV - Página {doc.page}"
            largura_texto = canvas.stringWidth(texto_rodape, 'Helvetica', 7)
            
            # Data de geração à esquerda
            canvas.drawString(2*cm, 1*cm, data_geracao)
            
            # Nome do sistema e número da página à direita
            canvas.drawRightString(doc.width + doc.leftMargin - 2*cm, 1*cm, texto_rodape)
            
            # Linha separadora
            canvas.setStrokeColor(colors.HexColor('#CCCCCC'))
            canvas.setLineWidth(0.5)
            canvas.line(2*cm, 1.3*cm, doc.width + doc.leftMargin - 2*cm, 1.3*cm)
            
            canvas.restoreState()
        
        # Adiciona o rodapé ao documento
        doc.build(elementos, onFirstPage=add_footer, onLaterPages=add_footer)
        return caminho_arquivo
        
        # Prepara os dados para a tabela
        dados_tabela = [cabecalhos]
        
        # Adiciona os dados formatados
        for linha in dados:
            linha_formatada = []
            
            for i, valor in enumerate(linha):
                # Formata itens da venda
                if 'itens' in cabecalhos[i].lower():
                    valor_formatado = self.formatar_itens(str(valor))
                    estilo = 'Dados'
                # Formata datas
                elif 'data' in cabecalhos[i].lower():
                    try:
                        if ' ' in str(valor):
                            data_obj = datetime.strptime(str(valor), '%Y-%m-%d %H:%M:%S')
                            valor_formatado = data_obj.strftime('%d/%m/%Y %H:%M')
                        else:
                            data_obj = datetime.strptime(str(valor), '%Y-%m-%d')
                            valor_formatado = data_obj.strftime('%d/%m/%Y')
                        estilo = 'Data'
                    except:
                        valor_formatado = str(valor)
                        estilo = 'Dados'
                # Formata valores monetários
                elif any(termo in cabecalhos[i].lower() for termo in ['total', 'valor', 'preço', 'preco', 'lucro', 'desconto']):
                    try:
                        valor_float = float(valor)
                        valor_formatado = f"MT {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        estilo = 'Numerico'
                    except:
                        valor_formatado = str(valor)
                        estilo = 'Dados'
                # Formata quantidades
                elif any(termo in cabecalhos[i].lower() for termo in ['quantidade', 'qtd', 'estoque']):
                    try:
                        if '.' in str(valor):
                            valor_float = float(valor)
                            valor_formatado = f"{valor_float:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        else:
                            valor_int = int(valor)
                            valor_formatado = f"{valor_int:,}".replace(",", ".")
                        estilo = 'Numerico'
                    except:
                        valor_formatado = str(valor)
                        estilo = 'Dados'
                else:
                    valor_formatado = str(valor)
                    estilo = 'Dados'
                
                # Adiciona o valor formatado à linha
            
            # Adiciona o valor formatado à linha
            linha_formatada.append(Paragraph(valor_formatado, self.estilos[estilo]))
        
        dados_tabela.append(linha_formatada)
    
    # Calcula a largura das colunas (proporcional para modo paisagem)
    num_colunas = len(cabecalhos)
    if self.orientacao == 'landscape':
        # Larguras personalizadas para modo paisagem
        largura_total = self.pagina[0] - self.margens[0] - self.margens[1] - 3*cm  # Margem extra para rolagem
                largura_encontrada = False
                
                # Procura por termos-chave no cabeçalho
                for termo, largura in larguras_padrao.items():
                    if termo in cabecalho_lower:
                        larguras_colunas.append(largura)
                        largura_encontrada = True
                        break
                
                # Se não encontrou um termo correspondente, usa largura padrão
                if not largura_encontrada:
                    larguras_colunas.append(3.0*cm)  # Largura padrão
            
            # Ajusta as larguras para caber na página
            largura_atual = sum(larguras_colunas)
            if largura_atual > largura_total:
                # Reduz proporcionalmente as colunas que são muito largas
                fator_reducao = largura_total / largura_atual
                larguras_colunas = [w * fator_reducao for w in larguras_colunas]
        else:
            # Modo retrato (menos comum para relatórios de vendas)
            largura_coluna = (self.pagina[0] - self.margens[0] - self.margens[1] - 2*cm) / num_colunas
            larguras_colunas = [largura_coluna] * num_colunas
        
        # Cria a tabela com espaçamento entre linhas
        tabela = Table(dados_tabela, colWidths=larguras_colunas, repeatRows=1, hAlign='CENTER')
        
        # Aplica estilos à tabela
        estilo_tabela = TableStyle([
            # Estilo do cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),  # Cor de fundo do cabeçalho
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Cor do texto do cabeçalho
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Alinhamento do cabeçalho
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Fonte do cabeçalho
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Tamanho da fonte do cabeçalho
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Espaçamento inferior do cabeçalho
            ('TOPPADDING', (0, 0), (-1, 0), 6),  # Espaçamento superior do cabeçalho
            
            # Estilo das células de dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Fonte dos dados
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Tamanho da fonte dos dados
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),  # Linhas de grade mais suaves
            
            # Linhas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            
            # Espaçamento interno
            ('LEFTPADDING', (0, 0), (-1, -1), 5),  # Espaçamento interno esquerdo
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),  # Espaçamento interno direito
            ('TOPPADDING', (0, 1), (-1, -1), 6),  # Espaçamento superior
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Espaçamento inferior
            
            # Quebra de linha automática e alinhamento
            ('WORDWRAP', (0, 0), (-1, -1), True),  # Quebra de linha automática
            
            # Alinhamento de colunas específicas
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Primeira coluna centralizada
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),  # Última coluna à direita
        ])
        
        # Adiciona alinhamento para colunas numéricas
        for i, cabecalho in enumerate(cabecalhos):
            cabecalho_lower = cabecalho.lower()
            if any(termo in cabecalho_lower for termo in ['total', 'valor', 'preço', 'preco', 'lucro', 'desconto', 'quantidade', 'estoque']):
                estilo_tabela.add('ALIGN', (i, 1), (i, -1), 'RIGHT')
            elif 'data' in cabecalho_lower:
                estilo_tabela.add('ALIGN', (i, 1), (i, -1), 'CENTER')
        
        # Aplica o estilo à tabela
        tabela.setStyle(estilo_tabela)
        
        # Adiciona a tabela aos elementos
        elementos.append(tabela)
        
        # Adiciona o totalizador, se houver
        if 'total' in [h.lower() for h in cabecalhos]:
            total_col = [h.lower() for h in cabecalhos].index('total') if 'total' in [h.lower() for h in cabecalhos] else -1
            if total_col >= 0:
                try:
                    total_geral = sum(float(str(linha[total_col]).replace('MT', '').replace('.', '').replace(',', '.').strip()) 
                                    for linha in dados if len(linha) > total_col and str(linha[total_col]).strip())
                    
                    # Formata o total geral
                    total_formatado = f"MT {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    
                    # Adiciona o totalizador
                    elementos.append(Spacer(1, 10))
                    elementos.append(Paragraph(
                        f"<b>Total Geral:</b> {total_formatado}", 
                        self.estilos['Normal']
                    ))
                except:
                    pass  # Ignora erros no cálculo do total
        
        # O PDF já foi gerado com o rodapé personalizado
        return caminho_arquivo

def gerar_relatorio_vendas(dados, cabecalhos, caminho_arquivo, titulo="Relatório de Vendas", 
                          orientacao='landscape', filtros=None):
    """
    Função auxiliar para gerar relatório de vendas
    
    Args:
        dados: Lista de listas com os dados das vendas
        cabecalhos: Lista com os nomes das colunas
        caminho_arquivo: Caminho onde o arquivo será salvo
        titulo: Título do relatório
        orientacao: 'portrait' ou 'landscape'
        filtros: Dicionário com filtros aplicados (opcional)
    """
    relatorio = RelatorioVendas(titulo, orientacao)
    return relatorio.gerar_relatorio(dados, cabecalhos, caminho_arquivo, filtros)

# Exemplo de uso:
if __name__ == "__main__":
    # Dados de exemplo
    cabecalhos = ["Data", "Nº Venda", "Cliente", "Itens", "Quantidade", "Total", "Forma Pagamento"]
    
    dados = [
        ["2023-10-15 14:30:00", "1001", "Cliente A", "Produto 1 (2 x 10,00 = 20,00), Produto 2 (1 x 15,50 = 15,50)", 3, 35.5, "Dinheiro"],
        ["2023-10-15 15:45:00", "1002", "Cliente B", "Produto 3 (5 x 8,00 = 40,00)", 5, 40.0, "Cartão"],
        ["2023-10-16 10:15:00", "1003", "Cliente C", "Produto 1 (1 x 10,00 = 10,00), Produto 4 (2 x 12,50 = 25,00)", 3, 35.0, "Transferência"],
    ]
    
    # Filtros aplicados
    filtros = {
        'periodo': '15/10/2023 a 16/10/2023',
        'vendedor': 'João Silva'
    }
    
    # Gera o relatório
    caminho = os.path.join("relatorios", "exemplo_relatorio_vendas.pdf")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    
    gerar_relatorio_vendas(
        dados=dados,
        cabecalhos=cabecalhos,
        caminho_arquivo=caminho,
        titulo="Relatório de Vendas - Exemplo",
        orientacao='landscape',
        filtros=filtros
    )
    
    print(f"Relatório gerado com sucesso em: {os.path.abspath(caminho)}")
