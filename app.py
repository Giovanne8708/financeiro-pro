# ========= FINANCEIRO PRO DEFINITIVO =========
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

st.set_page_config(layout="wide")

# ---------- CSV ----------
ARQS = {
    "receitas.csv": ["data","origem","valor","conta"],
    "despesas.csv": ["data","categoria","descricao","valor","conta"],
    "cartoes.csv": ["banco","limite","vencimento"],
    "investimentos.csv": ["ativo","valor","tipo"],
}

def init():
    for a,c in ARQS.items():
        if not Path(a).exists():
            pd.DataFrame(columns=c).to_csv(a,index=False)

def load(a): return pd.read_csv(a)
def save(df,a): df.to_csv(a,index=False)

init()

# ---------- MENU ----------
if "pg" not in st.session_state: st.session_state.pg="Home"
c1,c2,c3,c4 = st.columns(4)
if c1.button("🏠 Home"): st.session_state.pg="Home"
if c2.button("💳 Cartões"): st.session_state.pg="Cartoes"
if c3.button("📊 Análise"): st.session_state.pg="Analise"
if c4.button("📈 Investimentos"): st.session_state.pg="Invest"

st.divider()
pg = st.session_state.pg

rec = load("receitas.csv")
desp = load("despesas.csv")
cart = load("cartoes.csv")
inv = load("investimentos.csv")

saldo = rec.valor.sum() - desp.valor.sum()

# ---------- HOME ----------
if pg=="Home":
    st.title("Visão Geral Hoje")
    st.metric("Saldo Atual", f"R$ {saldo:,.2f}")

    st.subheader("➕ Lançar Despesa")
    with st.form("desp"):
        c1,c2,c3,c4 = st.columns(4)
        v = c1.number_input("Valor")
        cat = c2.text_input("Categoria")
        desc = c3.text_input("Descrição")
        conta = c4.selectbox("Conta", ["Inter","Itaú"] + [f"Cartão {b}" for b in cart.banco])
        if st.form_submit_button("Salvar Despesa"):
            nova = pd.DataFrame([[date.today(),cat,desc,v,conta]],
            columns=ARQS["despesas.csv"])
            save(pd.concat([desp,nova]),"despesas.csv")
            st.rerun()

    st.subheader("➕ Lançar Receita")
    with st.form("rec"):
        c1,c2,c3 = st.columns(3)
        v = c1.number_input("Valor ",key="r")
        o = c2.text_input("Origem")
        conta = c3.selectbox("Conta ",["Inter","Itaú"])
        if st.form_submit_button("Salvar Receita"):
            nova = pd.DataFrame([[date.today(),o,v,conta]],
            columns=ARQS["receitas.csv"])
            save(pd.concat([rec,nova]),"receitas.csv")
            st.rerun()

# ---------- CARTOES ----------
elif pg=="Cartoes":
    st.title("Cartões de Crédito")

    for _,r in cart.iterrows():
        fatura = desp[desp.conta==f"Cartão {r['banco']}"].valor.sum()
        st.metric(f"{r['banco']} • Fatura", f"R$ {fatura:,.2f}")

    st.subheader("Cadastrar Cartão")
    with st.form("cart"):
        b = st.text_input("Banco")
        l = st.number_input("Limite")
        v = st.number_input("Vencimento")
        if st.form_submit_button("Salvar"):
            novo = pd.DataFrame([[b,l,v]],columns=ARQS["cartoes.csv"])
            save(pd.concat([cart,novo]),"cartoes.csv")
            st.rerun()

# ---------- ANALISE ----------
elif pg=="Analise":
    if not desp.empty:
        st.plotly_chart(px.pie(desp,values="valor",names="categoria"))
        desp["data"] = pd.to_datetime(desp["data"])
        linha = desp.groupby(desp.data.dt.day).sum(numeric_only=True)
        st.plotly_chart(px.line(linha,y="valor"))

# ---------- INVEST ----------
elif pg=="Invest":
    st.title("Investimentos")
    with st.form("inv"):
        a = st.text_input("Ativo")
        v = st.number_input("Valor")
        t = st.selectbox("Tipo",["Tesouro","Ações","Cripto"])
        if st.form_submit_button("Adicionar"):
            novo = pd.DataFrame([[a,v,t]],columns=ARQS["investimentos.csv"])
            save(pd.concat([inv,novo]),"investimentos.csv")
            st.rerun()

    if not inv.empty:
        st.plotly_chart(px.pie(inv,values="valor",names="tipo"))
