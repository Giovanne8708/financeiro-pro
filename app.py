import streamlit as st
import database

# Inicializa o banco de dados ao abrir
database.init_db()

st.set_page_config(page_title="Finances and Economy", layout="wide")

st.sidebar.title("Navegação")
page = st.sidebar.radio("Ir para:", ["Dashboard", "Gastos", "Relatórios"])

if page == "Dashboard":
    from pages import dashboard
    dashboard.show()
elif page == "Gastos":
    st.title("💸 Lançar Gastos")
    st.info("Área de lançamentos em desenvolvimento.")
elif page == "Relatórios":
    st.title("📈 Relatórios")
    st.info("Área de gráficos em desenvolvimento.")
