import platform
import os
from datetime import datetime

class PrinterManager:
    """Versão web do PrinterManager - sem dependências Windows"""
    
    def __init__(self):
        self.sistema = platform.system().lower()
        self.web_mode = True
        
    def get_printer_list(self):
        """Retorna lista de impressoras disponíveis"""
        print("Modo web: Impressoras não disponíveis")
        return []

    def print_document(self, printer_name, data):
        """Imprime documento na impressora especificada"""
        print(f"Modo web: Simulando impressão em {printer_name}")
        print(f"Dados: {data}")
        return True

class RongtaPrinter:
    """Versão web da RongtaPrinter - sem dependências Windows"""
    
    def __init__(self):
        self.printer_name = None
        self.status = None
        self.web_mode = True

    def connect_usb(self, printer_name):
        """Conecta à impressora USB"""
        print(f"Modo web: Simulando conexão USB com {printer_name}")
        self.printer_name = printer_name
        self.status = "Simulado"
        return False  # Sempre falso no modo web

    def print_test(self):
        """Imprime página de teste"""
        print("=== SIMULAÇÃO DE TESTE DE IMPRESSÃO ===")
        test_text = "\n".join([
            "=== TESTE DE IMPRESSÃO ===",
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Impressora funcionando!",
            "======================="
        ])
        print(test_text)
        print("=== FIM DA SIMULAÇÃO ===")
        return True

    def print_receipt(self, data):
        """Imprime recibo de venda"""
        try:
            print("=== SIMULAÇÃO DE IMPRESSÃO DE RECIBO ===")
            receipt_text = self._format_receipt(data)
            print(receipt_text)
            print("=== FIM DA SIMULAÇÃO ===")
            return True
        except Exception as e:
            print(f"Erro na simulação de impressão: {e}")
            return False

    def _format_receipt(self, data):
        """Formata o texto do recibo"""
        try:
            lines = []
            
            # Cabeçalho
            lines.extend([
                "=" * 40,
                self._center_text(data.get('empresa', 'Empresa'), 40),
                self._center_text(data.get('endereco', ''), 40) if data.get('endereco') else "",
                self._center_text(f"Tel: {data.get('telefone', '')}", 40) if data.get('telefone') else "",
                self._center_text(f"NUIT: {data.get('nuit', '')}", 40) if data.get('nuit') else "",
                "=" * 40,
                "",
                f"Venda #: {data.get('venda_id', 'N/A')}",
                f"Data: {data.get('data', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}",
                f"Vendedor: {data.get('vendedor', 'N/A')}",
                "-" * 40
            ])
            
            # Cabeçalho dos itens
            lines.append(f"{'Produto':<20}{'Qtd':>5}{'Preço':>8}{'Total':>7}")
            lines.append("-" * 40)
            
            # Itens
            for item in data.get('itens', []):
                nome = str(item.get('produto', ''))[:20]
                quantidade = item.get('quantidade', 0)
                preco = item.get('preco_unitario', 0)
                subtotal = item.get('subtotal', 0)
                lines.append(
                    f"{nome:<20}{quantidade:>5}"
                    f"{preco:>8.2f}{subtotal:>7.2f}"
                )
            
            # Totais
            lines.extend([
                "-" * 40,
                f"{'Total:':<33}{data.get('total', 0):>7.2f}",
                f"Forma de Pagamento: {data.get('forma_pagamento', 'N/A')}",
                "",
                "=" * 40,
                self._center_text(data.get('rodape', ''), 40) if data.get('rodape') else "",
                "=" * 40,
                "\n" * 5  # Espaço para corte
            ])
            
            return "\n".join(line for line in lines if line is not None)
        except Exception as e:
            print(f"Erro ao formatar recibo: {e}")
            raise

    def _center_text(self, text, width):
        """Centraliza o texto em uma largura específica"""
        if not text:
            return ""
        return str(text).center(width)

    @staticmethod
    def get_printers():
        """Retorna lista de impressoras instaladas"""
        print("Modo web: Lista de impressoras não disponível")
        return []
