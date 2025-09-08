import re

def fix_specific_issues(content):
    # Corrigir problemas específicos identificados
    
    # 1. Corrigir strings quebradas em múltiplas linhas
    content = re.sub(r'"""\s*\n\s*', '"""', content)  # Remover quebras após """
    content = re.sub(r'\n\s*"""', '"""', content)    # Remover quebras antes de """
    
    # 2. Corrigir aspas simples dentro de strings SQL
    content = re.sub(r"(?<=\()'(.*?)'(?=\))", r"'\1'", content)  # Corrigir aspas simples em parênteses
    
    # 3. Corrigir strings SQL quebradas em múltiplas linhas
    sql_blocks = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    for block in sql_blocks:
        # Remover quebras de linha e múltiplos espaços dentro de blocos SQL
        fixed_block = ' '.join(line.strip() for line in block.split('\n') if line.strip())
        content = content.replace(f'"""{block}"""', f'"""{fixed_block}"""')
    
    # 4. Corrigir problemas comuns de formatação
    content = re.sub(r'\s+\n', '\n', content)  # Remover espaços no final das linhas
    content = re.sub(r'\n{3,}', '\n\n', content)  # Remover múltiplas linhas em branco
    
    return content

def fix_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplicar correções
    fixed_content = fix_specific_issues(content)
    
    # Salvar o arquivo corrigido
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Arquivo corrigido salvo como: {output_file}")

if __name__ == "__main__":
    input_file = r"c:\Users\saide\pdv3\database\database.py"
    output_file = r"c:\Users\saide\pdv3\database\database_fixed.py"
    
    print(f"Aplicando correções avançadas no arquivo: {input_file}")
    fix_file(input_file, output_file)
    print("Correção avançada concluída.")
    
    # Mostrar estatísticas
    with open(input_file, 'r', encoding='utf-8') as f:
        original_lines = len(f.readlines())
    
    with open(output_file, 'r', encoding='utf-8') as f:
        fixed_lines = len(f.readlines())
    
    print(f"\nEstatísticas:")
    print(f"- Linhas no original: {original_lines}")
    print(f"- Linhas após correção: {fixed_lines}")
    print(f"- Diferença: {original_lines - fixed_lines} linhas removidas")
