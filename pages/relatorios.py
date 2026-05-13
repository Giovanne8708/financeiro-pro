python
import streamlit as st
import pandas as pd
import plotly.express as px
from database import cursor

usuario = st.session_state.usuario

st.title("📈 Relatórios")

cursor.execute(
    "SELECT categoria, valor FROM gastos WHERE usuario=?",
    (usuario,)
)

resultado = cursor.fetchall()

if resultado:

    df = pd.DataFrame(
        resultado,
        columns=['cat', 'valor']
    )

    categoria_df = df.groupby(
        'cat'
    )['valor'].sum().reset_index()

    # =====================================
    # PIZZA PREMIUM
    # =====================================

    fig = px.pie(
        categoria_df,
        names='cat',
        values='valor',
        hole=0.72
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )

    fig.update_layout(
        paper_bgcolor='#0f172a',
        plot_bgcolor='#0f172a',
        font_color='white',
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================
    # BARRAS PREMIUM
    # =====================================

    fig2 = px.bar(
        categoria_df,
        x='cat',
        y='valor',
        text_auto=True
    )

    fig2.update_layout(
        paper_bgcolor='#0f172a',
        plot_bgcolor='#0f172a',
        font_color='white'
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

else:

    st.info("Nenhum gasto registrado")


---
