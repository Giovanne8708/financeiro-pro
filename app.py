import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config("Financeiro PRO", layout="wide")

DB = "financeiro_pro.db"

# ------------------ DB ------------------
def conectar():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS categorias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS tipos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS lancamentos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        descricao TEXT,
        valor REAL,
        categoria TEXT,
        tipo TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS config(
        id INTEGER PRIMARY KEY,
        salario REAL,
        meta REAL)""")

    if c.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
        for x in ["Moradia","Alimentação","Transporte","Lazer","Contas"]:
            c.execute("INSERT INTO categorias(nome) VALUES (?)",(x,))

    if c.execute("SELECT COUNT(*) FROM tipos").fetchone()[0] == 0:
        for x in ["Entrada","Gasto","Investimento"]:
            c.execute("INSERT INTO tipos(nome) VALUES (?)",(x,))

    if c.execute("SELECT COUNT(*) FROM config").fetchone()[0] == 0:
        c.execute("INSERT INTO config VALUES (1,0,10000)")

    conn.commit()
    conn.close()

init_db()

# ------------------ LOAD ------------------
conn = conectar()
df = pd.read_sql("SELECT * FROM lancamentos", conn)
cats = pd.read_sql("SELECT nome FROM categorias", conn)["nome"].tolist()
tipos = pd.read_sql("SELECT nome FROM tipos", conn)["nome"].tolist()
cfg = pd.read_sql("SELECT * FROM config", conn).iloc[0]
conn.close()

salario = float(cfg["salario"])
meta = float(cfg["meta"])

# ------------------ CALCULOS ------------------
entradas = df[df.tipo=="Entrada"]["valor"].sum()
gastos = df[df.tipo=="Gasto"]["valor"].sum()
invest = df[df.tipo=="Investimento"]["valor"].sum()

caixa = entradas - gastos - invest
patrimonio = invest
saldo_total = caixa + patrimonio

# ------------------ HEADER ------------------
st.title("💎 Financeiro PRO")

c1,c2,c3,c4 = st.columns(4)
c1.metric("Caixa Atual", f"R$ {caixa:,.2f}")
c2.metric("Patrimônio", f"R$ {patrimonio:,.2f}")
c3.metric("Saldo Total", f"R$ {saldo_total:,.2f}")
c4.metric("Meta", f"R$ {meta:,.2f}")

# ------------------ TABS ------------------
t1,t2,t3,t4 = st.tabs(["Visão Geral","Lançamentos","Diagnóstico","Configurações"])

# ------------------ VISÃO GERAL ------------------
with t1:
    if not df.empty:
        fig = px.pie(df[df.tipo=="Gasto"], values="valor", names="categoria", title="Para onde vai seu dinheiro")
        st.plotly_chart(fig, use_container_width=True)

# ------------------ LANÇAMENTOS ------------------
with t2:
    st.subheader("Novo Lançamento")

    desc = st.text_input("Descrição")
    valor = st.number_input("Valor",0.0)
    cat = st.selectbox("Categoria", cats)
    tipo = st.selectbox("Tipo", tipos)

    if st.button("Salvar"):
        conn = conectar()
        conn.execute(
            "INSERT INTO lancamentos(data,descricao,valor,categoria,tipo) VALUES (?,?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"),desc,valor,cat,tipo)
        )
        conn.commit()
        conn.close()
        st.rerun()

    st.dataframe(df, use_container_width=True)

# ------------------ DIAGNOSTICO ------------------
with t3:
    st.subheader("Diagnóstico Automático")

    if gastos > entradas:
        st.error("Você está gastando mais do que ganha.")
    else:
        st.success("Seu fluxo financeiro está positivo.")

    if salario > 0:
        perc = (invest/salario)*100
        st.write(f"{perc:.1f}% do seu salário está virando patrimônio.")

# ------------------ CONFIG ------------------
with t4:
    st.subheader("Sistema 100% Editável")

    nova_cat = st.text_input("Nova Categoria")
    if st.button("Adicionar Categoria"):
        conn = conectar()
        conn.execute("INSERT INTO categorias(nome) VALUES (?)",(nova_cat,))
        conn.commit()
        conn.close()
        st.rerun()

    novo_tipo = st.text_input("Novo Tipo")
    if st.button("Adicionar Tipo"):
        conn = conectar()
        conn.execute("INSERT INTO tipos(nome) VALUES (?)",(novo_tipo,))
        conn.commit()
        conn.close()
        st.rerun()

    novo_salario = st.number_input("Salário", value=salario)
    nova_meta = st.number_input("Meta", value=meta)

    if st.button("Salvar Configurações"):
        conn = conectar()
        conn.execute("UPDATE config SET salario=?, meta=? WHERE id=1",(novo_salario,nova_meta))
        conn.commit()
        conn.close()
        st.rerun()
