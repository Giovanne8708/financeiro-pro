python
import sqlite3

conn = sqlite3.connect(
    'dados.db',
    check_same_thread=False
)

cursor = conn.cursor()

# =========================================
# TABELA USUÁRIOS
# =========================================

cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    senha TEXT
)
''')

# =========================================
# TABELA GASTOS
# =========================================

cursor.execute('''
CREATE TABLE IF NOT EXISTS gastos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    descricao TEXT,
    categoria TEXT,
    valor REAL,
    data TEXT
)
''')

# =========================================
# TABELA INVESTIMENTOS
# =========================================

cursor.execute('''
CREATE TABLE IF NOT EXISTS investimentos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    tipo TEXT,
    valor REAL
)
''')

conn.commit()


---