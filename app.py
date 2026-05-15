# ================== FINANCE PRO ULTRA ==================
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

st.set_page_config(page_title="Finance PRO ULTRA", layout="wide")

# ---------------- TEMA DARK PROFISSIONAL ----------------
st.markdown("""
<style>
.stApp { background:#0d1117; color:white; }
button[kind="primary"] { background:#00ff88; color:black; border-radius:8px; }
[data-testid="stMetric"] { background:#161b22; padding:15px; border-radius:12px; }
</style>
""", unsafe_allow_html=True)

# ---------------- BANCO CSV ----------------
ARQS = {
    "receitas.csv": ["data","origem","valor","conta"],
    "despesas.csv": ["data","categoria","descricao","valor","conta"],
    "fixos.csv": ["descricao","valor"],
    "cartoes.csv": ["banco","limite","vencimento"],
    "investimentos.csv": ["ativo","valor","tipo"],
    "patrimonio.csv": ["salario","extra","origem_extra","inter","itau"]
}

def init():
    for a,c in ARQS.items():
        if not Path(a).exists():
            pd.DataFrame(columns=c).to_csv(a,index=False)

def load(a): return pd.read_csv(a)
def save(df,a): df.to_csv(a,index=False)

init()

# ---------------- MENU HORIZONTAL ----------------
if "pg" not in st.session_state: st.session_state.pg="Home"

c1,c2,c3,c4,c5 = st.columns(5)
if c1.button("🏠 Home"): st.session_state.pg="Home"
if c2.button("📊 Análise"): st.session_state.pg="Analise"
if c3.button("💳 Cartões"): st.session_state.pg="Cartoes"
if c4.button("🏦 Patrimônio"): st.session_state.pg="Patrimonio"
if c5.button("📈 Investimentos"): st.session_state.pg="Invest"

st.divider()
pg = st.session_state.pg

# ---------------- HOME ----------------
if pg=="Home":
    rec,desp = load("receitas.csv"), load("despesas.csv")
    saldo = rec.valor.sum()-desp.valor.sum()

    st.title("Visão Geral Hoje")
    m1,m2,m3 = st.columns(3)
    m1.metric("Saldo Real", f"R$ {saldo:,.2f}")
    m2.metric("Ganhos", f"R$ {rec.valor.sum():,.2f}")
    m3.metric("Gastos", f"R$ {desp.valor.sum():,.2f}")

    st.subheader("Últimos Lançamentos")
    st.dataframe(desp.tail(5),use_container_width=True)

# ---------------- ANALISE ----------------
elif pg=="Analise":
    desp = load("despesas.csv")
    if not desp.empty:
        c1,c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(desp,values="valor",names="categoria",template="plotly_dark"))
        with c2:
            desp["data"]=pd.to_datetime(desp["data"])
            mes = desp.groupby(desp["data"].dt.day).sum(numeric_only=True)
            st.plotly_chart(px.line(mes,y="valor",template="plotly_dark"))

# ---------------- CARTOES ----------------
elif pg=="Cartoes":
    st.title("Cartões")
    cart = load("cartoes.csv")
    desp = load("despesas.csv")

    for _,r in cart.iterrows():
        fatura = desp[desp.conta==f"Cartão {r['banco']}"].valor.sum()
        st.metric(f"Fatura {r['banco']}", f"R$ {fatura:,.2f}")

# ---------------- PATRIMONIO ----------------
elif pg=="Patrimonio":
    st.title("Patrimônio e Rendas")
    pat = load("patrimonio.csv")

    with st.form("pat"):
        s = st.number_input("Salário Mensal")
        e = st.number_input("Renda Extra")
        o = st.text_input("Origem da Renda Extra")
        inter = st.number_input("Saldo Inter")
        itau = st.number_input("Saldo Itaú")
        if st.form_submit_button("Salvar"):
            save(pd.DataFrame([[s,e,o,inter,itau]],columns=ARQS["patrimonio.csv"]),"patrimonio.csv")

    if not pat.empty:
        inv = load("investimentos.csv").valor.sum()
        total = pat.inter[0]+pat.itau[0]+inv
        st.metric("Patrimônio Total", f"R$ {total:,.2f}")

# ---------------- INVESTIMENTOS ----------------
elif pg=="Invest":
    st.title("Investimentos")
    inv = load("investimentos.csv")

    with st.form("inv"):
        a = st.text_input("Ativo")
        v = st.number_input("Valor")
        t = st.selectbox("Tipo",["Tesouro","Ações","Cripto"])
        if st.form_submit_button("Adicionar"):
            save(pd.concat([inv,pd.DataFrame([[a,v,t]],columns=ARQS["investimentos.csv"])]),"investimentos.csv")

    if not inv.empty:
        st.plotly_chart(px.pie(inv,values="valor",names="tipo",template="plotly_dark"))
