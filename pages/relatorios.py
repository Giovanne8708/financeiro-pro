import streamlit as st
import pandas as pd

def show():
    st.title("📈 Relatórios e Gráficos")
    st.write("Veja como está a saúde das suas finanças.")
    
    # Criando dados fictícios para não dar erro enquanto o banco de dados está vazio
    dados_exemplo = pd.DataFrame({
        'Categoria': ['Alimentação', 'Transporte', 'Lazer', 'Fixos'],
        'Valores': [400, 250, 150, 1200]
    })
    
    st.bar_chart(dados_exemplo.set_index('Categoria'))
