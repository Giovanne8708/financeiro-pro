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
# ESTILO
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #0E1117;
    color: white;
}

.block-container {
    padding-top: 2rem;
}

.stMetric {
    background: #161B22;
    border: 1px solid #30363D;
    padding: 15px;
    border-radius: 16px;
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

h1, h2, h3 {
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

USUARIO = "giovanne"
SENHA = "8708"

if not st.session_state.logado:

    st.title("🔐 Financeiro PRO")

    with st.form("login"):

        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        entrar = st.form_submit_button("Entrar")

        if entrar:

            if usuario == USUARIO and senha == SENHA:

                st.session_state.logado = True
                st.rerun()

            else:
                st.error("Usuário ou senha inválidos.")

    st.stop()

# =========================================================
# FUNÇÕES
# =========================================================

def criar_csv_se_nao_existir(file, cols):

    path = Path(file)

    if not path.exists():

        df = pd.DataFrame(columns=cols)
        df.to_csv(file, index=False)

    else:

        try:

            df = pd.read_csv(file)

            if list(df.columns) != cols:

                df = pd.DataFrame(columns=cols)
                df.to_csv(file, index=False)

        except:

            df = pd.DataFrame(columns=cols)
            df.to_csv(file, index=False)


def load_csv(file):

    return pd.read_csv(file)


def save_csv(df, file):

    df.to_csv(file, index=False)


def moeda(valor):

    return f"R$ {valor:,.2f}"


# =========================================================
# CRIAR BASES
# =========================================================

criar_csv_se_nao_existir(
    "receitas.csv",
    ["data", "categoria", "descricao", "valor"]
)

criar_csv_se_nao_existir(
    "despesas.csv",
    ["data", "categoria", "descricao", "valor"]
)

criar_csv_se_nao_existir(
    "fixos.csv",
    ["descricao", "valor"]
)

criar_csv_se_nao_existir(
    "investimentos.csv",
    [
        "ativo",
        "tipo",
        "quantidade",
        "preco_medio",
        "valor_atual"
    ]
)

# =========================================================
# CARREGAR BASES
# =========================================================

receitas = load_csv("receitas.csv")
despesas = load_csv("despesas.csv")
fixos = load_csv("fixos.csv")
investimentos = load_csv("investimentos.csv")

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
        "Investimentos",
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

    patrimonio = (
        investimentos["valor_atual"] *
        investimentos["quantidade"]
    ).sum()

    saldo = total_receitas - total_despesas - total_fixos

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("💰 Receitas", moeda(total_receitas))
    c2.metric("💸 Despesas", moeda(total_despesas))
    c3.metric("📌 Fixos", moeda(total_fixos))
    c4.metric("🏦 Saldo", moeda(saldo))
    c5.metric("📈 Investimentos", moeda(patrimonio))

    st.markdown("##")

    # =====================================================
    # PROJEÇÕES
    # =====================================================

    proj_6 = saldo * 6
    proj_12 = saldo * 12

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

        grafico = pd.DataFrame({
            "Tipo": [
                "Receitas",
                "Despesas",
                "Fixos",
                "Investimentos"
            ],
            "Valor": [
                total_receitas,
                total_despesas,
                total_fixos,
                patrimonio
            ]
        })

        fig = px.bar(
            grafico,
            x="Tipo",
            y="Valor",
            text_auto=True
        )

        fig.update_layout(
            template="plotly_dark",
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with g2:

        pizza = pd.DataFrame({
            "Categoria": [
                "Despesas",
                "Fixos",
                "Investimentos"
            ],
            "Valor": [
                total_despesas,
                total_fixos,
                patrimonio
            ]
        })

        fig2 = px.pie(
            pizza,
            names="Categoria",
            values="Valor",
            hole=0.5
        )

        fig2.update_layout(
            template="plotly_dark",
            height=450
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

    with st.form("receita", clear_on_submit=True):

        c1, c2 = st.columns(2)

        with c1:

            data = st.date_input(
                "Data",
                date.today()
            )

            categoria = st.selectbox(
                "Categoria",
                [
                    "Salário",
                    "Freelance",
                    "Investimentos",
                    "Extra",
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

        salvar = st.form_submit_button(
            "Adicionar Receita"
        )

        if salvar:

            nova_linha = pd.DataFrame([{
                "data": data,
                "categoria": categoria,
                "descricao": descricao,
                "valor": valor
            }])

            receitas = pd.concat(
                [receitas, nova_linha],
                ignore_index=True
            )

            save_csv(receitas, "receitas.csv")

            st.success("Receita adicionada!")
            st.rerun()

    st.markdown("##")

    receitas_edit = st.data_editor(
        receitas,
        use_container_width=True,
        num_rows="dynamic"
    )

    save_csv(receitas_edit, "receitas.csv")

# =========================================================
# DESPESAS
# =========================================================

elif pagina == "Despesas":

    st.title("💸 Despesas")

    with st.form("despesa", clear_on_submit=True):

        c1, c2 = st.columns(2)

        with c1:

            data = st.date_input(
                "Data",
                date.today()
            )

            categoria = st.selectbox(
                "Categoria",
                [
                    "Alimentação",
                    "Saúde",
                    "Lazer",
                    "Transporte",
                    "Moradia",
                    "Educação",
                    "Compras",
                    "Viagem",
                    "Streaming",
                    "Internet",
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

        salvar = st.form_submit_button(
            "Adicionar Despesa"
        )

        if salvar:

            nova_linha = pd.DataFrame([{
                "data": data,
                "categoria": categoria,
                "descricao": descricao,
                "valor": valor
            }])

            despesas = pd.concat(
                [despesas, nova_linha],
                ignore_index=True
            )

            save_csv(despesas, "despesas.csv")

            st.success("Despesa adicionada!")
            st.rerun()

    st.markdown("##")

    despesas_edit = st.data_editor(
        despesas,
        use_container_width=True,
        num_rows="dynamic"
    )

    save_csv(despesas_edit, "despesas.csv")

# =========================================================
# FIXOS
# =========================================================

elif pagina == "Fixos":

    st.title("📌 Gastos Fixos")

    with st.form("fixo", clear_on_submit=True):

        descricao = st.text_input("Descrição")

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            format="%.2f"
        )

        salvar = st.form_submit_button(
            "Adicionar"
        )

        if salvar:

            nova_linha = pd.DataFrame([{
                "descricao": descricao,
                "valor": valor
            }])

            fixos = pd.concat(
                [fixos, nova_linha],
                ignore_index=True
            )

            save_csv(fixos, "fixos.csv")

            st.success("Fixo adicionado!")
            st.rerun()

    st.markdown("##")

    fixos_edit = st.data_editor(
        fixos,
        use_container_width=True,
        num_rows="dynamic"
    )

    save_csv(fixos_edit, "fixos.csv")

# =========================================================
# INVESTIMENTOS
# =========================================================

elif pagina == "Investimentos":

    st.title("📈 Investimentos")

    with st.form("investimento", clear_on_submit=True):

        c1, c2 = st.columns(2)

        with c1:

            ativo = st.text_input("Nome do Ativo")

            tipo = st.selectbox(
                "Tipo",
                [
                    "Ações",
                    "ETF",
                    "Crypto",
                    "FII",
                    "Renda Fixa",
                    "Tesouro",
                    "Dólar",
                    "Outros"
                ]
            )

            quantidade = st.number_input(
                "Quantidade",
                min_value=0.0,
                format="%.2f"
            )

        with c2:

            preco_medio = st.number_input(
                "Preço Médio",
                min_value=0.0,
                format="%.2f"
            )

            valor_atual = st.number_input(
                "Valor Atual",
                min_value=0.0,
                format="%.2f"
            )

        salvar = st.form_submit_button(
            "Adicionar Investimento"
        )

        if salvar:

            nova_linha = pd.DataFrame([{
                "ativo": ativo,
                "tipo": tipo,
                "quantidade": quantidade,
                "preco_medio": preco_medio,
                "valor_atual": valor_atual
            }])

            investimentos = pd.concat(
                [investimentos, nova_linha],
                ignore_index=True
            )

            save_csv(
                investimentos,
                "investimentos.csv"
            )

            st.success("Investimento adicionado!")
            st.rerun()

    st.markdown("##")

    if not investimentos.empty:

        investimentos["total_investido"] = (
            investimentos["quantidade"] *
            investimentos["preco_medio"]
        )

        investimentos["valor_total"] = (
            investimentos["quantidade"] *
            investimentos["valor_atual"]
        )

        investimentos["lucro"] = (
            investimentos["valor_total"] -
            investimentos["total_investido"]
        )

    st.subheader("Carteira de Investimentos")

    investimentos_edit = st.data_editor(
        investimentos,
        use_container_width=True,
        num_rows="dynamic"
    )

    save_csv(
        investimentos_edit[
            [
                "ativo",
                "tipo",
                "quantidade",
                "preco_medio",
                "valor_atual"
            ]
        ],
        "investimentos.csv"
    )

    st.markdown("##")

    # =====================================================
    # GRÁFICOS INVESTIMENTOS
    # =====================================================

    if not investimentos.empty:

        g1, g2 = st.columns(2)

        with g1:

            fig = px.pie(
                investimentos,
                names="tipo",
                values="valor_total",
                hole=0.5
            )

            fig.update_layout(
                template="plotly_dark",
                height=450
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with g2:

            fig2 = px.bar(
                investimentos,
                x="ativo",
                y="lucro",
                text_auto=True
            )

            fig2.update_layout(
                template="plotly_dark",
                height=450
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

    st.markdown("##")

    # =====================================================
    # SIMULADOR
    # =====================================================

    st.subheader("🚀 Simulador de Juros Compostos")

    c1, c2, c3 = st.columns(3)

    with c1:

        aporte = st.number_input(
            "Aporte Mensal",
            min_value=0.0,
            value=500.0
        )

    with c2:

        juros = st.number_input(
            "Juros Anual (%)",
            min_value=0.0,
            value=12.0
        )

    with c3:

        anos = st.number_input(
            "Anos",
            min_value=1,
            value=10
        )

    taxa = juros / 100 / 12

    meses = anos * 12

    valor_futuro = 0

    evolucao = []

    for mes in range(meses):

        valor_futuro = (
            valor_futuro * (1 + taxa)
        ) + aporte

        evolucao.append(valor_futuro)

    st.success(
        f"💰 Patrimônio Futuro: {moeda(valor_futuro)}"
    )

    grafico = pd.DataFrame({
        "Mês": list(range(1, meses + 1)),
        "Valor": evolucao
    })

    fig3 = go.Figure()

    fig3.add_trace(
        go.Scatter(
            x=grafico["Mês"],
            y=grafico["Valor"],
            mode="lines"
        )
    )

    fig3.update_layout(
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

# =========================================================
# RELATÓRIOS
# =========================================================

elif pagina == "Relatórios":

    st.title("📑 Relatórios")

    total_receitas = receitas["valor"].sum()
    total_despesas = despesas["valor"].sum()
    total_fixos = fixos["valor"].sum()

    patrimonio = (
        investimentos["valor_atual"] *
        investimentos["quantidade"]
    ).sum()

    saldo = (
        total_receitas -
        total_despesas -
        total_fixos
    )

    relatorio = pd.DataFrame({

        "Indicador": [
            "Receitas",
            "Despesas",
            "Fixos",
            "Saldo",
            "Investimentos"
        ],

        "Valor": [
            total_receitas,
            total_despesas,
            total_fixos,
            saldo,
            patrimonio
        ]
    })

    st.dataframe(
        relatorio,
        use_container_width=True
    )

    st.markdown("##")

    csv = relatorio.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Baixar Relatório CSV",
        data=csv,
        file_name="relatorio_financeiro.csv",
        mime="text/csv"
    )
