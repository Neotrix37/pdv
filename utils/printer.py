import platform
import os
import win32print
import win32ui
from datetime import datetime

class PrinterManager:
    def __init__(self):
        self.sistema = platform.system().lower()
        
    def get_printer_list(self):
        """Retorna lista de impressoras disponíveis"""
        try:
            if self.sistema == "windows":
                printers = [printer[2] for printer in win32print.EnumPrinters(2)]
            else:
                # Para Linux/ChromeOS
                import subprocess
                output = subprocess.check_output(['lpstat', '-p']).decode()
                printers = [line.split()[1] for line in output.split('\n') if line]
            return printers
        except Exception as e:
            print(f"Erro ao listar impressoras: {e}")
            return []

    def print_document(self, printer_name, data):
        """Imprime documento na impressora especificada"""
        try:
            if self.sistema == "windows":
                import win32print
                import win32ui
                # Código específico para Windows
                # ...
            else:
                # Para Linux/ChromeOS usando CUPS
                import cups
                conn = cups.Connection()
                conn.printFile(printer_name, data, "Documento", {})
            return True
        except Exception as e:
            print(f"Erro ao imprimir: {e}")
            return False 

class RongtaPrinter:
    def __init__(self):
        self.printer_name = None
        self.status = None

    def connect_usb(self, printer_name):
        """Conecta à impressora USB"""
        try:
            self.printer_name = printer_name
            self.status = "Conectado"
            return True
        except Exception as e:
            print(f"Erro ao conectar impressora: {e}")
            self.status = "Erro"
            return False

    def print_test(self):
        """Imprime página de teste"""
        try:
            if not self.printer_name:
                raise Exception("Impressora não conectada")

            printer = win32print.OpenPrinter(self.printer_name)
            try:
                test_text = "\n".join([
                    "=== TESTE DE IMPRESSÃO ===",
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Impressora funcionando!",
                    "======================="
                ])
                job = win32print.StartDocPrinter(printer, 1, ("Test", None, "RAW"))
                try:
                    win32print.StartPagePrinter(printer)
                    win32print.WritePrinter(printer, test_text.encode('utf-8'))
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
        """Imprime recibo de venda"""
        try:
            if not self.printer_name:
                raise Exception("Impressora não conectada")

            # Formatar o recibo
            receipt_text = self._format_receipt(data)

            # Imprimir
            printer = win32print.OpenPrinter(self.printer_name)
            try:
                job = win32print.StartDocPrinter(printer, 1, ("Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(printer)
                    win32print.WritePrinter(printer, receipt_text.encode('utf-8'))
                    win32print.EndPagePrinter(printer)
                finally:
                    win32print.EndDocPrinter(printer)
            finally:
                win32print.ClosePrinter(printer)
            return True
        except Exception as e:
            print(f"Erro ao imprimir recibo: {e}")
            return False

    def _format_receipt(self, data):
        """Formata o texto do recibo"""
        try:
            lines = []
            
            # Cabeçalho
            lines.extend([
                "=" * 40,
                self._center_text(data['empresa'], 40),
                self._center_text(data['endereco'], 40) if data['endereco'] else "",
                self._center_text(f"Tel: {data['telefone']}", 40) if data['telefone'] else "",
                self._center_text(f"NUIT: {data['nuit']}", 40) if data['nuit'] else "",
                "=" * 40,
                "",
                f"Venda #: {data['venda_id']}",
                f"Data: {data['data']}",
                f"Vendedor: {data['vendedor']}",
                "-" * 40
            ])
            
            # Cabeçalho dos itens
            lines.append(f"{'Produto':<20}{'Qtd':>5}{'Preço':>8}{'Total':>7}")
            lines.append("-" * 40)
            
            # Itens
            for item in data['itens']:
                nome = item['produto'][:20]
                lines.append(
                    f"{nome:<20}{item['quantidade']:>5}"
                    f"{item['preco_unitario']:>8.2f}{item['subtotal']:>7.2f}"
                )
            
            # Totais
            lines.extend([
                "-" * 40,
                f"{'Total:':<33}{data['total']:>7.2f}",
                f"Forma de Pagamento: {data['forma_pagamento']}",
                "",
                "=" * 40,
                self._center_text(data['rodape'], 40) if data['rodape'] else "",
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

    @staticmethod
    def get_printers():
        """Retorna lista de impressoras instaladas"""
        try:
            printers = []
            for printer in win32print.EnumPrinters(2):
                printers.append({
                    'name': printer[2],
                    'port': printer[1]
                })
            return printers
        except Exception as e:
            print(f"Erro ao listar impressoras: {e}")
            return [] 