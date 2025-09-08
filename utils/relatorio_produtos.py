import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from datetime import datetime
import locale

class RelatorioProdutos:
    def __init__(self, titulo="Relatório de Produtos", orientacao='portrait'):
        self.titulo = titulo
        self.orientacao = orientacao
        self.pagina = A4
        self.margens = (1*cm, 1*cm, 1*cm, 1*cm)  # esquerda, direita, cima, baixo
        self.estilos = getSampleStyleSheet()
        self.configurar_estilos()
        
    def configurar_estilos(self):
        """Configura os estilos para o relatório"""
        # Estilo para o título principal
        self.estilos.add(ParagraphStyle(
            name='Titulo',
            parent=self.estilos['Heading1'],
            fontSize=14,
            leading=20,
            alignment=1,  # centralizado
            spaceAfter=20,
            textColor=colors.HexColor('#2C3E50')
        ))
        
        # Estilo para os cabeçalhos da tabela
        self.estilos.add(ParagraphStyle(
            name='Cabecalho',
            parent=self.estilos['Normal'],
            fontSize=9,
            leading=11,
            alignment=1,  # centralizado
            textColor=colors.white,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para as células de dados
        self.estilos.add(ParagraphStyle(
            name='Dados',
            parent=self.estilos['Normal'],
            fontSize=8,
            leading=10,
            alignment=0,  # alinhado à esquerda
            textColor=colors.black,
            fontName='Helvetica'
        ))
        
        # Estilo para valores numéricos
        self.estilos.add(ParagraphStyle(
            name='Numerico',
            parent=self.estilos['Dados'],
            alignment=2,  # alinhado à direita
        ))
        
    def gerar_relatorio(self, dados, cabecalhos, caminho_arquivo):
        """Gera o relatório de produtos em PDF"""
        if self.orientacao == 'paisagem':
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
        
        # Adiciona o título
        elementos.append(Paragraph(self.titulo, self.estilos['Titulo']))
        
        # Adiciona a data de geração
        data_geracao = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elementos.append(Paragraph(data_geracao, self.estilos['Italic']))
        elementos.append(Spacer(1, 20))
        
        # Prepara os dados para a tabela
        dados_tabela = [cabecalhos]
        
        # Adiciona os dados formatados
        for linha in dados:
            linha_formatada = []
            for i, valor in enumerate(linha):
                # Formata números com separadores de milhar e 2 casas decimais
                if isinstance(valor, (int, float)) and i > 0:  # Assumindo que a primeira coluna não é numérica
                    try:
                        valor = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        estilo = 'Numerico'
                    except:
                        estilo = 'Dados'
                else:
                    estilo = 'Dados'
                
                # Quebra o texto em várias linhas se for muito longo
                if isinstance(valor, str) and len(valor) > 30:
                    partes = [valor[i:i+30] for i in range(0, len(valor), 30)]
                    valor = '<br/>'.join(partes)
                
                linha_formatada.append(Paragraph(str(valor), self.estilos[estilo]))
            
            dados_tabela.append(linha_formatada)
        
        # Calcula a largura das colunas
        num_colunas = len(cabecalhos)
        if self.orientacao == 'paisagem':
            largura_coluna = (largura_util - 2*cm) / num_colunas
            larguras_colunas = [largura_coluna] * num_colunas
        else:
            # Larguras personalizadas para modo retrato
            larguras_colunas = [
                1.5*cm,  # Código
                3.5*cm,  # Nome
                3.0*cm,  # Descrição
                2.0*cm,  # Preço Custo
                2.0*cm,  # Preço Venda
                1.5*cm,  # Estoque
                1.5*cm,  # Estoque Mínimo
                2.0*cm   # Categoria
            ]
            # Ajusta se tiver mais ou menos colunas
            if num_colunas < len(larguras_colunas):
                larguras_colunas = larguras_colunas[:num_colunas]
            elif num_colunas > len(larguras_colunas):
                largura_adicional = (num_colunas - len(larguras_colunas)) * 2.0*cm
                larguras_colunas.extend([2.0*cm] * (num_colunas - len(larguras_colunas)))
        
        # Cria a tabela
        tabela = Table(dados_tabela, colWidths=larguras_colunas, repeatRows=1)
        
        # Aplica estilos à tabela
        estilo_tabela = TableStyle([
            # Estilo do cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),  # Cor de fundo do cabeçalho
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Cor do texto do cabeçalho
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Alinhamento do cabeçalho
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Fonte do cabeçalho
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Tamanho da fonte do cabeçalho
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),  # Espaçamento inferior do cabeçalho
            
            # Estilo das células de dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Fonte dos dados
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Tamanho da fonte dos dados
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alinhamento vertical
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Alinhamento horizontal padrão
            
            # Alinhamento para colunas numéricas
            ('ALIGN', (3, 1), (5, -1), 'RIGHT'),  # Colunas de preço e estoque alinhadas à direita
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),  # Linhas de grade
            
            # Linhas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Espaçamento interno
            ('PADDING', (0, 0), (-1, -1), 4),  # Espaçamento interno das células
            
            # Quebra de linha automática
            ('WORDWRAP', (0, 0), (-1, -1), True),  # Quebra de linha automática
        ])
        
        # Aplica o estilo à tabela
        tabela.setStyle(estilo_tabela)
        
        # Adiciona a tabela aos elementos
        elementos.append(tabela)
        
        # Gera o PDF
        doc.build(elementos)
        
        return caminho_arquivo

def gerar_relatorio_produtos(dados, cabecalhos, caminho_arquivo, titulo="Relatório de Produtos", orientacao='portrait'):
    """Função auxiliar para gerar relatório de produtos"""
    relatorio = RelatorioProdutos(titulo, orientacao)
    return relatorio.gerar_relatorio(dados, cabecalhos, caminho_arquivo)

# Exemplo de uso:
if __name__ == "__main__":
    # Dados de exemplo
    cabecalhos = ["Código", "Nome", "Descrição", "Preço Custo", "Preço Venda", "Estoque", "Estoque Mínimo"]
    
    dados = [
        ["PROD001", "Produto 1", "Descrição do produto 1 com texto mais longo para teste de quebra de linha", 10.5, 25.9, 100, 20],
        ["PROD002", "Produto 2", "Descrição 2", 15.75, 32.5, 50, 15],
        ["PROD003", "Produto 3", "Outra descrição com texto mais longo para testar a quebra de linha automática no relatório", 8.2, 19.9, 75, 25],
    ]
    
    # Gera o relatório
    caminho = os.path.join("relatorios", "exemplo_relatorio_produtos.pdf")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    
    gerar_relatorio_produtos(
        dados=dados,
        cabecalhos=cabecalhos,
        caminho_arquivo=caminho,
        titulo="Relatório de Produtos - Exemplo",
        orientacao='portrait'  # ou 'paisagem' para relatórios mais largos
    )
    
    print(f"Relatório gerado com sucesso em: {os.path.abspath(caminho)}")
