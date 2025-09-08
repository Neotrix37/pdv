import flet as ft
import time
from database.database import Database
from views.dashboard_view import DashboardView

def testar_reset_dashboard():
    print("\n=== TESTE DE RESET DO DASHBOARD ===\n")
    
    # Inicializar banco de dados
    print("Inicializando banco de dados...")
    db = Database()
    print("Banco de dados inicializado com sucesso!")
    
    # Simular página e dados
    # O objeto Page do Flet requer conn e session_id
    # Vamos criar um objeto simulado que tenha os mesmos atributos
    class MockPage:
        def __init__(self):
            self.data = {}
            self.controls = []
            self.views = []
            self.session = MockSession()
        
        def update(self):
            pass
            
    class MockSession:
        def __init__(self):
            self.data = {}
            
        def set(self, key, value):
            self.data[key] = value
            
        def get(self, key):
            return self.data.get(key)
    
    page = MockPage()
    page.data = {}
    
    # Buscar um usuário não-admin para teste
    usuario_row = db.fetchone("SELECT * FROM usuarios WHERE is_admin = 0 LIMIT 1")
    if not usuario_row:
        print("❌ Erro: Nenhum usuário não-admin encontrado para teste")
        return False
    
    # Converter o objeto sqlite3.Row para um dicionário
    usuario = {}
    for key in usuario_row.keys():
        usuario[key] = usuario_row[key]
    
    print(f"Usuário de teste: {usuario['nome']} (ID: {usuario['id']})")
    
    # Criar instância do dashboard
    print("Criando instância do dashboard...")
    try:
        dashboard = DashboardView(page, usuario)
        print("Instância do dashboard criada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar instância do dashboard: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False
    
    # Verificar valores iniciais
    print("\n1. Valores iniciais do dashboard:")
    dashboard.atualizar_valores()
    print(f"   - Vendas mês: {dashboard.vendas_mes.value}")
    print(f"   - Vendas dia: {dashboard.vendas_dia.value}")
    print(f"   - Lucro mês: {dashboard.lucro_mes.value}")
    print(f"   - Lucro dia: {dashboard.lucro_dia.value}")
    print(f"   - Valor estoque: {dashboard.valor_estoque.value}")
    print(f"   - Valor potencial: {dashboard.valor_potencial.value}")
    
    # Simular fechamento de caixa (definir flag reset_dashboard_values)
    print("\n2. Simulando fechamento de caixa (definindo flag reset_dashboard_values = True)")
    page.data['reset_dashboard_values'] = True
    
    # Chamar did_mount para processar a flag
    print("\n3. Chamando did_mount para processar a flag:")
    dashboard.did_mount()
    
    # Verificar se os valores foram resetados
    print("\n4. Verificando valores após reset:")
    print(f"   - Vendas mês: {dashboard.vendas_mes.value}")
    print(f"   - Vendas dia: {dashboard.vendas_dia.value}")
    print(f"   - Lucro mês: {dashboard.lucro_mes.value}")
    print(f"   - Lucro dia: {dashboard.lucro_dia.value}")
    print(f"   - Valor estoque: {dashboard.valor_estoque.value}")
    print(f"   - Valor potencial: {dashboard.valor_potencial.value}")
    
    # Verificar se os valores de vendas e lucros foram zerados
    vendas_mes = float(dashboard.vendas_mes.value.replace('MT ', ''))
    vendas_dia = float(dashboard.vendas_dia.value.replace('MT ', ''))
    lucro_mes = float(dashboard.lucro_mes.value.replace('MT ', ''))
    lucro_dia = float(dashboard.lucro_dia.value.replace('MT ', ''))
    
    # Verificar se os valores de estoque foram mantidos
    valor_estoque = float(dashboard.valor_estoque.value.replace('MT ', ''))
    valor_potencial = float(dashboard.valor_potencial.value.replace('MT ', ''))
    
    # Verificar resultados
    if vendas_mes == 0.0 and vendas_dia == 0.0 and lucro_mes == 0.0 and lucro_dia == 0.0:
        print("\n✅ SUCESSO: Valores de vendas e lucros foram zerados corretamente")
    else:
        print("\n❌ ERRO: Valores de vendas e lucros NÃO foram zerados")
        print(f"   - Vendas mês: {vendas_mes}")
        print(f"   - Vendas dia: {vendas_dia}")
        print(f"   - Lucro mês: {lucro_mes}")
        print(f"   - Lucro dia: {lucro_dia}")
    
    if valor_estoque > 0 and valor_potencial > 0:
        print("\n✅ SUCESSO: Valores de estoque foram mantidos corretamente")
    else:
        print("\n❌ ERRO: Valores de estoque foram zerados incorretamente")
        print(f"   - Valor estoque: {valor_estoque}")
        print(f"   - Valor potencial: {valor_potencial}")
    
    # Verificar se a flag foi removida
    if 'reset_dashboard_values' not in page.data:
        print("\n✅ SUCESSO: Flag reset_dashboard_values foi removida corretamente")
    else:
        print("\n❌ ERRO: Flag reset_dashboard_values NÃO foi removida")
    
    print("\n=== FIM DO TESTE ===\n")
    return True

if __name__ == "__main__":
    print("Iniciando teste de reset do dashboard...")
    try:
        testar_reset_dashboard()
        print("Teste concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ ERRO durante a execução do teste: {str(e)}")
        import traceback
        print(traceback.format_exc())