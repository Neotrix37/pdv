def fix_end_of_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há aspas triplas não fechadas no final do arquivo
    if content.count('"""') % 2 != 0:
        # Adicionar aspas triplas de fechamento
        content = content.rstrip() + '\n"""\n'
    
    # Remover múltiplas linhas em branco no final do arquivo
    content = content.rstrip() + '\n'
    # Salvar o arquivo corrigido
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Arquivo corrigido salvo como: {output_file}")

if __name__ == "__main__":
    input_file = r"c:\Users\saide\pdv3\database\database_fixed.py"
    output_file = r"c:\Users\saide\pdv3\database\database_final.py"
    
    print(f"Corrigindo final do arquivo: {input_file}")
    fix_end_of_file(input_file, output_file)
    print("Correção concluída.")
