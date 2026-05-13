import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(layout="wide")

# ---------- FUNÇÕES BASE ----------

def load_csv(file, cols):
    try:
        df = pd.read_csv(file)
    except:
        df = pd.DataFrame(columns=cols)
        df.to_csv(file, index=False)
    return df

def save_csv(df, file):
    df.to_csv(file, index=False)

# ---------- CARREGAR BASES ----------

receitas = load_csv("receitas.csv", ["data", "descricao", "valor"])
despesas = load_csv("despesas.csv", ["data", "descricao", "valor"])
fixos = load_csv("fixos.csv", ["descricao", "valor"])

# ---------- TÍTULO ----------

st.title("💼 Financeiro PRO — Controle Total")

# ---------- CADASTROS ----------

st.header("➕ Lançamentos")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Nova Receita")
    with st.form("form_receita"):
        data = st.date_input("Data", date.today())
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        if st.form_submit_button("Adicionar Receita"):
            receitas.loc[len(receitas)] = [data, desc, valor]
            save_csv(receitas, "receitas.csv")
            st.success("Receita adicionada!")

with col2:
    st.subheader("Nova Despesa")
    with st.form("form_despesa"):
        data = st.date_input("Data ", date.today())
        desc = st.text_input("Descrição ")
        valor = st.number_input("Valor ", min_value=0.0, format="%.2f")
        if st.form_submit_button("Adicionar Despesa"):
            despesas.loc[len(despesas)] = [data, desc, valor]
            save_csv(despesas, "despesas.csv")
            st.success("Despesa adicionada!")

# ---------- FIXOS ----------

st.header("📌 Compromissos Fixos")

with st.form("form_fixo"):
    desc = st.text_input("Descrição do Fixo")
    valor = st.number_input("Valor Fixo", min_value=0.0, format="%.2f")
    if st.form_submit_button("Adicionar Fixo"):
        fixos.loc[len(fixos)] = [desc, valor]
        save_csv(fixos, "fixos.csv")
        st.success("Fixo adicionado!")

st.dataframe(fixos, use_container_width=True)

# ---------- PAINEL ----------

st.header("📊 Painel Financeiro")

total_receitas = receitas["valor"].sum()
total_despesas = despesas["valor"].sum()
total_fixos = fixos["valor"].sum()

saldo = total_receitas - (total_despesas + total_fixos)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Receitas", f"R$ {total_receitas:,.2f}")
c2.metric("Despesas", f"R$ {total_despesas:,.2f}")
c3.metric("Fixos", f"R$ {total_fixos:,.2f}")
c4.metric("Saldo", f"R$ {saldo:,.2f}")

# ---------- TABELAS EDITÁVEIS ----------

st.header("📝 Editar Dados")

st.subheader("Receitas")
edit_r = st.data_editor(receitas, num_rows="dynamic")
save_csv(edit_r, "receitas.csv")

st.subheader("Despesas")
edit_d = st.data_editor(despesas, num_rows="dynamic")
save_csv(edit_d, "despesas.csv")
