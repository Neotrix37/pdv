from datetime import datetime

def formatar_moeda(valor):
    return f"MT {valor:,.2f}"

def formatar_data(data_str):
    data = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
    return data.strftime('%d/%m/%Y %H:%M')

def calcular_troco(valor_total, valor_pago):
    return max(0, valor_pago - valor_total)
