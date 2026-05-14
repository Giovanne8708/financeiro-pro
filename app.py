import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

# =========================================================
# CONFIG E ESTILO
# =========================================================
st.set_page_config(page_title="Financeiro PRO", page_icon="💰", layout="wide")

st.markdown("""
<style>
    .main { background-color: #0E1117; color: white; }
    .stMetric { background: #161B22; border: 1px solid #30363D; padding: 15px; border-radius: 16px; }
    .card { background: #161B22; border: 1px solid #30363D; padding: 18px; border-radius: 18px; text-align: center; }
    h1, h2, h3, h4 { color: #00ff88 !important; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# BANCO DE DADOS (CSV)
# =========================================================
FILES = {
    "receitas.csv": ["data", "categoria", "valor"],
    "despesas.csv": ["data", "categoria", "valor"],
    "fixos.csv": ["descricao", "valor_parcela", "parcelas_total", "parcelas_pagas"]
}

def init_db():
    for file, cols in FILES.items():
        if not Path(file).exists():
            pd.DataFrame(columns=cols).to_csv(file, index=False)

def load_data(file):
    df = pd.read_csv(file)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors='coerce').dt.date
    return df

def save_data(df, file):
    df.to_csv(file, index=False)

init_db()

# =========================================================
# LOGIN
# =========================================================
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 Acesso")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "giovanne" and s == "8708":
            st.session_state.logado = True
            st.rerun()
    st.stop()

# =========================================================
# NAVEGAÇÃO
# =========================================================
menu = ["Dashboard", "Receitas", "Despesas", "Fixos"]
escolha = st.sidebar.radio("Menu", menu)

if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.rerun()

# Carregamento Global
rec = load_data("receitas.csv")
des = load_data("despesas.csv")
fix = load_data("fixos.csv")

# =========================================================
# LÓGICA DE SALDO (SUBTRAÇÃO)
# =========================================================
total_rec = rec["valor"].sum()
total_des = des["valor"].sum()
# O saldo considera o que já foi ganho menos o que já foi gasto
saldo_atual = total_rec - total_des

def moeda(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================
# DASHBOARD
# =========================================================
if escolha == "Dashboard":
    st.title("📊 Resumo Financeiro")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Ganhos Totais", moeda(total_rec))
    with c2: st.metric("Gastos Totais", moeda(total_des), delta=f"-{moeda(total_des)}", delta_color="inverse")
    with c3: st.metric("Saldo em Conta", moeda(saldo_atual))

    st.markdown("---")
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Balanço")
        fig = px.bar(x=["Entradas", "Saídas"], y=[total_rec, total_des], color=["Entradas", "Saídas"], template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# RECEITAS E DESPESAS
# =========================================================
elif escolha in ["Receitas", "Despesas"]:
    tipo = escolha.lower()
    st.title(f"📑 Gerenciar {escolha}")
    
    with st.form(f"form_{tipo}"):
        v = st.number_input("Valor", min_value=0.0)
        cat = st.selectbox("Categoria", ["Salário", "Extra", "Alimentação", "Lazer", "Outros"])
        if st.form_submit_button("Salvar"):
            novo = pd.DataFrame([{"data": date.today(), "categoria": cat, "valor": v}])
            df_atual = load_data(f"{tipo}.csv")
            save_data(pd.concat([df_atual, novo]), f"{tipo}.csv")
            st.rerun()
            
    st.dataframe(load_data(f"{tipo}.csv"), use_container_width=True)

# =========================================================
# FIXOS (COM BOTÃO DE PAGAR QUE SUBTRAI SALDO)
# =========================================================
elif escolha == "Fixos":
    st.title("📌 Contas Fixas / Parceladas")
    
    with st.expander("➕ Adicionar Nova Conta"):
        with st.form("f_fix"):
            desc = st.text_input("Descrição")
            val = st.number_input("Valor da Parcela")
            tot = st.number_input("Total de Parcelas", min_value=1)
            if st.form_submit_button("Cadastrar"):
                n = pd.DataFrame([{"descricao": desc, "valor_parcela": val, "parcelas_total": tot, "parcelas_pagas": 0}])
                save_data(pd.concat([fix, n]), "fixos.csv")
                st.rerun()

    for i, r in fix.iterrows():
        c1, c2, c3 = st.columns([3, 2, 2])
        c1.write(f"**{r['descricao']}** ({int(r['parcelas_pagas'])}/{int(r['parcelas_total'])})")
        c2.write(moeda(r['valor_parcela']))
        
        # Botão para Pagar Parcela: Registra despesa e aumenta contador
        if c3.button(f"Pagar Parcela ✅", key=f"btn_{i}"):
            if r['parcelas_pagas'] < r['parcelas_total']:
                # 1. Adiciona na tabela de despesas (para subtrair do saldo)
                n_desp = pd.DataFrame([{"data": date.today(), "categoria": "Contas Fixas", "valor": r['valor_parcela']}])
                save_data(pd.concat([load_data("despesas.csv"), n_desp]), "despesas.csv")
                
                # 2. Atualiza contador de parcelas
                fix.at[i, 'parcelas_pagas'] += 1
                save_data(fix, "fixos.csv")
                st.success("Parcela paga e debitada do saldo!")
                st.rerun()
