import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Financeiro PRO",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CSS PROFISSIONAL
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #0E1117;
    color: white;
}

.stMetric {
    background: #161B22;
    padding: 15px;
    border-radius: 14px;
    border: 1px solid #30363D;
}

div[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

.block-container {
    padding-top: 2rem;
}

h1, h2, h3 {
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SEGURANÇA SIMPLES
# =========================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

USUARIO = "giovanne"
SENHA = "8708"

if not st.session_state.logado:

    st.title("🔐 Login Financeiro PRO")

    with st.form("login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        entrar = st.form_submit_button("Entrar")

        if entrar:
            if usuario == USUARIO and senha == SENHA:
                st.session_state.logado = True
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

    st.stop()

# =========================================================
# FUNÇÕES
# =========================================================

def load_csv(file, cols):

    path = Path(file)

    if path.exists():
        try:
            return pd.read_csv(file)
        except:
            pass

    df = pd.DataFrame(columns=cols)
    df.to_csv(file, index=False)
    return df


def save_csv(df, file):
    df.to_csv(file, index=False)


def moeda(valor):
    return f"R$ {valor:,.2f}"


# =========================================================
# BASES
# =========================================================

receitas = load_csv(
    "receitas.csv",
    ["data", "categoria", "descricao", "valor"]
)

despesas = load_csv(
    "despesas.csv",
    ["data", "categoria", "descricao", "valor"]
)

fixos = load_csv(
    "fixos.csv",
    ["descricao", "valor"]
)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("💼 Financeiro PRO")

pagina = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Receitas",
        "Despesas",
        "Fixos",
        "Relatórios"
    ]
)

st.sidebar.markdown("---")

if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.rerun()

# =========================================================
# DASHBOARD
# =========================================================

if pagina == "Dashboard":

    st.title("📊 Dashboard Financeiro")

    total_receitas = receitas["valor"].sum()
    total_despesas = despesas["valor"].sum()
    total_fixos = fixos["valor"].sum()

    saldo = total_receitas - total_despesas - total_fixos

    # =====================================================
    # MÉTRICAS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "💰 Receitas",
        moeda(total_receitas)
    )

    c2.metric(
        "💸 Despesas",
        moeda(total_despesas)
    )

    c3.metric(
        "📌 Fixos",
        moeda(total_fixos)
    )

    c4.metric(
        "🏦 Saldo",
        moeda(saldo)
    )

    st.markdown("##")

    # =====================================================
    # PROJEÇÃO
    # =====================================================

    economia_mensal = saldo

    proj_6 = economia_mensal * 6
    proj_12 = economia_mensal * 12

    p1, p2 = st.columns(2)

    p1.success(
        f"📈 Projeção 6 meses: {moeda(proj_6)}"
    )

    p2.success(
        f"🚀 Projeção 12 meses: {moeda(proj_12)}"
    )

    st.markdown("##")

    # =====================================================
    # GRÁFICOS
    # =====================================================

    g1, g2 = st.columns(2)

    with g1:

        st.subheader("Receitas vs Despesas")

        grafico_barra = pd.DataFrame({
            "Tipo": ["Receitas", "Despesas", "Fixos"],
            "Valor": [
                total_receitas,
                total_despesas,
                total_fixos
            ]
        })

        fig = px.bar(
            grafico_barra,
            x="Tipo",
            y="Valor",
            text_auto=True
        )

        fig.update_layout(
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with g2:

        st.subheader("Distribuição de Gastos")

        pizza = pd.DataFrame({
            "Tipo": ["Despesas", "Fixos"],
            "Valor": [total_despesas, total_fixos]
        })

        fig2 = px.pie(
            pizza,
            names="Tipo",
            values="Valor",
            hole=0.5
        )

        fig2.update_layout(
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

# =========================================================
# RECEITAS
# =========================================================

elif pagina == "Receitas":

    st.title("💰 Receitas")

    with st.form("form_receita", clear_on_submit=True):

        c1, c2 = st.columns(2)

        with c1:
            data = st.date_input("Data", date.today())

            categoria = st.selectbox(
                "Categoria",
                [
                    "Salário",
                    "Freelance",
                    "Investimento",
                    "Outros"
                ]
            )

        with c2:
            descricao = st.text_input("Descrição")

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                format="%.2f"
            )

        salvar = st.form_submit_button("Adicionar Receita")

        if salvar:

            if descricao and valor > 0:

                receitas.loc[len(receitas)] = [
                    data,
                    categoria,
                    descricao,
                    valor
                ]

                save_csv(receitas, "receitas.csv")

                st.success("Receita adicionada com sucesso!")

                st.rerun()

            else:
                st.warning("Preencha os campos corretamente.")

    st.markdown("##")

    st.subheader("Editar Receitas")

    edit_r = st.data_editor(
        receitas,
        num_rows="dynamic",
        use_container_width=True
    )

    save_csv(edit_r, "receitas.csv")

# =========================================================
# DESPESAS
# =========================================================

elif pagina == "Despesas":

    st.title("💸 Despesas")

    with st.form("form_despesa", clear_on_submit=True):

        c1, c2 = st.columns(2)

        with c1:
            data = st.date_input("Data", date.today())

            categoria = st.selectbox(
                "Categoria",
                [
                    "Alimentação",
                    "Transporte",
                    "Moradia",
                    "Lazer",
                    "Saúde",
                    "Outros"
                ]
            )

        with c2:
            descricao = st.text_input("Descrição")

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                format="%.2f"
            )

        salvar = st.form_submit_button("Adicionar Despesa")

        if salvar:

            if descricao and valor > 0:

                despesas.loc[len(despesas)] = [
                    data,
                    categoria,
                    descricao,
                    valor
                ]

                save_csv(despesas, "despesas.csv")

                st.success("Despesa adicionada!")

                st.rerun()

            else:
                st.warning("Preencha os campos corretamente.")

    st.markdown("##")

    st.subheader("Editar Despesas")

    edit_d = st.data_editor(
        despesas,
        num_rows="dynamic",
        use_container_width=True
    )

    save_csv(edit_d, "despesas.csv")

# =========================================================
# FIXOS
# =========================================================

elif pagina == "Fixos":

    st.title("📌 Compromissos Fixos")

    with st.form("form_fixo", clear_on_submit=True):

        descricao = st.text_input("Descrição")

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            format="%.2f"
        )

        salvar = st.form_submit_button("Adicionar")

        if salvar:

            if descricao and valor > 0:

                fixos.loc[len(fixos)] = [
                    descricao,
                    valor
                ]

                save_csv(fixos, "fixos.csv")

                st.success("Fixo adicionado!")

                st.rerun()

            else:
                st.warning("Preencha corretamente.")

    st.markdown("##")

    st.subheader("Editar Fixos")

    edit_f = st.data_editor(
        fixos,
        num_rows="dynamic",
        use_container_width=True
    )

    save_csv(edit_f, "fixos.csv")

# =========================================================
# RELATÓRIOS
# =========================================================

elif pagina == "Relatórios":

    st.title("📑 Relatórios Financeiros")

    total_receitas = receitas["valor"].sum()
    total_despesas = despesas["valor"].sum()
    total_fixos = fixos["valor"].sum()

    saldo = total_receitas - total_despesas - total_fixos

    relatorio = pd.DataFrame({
        "Indicador": [
            "Receitas",
            "Despesas",
            "Fixos",
            "Saldo"
        ],
        "Valor": [
            total_receitas,
            total_despesas,
            total_fixos,
            saldo
        ]
    })

    st.dataframe(
        relatorio,
        use_container_width=True
    )

    # =====================================================
    # LINHA DE EVOLUÇÃO
    # =====================================================

    if not receitas.empty:

        receitas["data"] = pd.to_datetime(receitas["data"])

        evolucao = receitas.groupby(
            receitas["data"].dt.strftime("%Y-%m")
        )["valor"].sum().reset_index()

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=evolucao["data"],
                y=evolucao["valor"],
                mode="lines+markers",
                name="Receitas"
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=500,
            title="Evolução Financeira"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =====================================================
    # EXPORTAÇÃO
    # =====================================================

    st.markdown("##")

    csv = relatorio.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Baixar Relatório CSV",
        data=csv,
        file_name="relatorio_financeiro.csv",
        mime="text/csv"
    )
