python
import streamlit as st
from database import cursor, conn
from datetime import datetime

usuario = st.session_state.usuario

st.title("💸 Gastos")

with st.form("gasto_form"):

    desc = st.text_input("Descrição")

    valor = st.number_input(
        "Valor",
        min_value=0.0
    )

    categoria = st.selectbox(
        "Categoria",
        [
            "Alimentação",
            "Transporte",
            "Lazer",
            "Saúde"
        ]
    )

    enviar = st.form_submit_button(
        "Salvar"
    )

if enviar:

    cursor.execute(
        """
        INSERT INTO gastos(
            usuario,
            descricao,
            categoria,
            valor,
            data
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            usuario,
            desc,
            categoria,
            valor,
            datetime.now().strftime("%d/%m/%Y")
        )
    )

    conn.commit()

    st.toast("✅ Gasto salvo")


---