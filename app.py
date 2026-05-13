import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime

# =========================================================
# CONFIGURAÇÃO E BANCO DE DADOS
# =========================================================
st.set_page_config(page_title="Financeiro Pro", layout="wide", page_icon="💰")

def conectar():
    conn = sqlite3.connect('financeiro_pro.db', check_same_thread=False)
    return conn

def init_db():
    conn = conectar()
    c = conn.cursor()
    # Tabela de Saldo e Investimentos
    c.execute('''CREATE TABLE IF NOT EXISTS patrimonio 
                 (id INTEGER PRIMARY KEY, saldo REAL, cdb REAL, tesouro REAL)''')
    # Tabela de Movimentações
    c.execute('''CREATE TABLE IF NOT EXISTS mov 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, desc TEXT, valor REAL, cat TEXT, tipo TEXT)''')
    
    # Inicializa patrimônio se vazio
    c.execute("SELECT COUNT(*) FROM patrimonio")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO patrimonio VALUES (1, 0.0, 0.0, 0.0)")
    
    conn.commit()
    conn.close()

init_db()

# =========================================================
# ESTILIZAÇÃO PREMIUM (CSS)
# =========================================================
st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; }
    [data-testid="stMetric"] {
        background: #1e293b;
        border: 1px solid #334155;
        padding: 15px;
        border-radius: 15px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background: #1e293b;
        border-radius: 10px;
        padding: 10px 20px;
        color: white;
    }
    .card-mov {
        background: #1e293b;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# AUTENTICAÇÃO
# =========================================================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>🔐 Financeiro Pro</h1>", unsafe_allow_html=True)
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar", use_container_width=True):
        if user == "giovanne" and password == "8708":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Dados incorretos")
    st.stop()

# =========================================================
# LÓGICA DE DADOS
# =========================================================
def get_patrimonio():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM patrimonio WHERE id=1", conn)
    conn.close()
    return df.iloc[0]

def add_mov(desc, valor, cat, tipo):
    conn = conectar()
    c = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO mov (data, desc, valor, cat, tipo) VALUES (?,?,?,?,?)",
              (data, desc, valor, cat, tipo))
    # Atualiza saldo se for gasto ou entrada
    if tipo == "Gasto":
        c.execute("UPDATE patrimonio SET saldo = saldo - ? WHERE id=1", (valor,))
    elif tipo == "Entrada":
        c.execute("UPDATE patrimonio SET saldo = saldo + ? WHERE id=1", (valor,))
    conn.commit()
    conn.close()

patrimonio = get_patrimonio()

# =========================================================
# INTERFACE PRINCIPAL
# =========================================================
st.title("💰 Financeiro Pro")

# Métricas Principais
m1, m2, m3 = st.columns(3)
m1.metric("Saldo em Conta", f"R$ {patrimonio['saldo']:,.2f}")
m2.metric("Investido (CDB)", f"R$ {patrimonio['cdb']:,.2f}")
# Projeção simples de 1% ao mês no CDB
projecao = patrimonio['cdb'] * 0.00033 # aprox rendimento diário
m3.metric("Rendimento Hoje (Est.)", f"R$ {projecao:,.2f}", delta_color="normal")

tab1, tab2, tab3 = st.tabs(["💸 Lançamentos", "📊 Dashboards", "🏦 Gestão"])

with tab1:
    st.subheader("Novo Registro")
    col_a, col_b = st.columns(2)
    with col_a:
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
    with col_b:
        tipo = st.selectbox("Tipo", ["Gasto", "Entrada"])
        cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Serviços", "Salário", "Bet"])
    
    if st.button("Confirmar Lançamento", use_container_width=True):
        if desc and valor > 0:
            add_mov(desc, valor, cat, tipo)
            st.success("Registrado com sucesso!")
            st.rerun()

with tab2:
    st.subheader("Análise de Gastos")
    conn = conectar()
    df_mov = pd.read_sql("SELECT * FROM mov ORDER BY id DESC", conn)
    conn.close()
    
    if not df_mov.empty:
        fig = px.pie(df_mov[df_mov['tipo']=='Gasto'], values='valor', names='cat', 
                     title="Distribuição por Categoria", hole=0.4,
                     color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("### Últimas Movimentações")
        for _, row in df_mov.head(10).iterrows():
            cor = "#ef4444" if row['tipo'] == "Gasto" else "#22c55e"
            st.markdown(f"""
                <div class="card-mov" style="border-left-color: {cor}">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{row['desc']}</b>
                        <span>{row['data']}</span>
                    </div>
                    <div style="font-size: 20px; font-weight: bold; color: {cor}">
                        {' - ' if row['tipo'] == "Gasto" else ' + '} R$ {row['valor']:,.2f}
                    </div>
                </div>
            """, unsafe_allow_html=True)

with tab3:
    st.subheader("Ajuste de Patrimônio")
    new_saldo = st.number_input("Corrigir Saldo Bancário", value=patrimonio['saldo'])
    new_cdb = st.number_input("Total no CDB (Inter)", value=patrimonio['cdb'])
    
    if st.button("Atualizar Banco", use_container_width=True):
        conn = conectar()
        c = conn.cursor()
        c.execute("UPDATE patrimonio SET saldo=?, cdb=? WHERE id=1", (new_saldo, new_cdb))
        conn.commit()
        conn.close()
        st.rerun()

# Sidebar para Sair
with st.sidebar:
    if st.button("🚪 Sair"):
        st.session_state.auth = False
        st.rerun()
