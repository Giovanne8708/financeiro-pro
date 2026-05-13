import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, timedelta

# =========================================================
# CONFIGURAÇÃO DE ELITE
# =========================================================
st.set_page_config(page_title="Financeiro Pro", layout="wide", page_icon="📈")

# CSS para esconder o menu lateral e criar cards modernos
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .stApp { background: #0f172a; }
        .metric-card {
            background: #1e293b;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #334155;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# BANCO DE DADOS PROFISSIONAL
# =========================================================
def init_db():
    conn = sqlite3.connect('financeiro_pro.db')
    c = conn.cursor()
    # Tabela de Saldo e Investimentos
    c.execute('''CREATE TABLE IF NOT EXISTS status (id int primary key, saldo real, cdb real)''')
    # Tabela de Movimentações (Entradas, Gastos, Apostas)
    c.execute('''CREATE TABLE IF NOT EXISTS movs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, desc TEXT, valor REAL, cat TEXT, tipo TEXT)''')
    # Tabela de Metas
    c.execute('''CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, alvo REAL)''')
    
    c.execute("SELECT COUNT(*) FROM status")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO status VALUES (1, 0.0, 0.0)")
    conn.commit()
    conn.close()

init_db()

# =========================================================
# LÓGICA DE NEGÓCIO
# =========================================================
def format_br(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_data():
    conn = sqlite3.connect('financeiro_pro.db')
    status = pd.read_sql("SELECT * FROM status WHERE id=1", conn).iloc[0]
    movs = pd.read_sql("SELECT * FROM movs ORDER BY id DESC", conn)
    metas = pd.read_sql("SELECT * FROM metas", conn)
    conn.close()
    return status, movs, metas

# =========================================================
# INTERFACE PRINCIPAL
# =========================================================
status, movs, metas = get_data()

st.title("💰 Financeiro Pro")
st.write(f"Olá, Giovanne | {datetime.now().strftime('%d/%m/%Y')}")

# --- DASHBOARD DE MÉTRICAS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Saldo em Conta", format_br(status['saldo']))
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Investido (CDB Inter)", format_br(status['cdb']))
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    # Projeção de rendimento (Baseado em 100% CDI ~11.15% aa)
    rend_dia = (status['cdb'] * 0.1115 / 252)
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Rendimento Estimado Hoje", format_br(rend_dia), delta_color="normal")
    st.markdown('</div>', unsafe_allow_html=True)

# --- NAVEGAÇÃO POR ABAS ---
tab1, tab2, tab3 = st.tabs(["💸 Lançamentos", "📊 Inteligência", "🎯 Metas"])

with tab1:
    with st.expander("📝 Novo Registro", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        desc = c1.text_input("Descrição")
        valor = c2.number_input("Valor R$", min_value=0.0)
        tipo = c3.selectbox("Tipo", ["Gasto", "Entrada", "Aposta (Bet)", "Investir no CDB"])
        
        cat = st.selectbox("Categoria", ["Alimentação", "Contas Fixas", "Lazer", "Salário", "Extra", "Outros"])
        
        if st.button("Salvar Movimentação", use_container_width=True):
            conn = sqlite3.connect('financeiro_pro.db')
            cur = conn.cursor()
            cur.execute("INSERT INTO movs (data, desc, valor, cat, tipo) VALUES (?,?,?,?,?)",
                        (datetime.now().strftime("%Y-%m-%d"), desc, valor, cat, tipo))
            
            # Atualiza Saldo Real
            if tipo == "Gasto" or tipo == "Aposta (Bet)":
                cur.execute("UPDATE status SET saldo = saldo - ? WHERE id=1", (valor,))
            elif tipo == "Entrada":
                cur.execute("UPDATE status SET saldo = saldo + ? WHERE id=1", (valor,))
            elif tipo == "Investir no CDB":
                cur.execute("UPDATE status SET saldo = saldo - ?, cdb = cdb + ? WHERE id=1", (valor, valor))
            
            conn.commit()
            conn.close()
            st.success("Lançado com sucesso!")
            st.rerun()

    st.subheader("Histórico Recente")
    st.dataframe(movs.head(10), use_container_width=True, hide_index=True)

with tab2:
    if not movs.empty:
        col_left, col_right = st.columns(2)
        
        # Gastos por Categoria
        gastos = movs[movs['tipo'].isin(['Gasto', 'Aposta (Bet)'])]
        fig_pizza = px.pie(gastos, values='valor', names='cat', hole=0.4, title="Onde está seu dinheiro?")
        fig_pizza.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        col_left.plotly_chart(fig_pizza, use_container_width=True)
        
        # Monitor de Apostas (Regra de Ouro)
        total_bets = movs[movs['tipo'] == 'Aposta (Bet)']['valor'].sum()
        col_right.markdown(f"""
            <div style="background:#334155; padding:20px; border-radius:15px; border-left: 10px solid #f87171;">
                <h4>Monitor de Apostas</h4>
                <p>Total gasto este mês: <b>{format_br(total_bets)}</b></p>
                <p><small>Mantenha sempre abaixo do seu limite estipulado.</small></p>
            </div>
        """, unsafe_allow_html=True)

with tab3:
    st.subheader("Suas Metas de Longo Prazo")
    c_m1, c_m2 = st.columns(2)
    m_nome = c_m1.text_input("Nome da Meta (Ex: Viagem)")
    m_alvo = c_m2.number_input("Valor Alvo R$")
    if st.button("Criar Nova Meta"):
        conn = sqlite3.connect('financeiro_pro.db')
        conn.execute("INSERT INTO metas (nome, alvo) VALUES (?,?)", (m_nome, m_alvo))
        conn.commit()
        conn.close()
        st.rerun()
    
    st.divider()
    for _, meta in metas.iterrows():
        progresso = min(status['cdb'] / meta['alvo'], 1.0) if meta['alvo'] > 0 else 0
        st.write(f"**{meta['nome']}** ({format_br(status['cdb'])} de {format_br(meta['alvo'])})")
        st.progress(progresso)
