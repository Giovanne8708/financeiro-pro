import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Finances and Economy",
    layout="wide",
    page_icon="💰"
)

# =====================================================
# ESTILO
# =====================================================
st.markdown("""
<style>
[data-testid="stSidebar"]{ display:none; }
.stApp{ background:#0f172a; color:white; }
div[data-testid="stMetric"]{
    background:#1e293b;
    border:1px solid #334155;
    padding:20px;
    border-radius:18px;
}
.stTabs [data-baseweb="tab"]{
    background:#1e293b;
    border-radius:12px;
    color:white;
    padding:10px;
}
.stButton button{
    border-radius:12px;
    background:#2563eb;
    color:white;
    border:none;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE
# =====================================================
DB = "financeiro_pro.db"

def conectar():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        meta_reserva REAL,
        salario_mensal REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS patrimonio (
        id INTEGER PRIMARY KEY,
        saldo REAL,
        investimentos REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS mov (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        descricao TEXT,
        valor REAL,
        categoria TEXT,
        tipo TEXT
    )
    """)

    c.execute("SELECT COUNT(*) FROM config")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO config VALUES (1,'Usuário',10000,0)")

    c.execute("SELECT COUNT(*) FROM patrimonio")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO patrimonio VALUES (1,0,0)")

    conn.commit()
    conn.close()

init_db()

# =====================================================
# FIX ESTRUTURA DO BANCO (MIGRATION AUTOMÁTICA)
# =====================================================
def fix_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("PRAGMA table_info(patrimonio)")
    colunas = [col[1] for col in c.fetchall()]

    if "investimentos" not in colunas:
        c.execute("ALTER TABLE patrimonio ADD COLUMN investimentos REAL DEFAULT 0")

    conn.commit()
    conn.close()

fix_db()

# =====================================================
# LOAD DATA
# =====================================================
def carregar():
    conn = conectar()

    config = pd.read_sql("SELECT * FROM config WHERE id=1", conn).iloc[0]
    patrimonio = pd.read_sql("SELECT * FROM patrimonio WHERE id=1", conn).iloc[0]
    mov = pd.read_sql("SELECT * FROM mov ORDER BY id DESC", conn)

    conn.close()
    return config, patrimonio, mov

config, p, m = carregar()

# =====================================================
# LOGIN
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>💰 Finances and Economy</h1>", unsafe_allow_html=True)
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", use_container_width=True):
        if usuario == "giovanne" and senha == "8708":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Usuário inválido")
    st.stop()

# =====================================================
# HEADER
# =====================================================
st.title(f"📈 Painel Financeiro - {config['nome']}")

saldo = float(p["saldo"])
investimentos = float(p["investimentos"])
meta = float(config["meta_reserva"])
rendimento = investimentos * 0.0004

# (restante do seu código permanece IGUAL — sem nenhuma outra alteração)
