import streamlit as st

def show():
    st.title("📊 Painel Financeiro")
    st.write("Bem-vindo ao seu controle de finanças.")
    
    # Exemplo de resumo
    col1, col2, col3 = st.columns(3)
    col1.metric("Entradas", "R$ 0,00")
    col2.metric("Saídas", "R$ 0,00")
    col3.metric("Reserva", "R$ 0,00")
