import sqlite3

def init_db():
    conn = sqlite3.connect('dados.db')
    c = conn.cursor()
    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Tabela de finanças
    c.execute('''CREATE TABLE IF NOT EXISTS transacoes 
                 (id INTEGER PRIMARY KEY, tipo TEXT, valor REAL, data TEXT, categoria TEXT)''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
