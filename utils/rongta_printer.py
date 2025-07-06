import platform
import os
import win32print
import win32ui
from datetime import datetime

class RongtaPrinter:
    def __init__(self):
        self.printer = None
        self.status = None
        self.sistema = platform.system().lower()
        self.marcas_suportadas = [
            "RONGTA", "ELGIN", "BEMATECH", "SWEDA", 
            "DARUMA", "EPSON", "ZEBRA", "CITIZEN"
        ]

    def is_connected(self):
        """Verifica se a impressora está conectada"""
        return self.printer is not None and self.status == "connected"

    def list_usb_printers(self):
        """Lista todas as impressoras térmicas conectadas via USB"""
        try:
            print("Iniciando busca de impressoras USB...")
            printers = []
            for printer in win32print.EnumPrinters(2):  # 2 = PRINTER_ENUM_LOCAL
                printer_name = printer[2]
                print(f"Encontrada impressora: {printer_name}")
                
                # Verifica se é uma impressora térmica suportada
                if any(marca.lower() in printer_name.lower() for marca in self.marcas_suportadas):
                    print(f"Impressora suportada encontrada: {printer_name}")
                    printers.append({
                        'name': printer_name,
                        'port': printer[1],
                        'type': 'USB',
                        'driver': printer[3] if len(printer) > 3 else None
                    })
                else:
                    print(f"Impressora não suportada: {printer_name}")
            
            print(f"Total de impressoras USB suportadas encontradas: {len(printers)}")
            return printers
        except Exception as e:
            print(f"Erro ao listar impressoras USB: {e}")
            import traceback
            print(f"Stacktrace: {traceback.format_exc()}")
            return []

    def list_bluetooth_printers(self):
        """Lista todas as impressoras Bluetooth disponíveis"""
        try:
            print("Iniciando busca de impressoras Bluetooth...")
            printers = []
            for printer in win32print.EnumPrinters(2):  # 2 = PRINTER_ENUM_LOCAL
                printer_name = printer[2]
                print(f"Encontrada impressora: {printer_name}")
                
                # Verifica se é uma impressora Bluetooth suportada
                if "BLUETOOTH" in printer_name.upper():
                    if any(marca.lower() in printer_name.lower() for marca in self.marcas_suportadas):
                        print(f"Impressora Bluetooth suportada encontrada: {printer_name}")
                        printers.append({
                            'name': printer_name,
                            'port': printer[1],
                            'type': 'BLUETOOTH',
                            'driver': printer[3] if len(printer) > 3 else None
                        })
                    else:
                        print(f"Impressora Bluetooth não suportada: {printer_name}")
            
            print(f"Total de impressoras Bluetooth suportadas encontradas: {len(printers)}")
            return printers
        except Exception as e:
            print(f"Erro ao listar impressoras Bluetooth: {e}")
            import traceback
            print(f"Stacktrace: {traceback.format_exc()}")
            return []

    def connect_usb(self, printer_name):
        """Conecta à impressora USB"""
        try:
            # Verifica se a impressora existe
            printer = win32print.OpenPrinter(printer_name)
            if printer:
                win32print.ClosePrinter(printer)
                self.printer = printer_name
                self.status = "connected"
                return True
            return False
        except Exception as e:
            print(f"Erro ao conectar à impressora USB: {e}")
            return False

    def connect_bluetooth(self, printer_name):
        """Conecta à impressora Bluetooth"""
        try:
            # Verifica se a impressora existe
            printer = win32print.OpenPrinter(printer_name)
            if printer:
                win32print.ClosePrinter(printer)
                self.printer = printer_name
                self.status = "connected"
                return True
            return False
        except Exception as e:
            print(f"Erro ao conectar à impressora Bluetooth: {e}")
            return False

    def print_test(self):
        """Imprime página de teste"""
        try:
            if not self.is_connected():
                return False

            printer = win32print.OpenPrinter(self.printer)
            try:
                # Formata o texto de teste
                test_text = "\n".join([
                    "=" * 40,
                    "TESTE DE IMPRESSÃO",
                    "=" * 40,
                    f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    f"Impressora: {self.printer}",
                    "=" * 40,
                    "\n" * 3  # Espaço para corte
                ]).encode('cp850', 'replace')

                # Inicia o job de impressão
                job = win32print.StartDocPrinter(printer, 1, ("Test Page", None, "RAW"))
                try:
                    win32print.StartPagePrinter(printer)
                    win32print.WritePrinter(printer, test_text)
                    win32print.EndPagePrinter(printer)
                finally:
                    win32print.EndDocPrinter(printer)
            finally:
                win32print.ClosePrinter(printer)
            return True
        except Exception as e:
            print(f"Erro ao imprimir teste: {e}")
            return False

    def print_receipt(self, data):
        """Imprime recibo/factura"""
        try:
            if not self.is_connected():
                raise Exception("Impressora não configurada")

            printer = win32print.OpenPrinter(self.printer)
            try:
                # Formata o conteúdo do recibo
                content = self._format_receipt(data)
                
                # Inicia o job de impressão
                job = win32print.StartDocPrinter(printer, 1, ("Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(printer)
                    win32print.WritePrinter(printer, content.encode('cp850', 'replace'))
                    win32print.EndPagePrinter(printer)
                finally:
                    win32print.EndDocPrinter(printer)
            finally:
                win32print.ClosePrinter(printer)
            
            return True
        except Exception as e:
            print(f"Erro na impressão: {e}")
            return False

    def _format_receipt(self, data):
        """Formata o recibo para impressão"""
        try:
            lines = []
            
            # Cabeçalho
            lines.extend([
                "=" * 40,
                self._center_text(data['empresa'], 40),
                self._center_text(data['endereco'], 40) if data.get('endereco') else "",
                self._center_text(f"Tel: {data['telefone']}", 40) if data.get('telefone') else "",
                self._center_text(f"NUIT: {data['nuit']}", 40) if data.get('nuit') else "",
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
                nome = item.get('nome', '')[:20]
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
        return text.center(width)

    def disconnect(self):
        """Desconecta a impressora"""
        try:
            self.printer = None
            self.status = None
        except Exception as e:
            print(f"Erro ao desconectar: {e}") 