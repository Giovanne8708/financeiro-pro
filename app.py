import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Finances and Economy", layout="wide", page_icon="📈")

# Estilo Dark Mode Premium para Celular
st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
        .stApp {background: #0f172a; color: white;}
        div[data-testid="stMetric"] {
            background: #1e293b;
            border: 1px solid #334155;
            padding: 20px;
            border-radius: 20px;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background: #1e293b;
            border-radius: 12px;
            color: white;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('financeiro_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patrimonio (id int primary key, saldo real, cdb real, reserva_meta real)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mov (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, desc TEXT, valor REAL, cat TEXT, tipo TEXT)''')
    c.execute("SELECT COUNT(*) FROM patrimonio")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO patrimonio VALUES (1, 0.0, 0.0, 10000.0)") # Meta padrão 10k
    conn.commit()
    conn.close()

init_db()

def carregar_dados():
    conn = sqlite3.connect('financeiro_pro.db')
    p = pd.read_sql("SELECT * FROM patrimonio WHERE id=1", conn).iloc[0]
    m = pd.read_sql("SELECT * FROM mov ORDER BY id DESC", conn)
    conn.close()
    return p, m

# --- AUTENTICAÇÃO ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>📊 Finances and Economy</h1>", unsafe_allow_html=True)
    with st.container():
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if user == "giovanne" and senha == "8708":
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- INTERFACE ---
p, m = carregar_dados()
st.title("📈 Finances and Economy")

# Métricas Principais
c1, c2, c3 = st.columns(3)
c1.metric("Saldo Disponível", f"R$ {p['saldo']:,.2f}")
c2.metric("Reserva CDB (Inter)", f"R$ {p['cdb']:,.2f}")
# Projeção baseada em 100% do CDI (aprox. 0.04% ao dia útil)
rend_estimado = p['cdb'] * 0.0004
c3.metric("Rendimento Previsto Hoje", f"R$ {rend_estimado:,.2f}")

tab1, tab2, tab3 = st.tabs(["💎 Gestão", "📊 Evolução", "🎯 Metas"])

with tab1:
    st.subheader("Novo Lançamento")
    col_a, col_b = st.columns(2)
    with col_a:
        desc = st.text_input("Descrição do Gasto/Ganho")
        valor = st.number_input("Valor (R$)", min_value=0.0)
    with col_b:
        tipo = st.selectbox("Tipo de Fluxo", ["Gasto", "Entrada", "Investimento"])
        cat = st.selectbox("Categoria", ["Alimentação", "Lazer", "Contas Fixas", "Salário", "Bet", "Outros"])
    
    if st.button("Confirmar", use_container_width=True):
        conn = sqlite3.connect('financeiro_pro.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO mov (data, desc, valor, cat, tipo) VALUES (?,?,?,?,?)", 
                    (datetime.now().strftime("%Y-%m-%d"), desc, valor, cat, tipo))
        
        if tipo == "Gasto":
            cur.execute("UPDATE patrimonio SET saldo = saldo - ? WHERE id=1", (valor,))
        elif tipo == "Entrada":
            cur.execute("UPDATE patrimonio SET saldo = saldo + ? WHERE id=1", (valor,))
        elif tipo == "Investimento":
            cur.execute("UPDATE patrimonio SET saldo = saldo - ?, cdb = cdb + ? WHERE id=1", (valor, valor))
            
        conn.commit()
        conn.close()
        st.success("Dados atualizados!")
        st.rerun()

with tab2:
    if not m.empty:
        st.subheader("Análise Econômica")
        gastos_df = m[m['tipo']=='Gasto']
        if not gastos_df.empty:
            fig = px.pie(gastos_df, values='valor', names='cat', hole=0.5, title="Distribuição de Gastos")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig, use_container_width=True)
        
        st.write("### Histórico")
        st.dataframe(m, use_container_width=True)
    else:
        st.info("Sem dados registrados.")

with tab3:
    st.subheader("Reserva de Emergência")
    progresso = min(p['cdb'] / p['reserva_meta'], 1.0)
    st.write(f"Alvo: R$ {p['reserva_meta']:,.2f}")
    st.progress(progresso)
    st.write(f"{progresso*100:.1f}% da meta atingida")
    
    st.divider()
    if st.button("Sair do Sistema"):
        st.session_state.auth = False
        st.rerun()
