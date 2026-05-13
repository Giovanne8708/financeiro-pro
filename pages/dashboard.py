python
import streamlit as st
from database import cursor

usuario = st.session_state.usuario

st.title("📊 Dashboard")

cursor.execute(
    "SELECT SUM(valor) FROM gastos WHERE usuario=?",
    (usuario,)
)

total_gastos = cursor.fetchone()[0] or 0

c1, c2 = st.columns(2)

c1.metric(
    "💸 Gastos",
    f"R$ {total_gastos:,.2f}"
)

c2.metric(
    "📈 Saúde Financeira",
    "Boa"
)


---