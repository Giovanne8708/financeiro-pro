import streamlit as st

def show():
    st.title("💸 Lançar Gastos")
    st.write("Use esta tela para registrar suas saídas.")
    
    with st.form("form_gastos"):
        descricao = st.text_input("Descrição do gasto")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Fixos", "Outros"])
        data = st.date_input("Data")
        
        enviar = st.form_submit_button("Salvar Gasto")
        
        if enviar:
            st.success(f"Gasto de R$ {valor:.2f} em '{descricao}' registrado! (Simulação)")
