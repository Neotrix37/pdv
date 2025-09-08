def fix_final_file():
    input_file = r"c:\Users\saide\pdv3\database\database_final.py"
    output_file = r"c:\Users\saide\pdv3\database\database.py"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar a última ocorrência de uma string tripla
    last_triple = content.rfind('"""')
    
    if last_triple != -1:
        # Verificar se a string tripla está fechada
        if content.count('"""') % 2 != 0:
            # Remover qualquer texto após a última string tripla
            content = content[:last_triple + 3] + '\n'
    
    # Garantir que o arquivo termine com uma quebra de linha
    content = content.rstrip() + '\n'
    # Adicionar fechamento da classe Database
    if 'class Database:' in content and not content.strip().endswith('pass'):
        content = content.rstrip() + '\n\n    pass\n'
    # Salvar o arquivo final
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Arquivo final salvo como: {output_file}")

if __name__ == "__main__":
    print("Corrigindo arquivo final...")
    fix_final_file()
    print("Correção concluída.")
