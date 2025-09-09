import platform
import os
from datetime import datetime

class RongtaPrinter:
    """Versão web da RongtaPrinter - sem dependências Windows"""
    
    def __init__(self):
        self.printer = None
        self.status = None
        self.sistema = platform.system().lower()
        self.marcas_suportadas = [
            "RONGTA", "ELGIN", "BEMATECH", "SWEDA", 
            "DARUMA", "EPSON", "ZEBRA", "CITIZEN"
        ]
        self.web_mode = True

    def is_connected(self):
        """Verifica se a impressora está conectada"""
        # No modo web, sempre retorna False (impressão não disponível)
        return False

    def list_usb_printers(self):
        """Lista todas as impressoras térmicas conectadas via USB"""
        print("Modo web: Impressoras USB não disponíveis")
        return []

    def list_bluetooth_printers(self):
        """Lista todas as impressoras Bluetooth disponíveis"""
        print("Modo web: Impressoras Bluetooth não disponíveis")
        return []

    def connect_usb(self, printer_name):
        """Conecta à impressora USB"""
        print(f"Modo web: Conexão USB não disponível para {printer_name}")
        return False

    def connect_bluetooth(self, printer_name):
        """Conecta à impressora Bluetooth"""
        print(f"Modo web: Conexão Bluetooth não disponível para {printer_name}")
        return False

    def print_test(self):
        """Imprime página de teste"""
        print("Modo web: Impressão de teste não disponível")
        return False

    def print_receipt(self, data):
        """Imprime recibo/factura"""
        try:
            # No modo web, apenas simula a impressão
            print("=== SIMULAÇÃO DE IMPRESSÃO ===")
            content = self._format_receipt(data)
            print(content)
            print("=== FIM DA SIMULAÇÃO ===")
            return True
        except Exception as e:
            print(f"Erro na simulação de impressão: {e}")
            return False

    def _format_receipt(self, data):
        """Formata o recibo para impressão"""
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
                f"Venda #: {data.get('numero', 'N/A')}",
                f"Data: {data.get('data', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}",
                f"Operador: {data.get('operador', 'N/A')}",
                "-" * 40
            ])
            
            # Cabeçalho dos itens
            lines.append(f"{'Produto':<20}{'Qtd':>5}{'Preço':>8}{'Total':>7}")
            lines.append("-" * 40)
            
            # Itens
            for item in data.get('items', []):
                nome = str(item.get('nome', ''))[:20]
                qtd = item.get('qtd', 0)
                preco = item.get('preco', 0)
                total = item.get('total', 0)
                lines.append(
                    f"{nome:<20}{qtd:>5}"
                    f"{preco:>8.2f}{total:>7.2f}"
                )
            
            # Totais
            lines.extend([
                "-" * 40,
                f"{'Total:':<33}{data.get('total', 0):>7.2f}",
                f"Forma de Pagamento: {data.get('pagamento', 'N/A')}",
                f"Valor Pago: {data.get('valor_pago', 0):.2f}",
                f"Troco: {data.get('troco', 0):.2f}",
                "",
                "=" * 40,
                self._center_text(data.get('rodape', ''), 40),
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

    def disconnect(self):
        """Desconecta a impressora"""
        try:
            self.printer = None
            self.status = None
            print("Modo web: Impressora desconectada")
        except Exception as e:
            print(f"Erro ao desconectar: {e}")
