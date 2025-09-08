import sqlite3
import os

def fix_vendas_mes():
    # Path to the database
    db_path = os.path.join(os.getenv('APPDATA'), 'SistemaGestao', 'database', 'sistema.db')
    
    # Backup the database first
    backup_path = db_path + '.backup'
    if not os.path.exists(backup_path):
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Update the method to use 'total' instead of 'valor_total'
        with open('c:\\Users\\Cuamba\\pdv3\\database\\database.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Make the replacement
        new_content = content.replace(
            """                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE valor_total 
                    END""",
            """                    CASE 
                        WHEN status = 'Anulada' THEN 0 
                        ELSE total 
                    END"""
        )
        
        # Write the updated content back to the file
        with open('c:\\Users\\Cuamba\\pdv3\\database\\database.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("Updated database.py to use 'total' column instead of 'valor_total'")
        print("Please restart the application for changes to take effect.")
        
    except Exception as e:
        print(f"Error updating the file: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_vendas_mes()
