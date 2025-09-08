import re

def fix_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir quebras de linha
    content = content.replace('\r\n', '\n')
    
    # Corrigir strings triplas não fechadas
    triple_single = content.count("'''")
    triple_double = content.count('"""')
    
    if triple_single % 2 != 0:
        print(f"Aviso: Número ímpar de aspas triplas simples encontrado: {triple_single}")
        # Adiciona uma aspa tripla de fechamento se necessário
        content = content + "'''"
    
    if triple_double % 2 != 0:
        print(f"Aviso: Número ímpar de aspas triplas duplas encontrado: {triple_double}")
        # Adiciona aspas triplas duplas de fechamento se necessário
        content = content + '"""'
    
    # Salva o arquivo corrigido
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Arquivo corrigido salvo como: {output_file}")

if __name__ == "__main__":
    input_file = r"c:\Users\saide\pdv3\database\database.py"
    output_file = r"c:\Users\saide\pdv3\database\database_fixed.py"
    
    print(f"Corrigindo arquivo: {input_file}")
    fix_file(input_file, output_file)
    print("Correção concluída.")
