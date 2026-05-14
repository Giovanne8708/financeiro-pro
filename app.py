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
# CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #0E1117;
    color: white;
}

.block-container {
    padding-top: 1.5rem;
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

def criar_csv(file, cols):

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

@st.cache_data
def load_csv(file):

    return pd.read_csv(file)

def save_csv(df, file):

    df.to_csv(file, index=False)

    load_csv.clear()

def moeda(valor):

    return f"R$ {valor:,.2f}"

# =========================================================
# CRIAR BASES
# =========================================================

criar_csv(
    "receitas.csv",
    ["data", "categoria", "descricao", "valor"]
)

criar_csv(
    "despesas.csv",
    ["data", "categoria", "descricao", "valor"]
)

criar_csv(
    "fixos.csv",
    [
        "descricao",
        "valor_parcela",
        "parcelas_total",
        "parcelas_pagas"
    ]
)

criar_csv(
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
# LOAD
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

    total_fixos = (
        fixos["valor_parcela"] *
        (
            fixos["parcelas_total"] -
            fixos["parcelas_pagas"]
        )
    ).sum()

    patrimonio = (
        investimentos["valor_atual"] *
        investimentos["quantidade"]
    ).sum()

    saldo = (
        total_receitas -
        total_despesas -
        total_fixos
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "💰 Receitas",
        moeda(total_receitas)
    )

    c2.metric(
        "💸 Despesas",
        moeda(total_despesas)
    )

    c3.metric(
        "📌 Dívidas/Fixos",
        moeda(total_fixos)
    )

    c4.metric(
        "🏦 Saldo",
        moeda(saldo)
    )

    c5.metric(
        "📈 Patrimônio",
        moeda(patrimonio)
    )

    st.markdown("##")

    # =====================================================
    # PROJEÇÕES
    # =====================================================

    p1, p2 = st.columns(2)

    proj_6 = saldo * 6
    proj_12 = saldo * 12

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

            "Categoria": [
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
            x="Categoria",
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

    with st.form("receitas_form", clear_on_submit=True):

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

            nova = pd.DataFrame([{
                "data": data,
                "categoria": categoria,
                "descricao": descricao,
                "valor": valor
            }])

            receitas = pd.concat(
                [receitas, nova],
                ignore_index=True
            )

            save_csv(receitas, "receitas.csv")

            st.success("Receita adicionada!")

    st.markdown("##")

    edit = st.data_editor(
        receitas,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("💾 Salvar Receitas"):

        save_csv(edit, "receitas.csv")
        st.success("Receitas atualizadas!")

# =========================================================
# DESPESAS
# =========================================================

elif pagina == "Despesas":

    st.title("💸 Despesas")

    with st.form("despesas_form", clear_on_submit=True):

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
                    "Internet",
                    "Streaming",
                    "Viagem",
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

            nova = pd.DataFrame([{
                "data": data,
                "categoria": categoria,
                "descricao": descricao,
                "valor": valor
            }])

            despesas = pd.concat(
                [despesas, nova],
                ignore_index=True
            )

            save_csv(despesas, "despesas.csv")

            st.success("Despesa adicionada!")

    st.markdown("##")

    edit = st.data_editor(
        despesas,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("💾 Salvar Despesas"):

        save_csv(edit, "despesas.csv")
        st.success("Despesas atualizadas!")

# =========================================================
# FIXOS / PARCELAS
# =========================================================

elif pagina == "Fixos":

    st.title("📌 Parcelas e Fixos")

    with st.form("fixos_form", clear_on_submit=True):

        descricao = st.text_input(
            "Descrição"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            valor = st.number_input(
                "Valor da Parcela",
                min_value=0.0,
                format="%.2f"
            )

        with c2:

            parcelas_total = st.number_input(
                "Parcelas Totais",
                min_value=1,
                step=1
            )

        with c3:

            parcelas_pagas = st.number_input(
                "Parcelas Pagas",
                min_value=0,
                step=1
            )

        salvar = st.form_submit_button(
            "Adicionar"
        )

        if salvar:

            nova = pd.DataFrame([{

                "descricao": descricao,
                "valor_parcela": valor,
                "parcelas_total": parcelas_total,
                "parcelas_pagas": parcelas_pagas

            }])

            fixos = pd.concat(
                [fixos, nova],
                ignore_index=True
            )

            save_csv(fixos, "fixos.csv")

            st.success("Parcela adicionada!")

    st.markdown("##")

    if not fixos.empty:

        fixos["faltam"] = (
            fixos["parcelas_total"] -
            fixos["parcelas_pagas"]
        )

        fixos["valor_restante"] = (
            fixos["faltam"] *
            fixos["valor_parcela"]
        )

        st.subheader("📋 Controle de Parcelas")

        for i, row in fixos.iterrows():

            progresso = (
                row["parcelas_pagas"] /
                row["parcelas_total"]
            )

            st.markdown(f"### {row['descricao']}")

            st.progress(float(progresso))

            c1, c2, c3 = st.columns(3)

            c1.info(
                f"Parcelas: "
                f"{int(row['parcelas_pagas'])}/"
                f"{int(row['parcelas_total'])}"
            )

            c2.warning(
                f"Faltam: "
                f"{int(row['faltam'])}"
            )

            c3.error(
                f"Restante: "
                f"{moeda(row['valor_restante'])}"
            )

        st.markdown("##")

    edit = st.data_editor(
        fixos,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("💾 Salvar Parcelas"):

        save_csv(
            edit[
                [
                    "descricao",
                    "valor_parcela",
                    "parcelas_total",
                    "parcelas_pagas"
                ]
            ],
            "fixos.csv"
        )

        st.success("Parcelas atualizadas!")

# =========================================================
# INVESTIMENTOS
# =========================================================

elif pagina == "Investimentos":

    st.title("📈 Investimentos")

    with st.form("invest_form", clear_on_submit=True):

        c1, c2 = st.columns(2)

        with c1:

            ativo = st.text_input(
                "Ativo"
            )

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

            nova = pd.DataFrame([{

                "ativo": ativo,
                "tipo": tipo,
                "quantidade": quantidade,
                "preco_medio": preco_medio,
                "valor_atual": valor_atual

            }])

            investimentos = pd.concat(
                [investimentos, nova],
                ignore_index=True
            )

            save_csv(
                investimentos,
                "investimentos.csv"
            )

            st.success(
                "Investimento adicionado!"
            )

    st.markdown("##")

    if not investimentos.empty:

        investimentos["investido"] = (
            investimentos["quantidade"] *
            investimentos["preco_medio"]
        )

        investimentos["patrimonio"] = (
            investimentos["quantidade"] *
            investimentos["valor_atual"]
        )

        investimentos["lucro"] = (
            investimentos["patrimonio"] -
            investimentos["investido"]
        )

    edit = st.data_editor(
        investimentos,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("💾 Salvar Investimentos"):

        save_csv(
            edit[
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

        st.success("Investimentos atualizados!")

    st.markdown("##")

    if not investimentos.empty:

        g1, g2 = st.columns(2)

        with g1:

            fig = px.pie(
                investimentos,
                names="tipo",
                values="patrimonio",
                hole=0.5
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

            fig2 = px.bar(
                investimentos,
                x="ativo",
                y="lucro",
                text_auto=True
            )

            fig2.update_layout(
                template="plotly_dark",
                height=400
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

    st.markdown("##")

    # =====================================================
    # SIMULADOR
    # =====================================================

    st.subheader(
        "🚀 Simulador de Juros Compostos"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        aporte = st.number_input(
            "Aporte Mensal",
            value=500.0
        )

    with c2:

        juros = st.number_input(
            "Juros Anual (%)",
            value=12.0
        )

    with c3:

        anos = st.number_input(
            "Anos",
            value=10
        )

    taxa = juros / 100 / 12

    meses = anos * 12

    valor = 0

    historico = []

    for mes in range(meses):

        valor = (
            valor * (1 + taxa)
        ) + aporte

        historico.append(valor)

    st.success(
        f"💰 Patrimônio Futuro: "
        f"{moeda(valor)}"
    )

    grafico = pd.DataFrame({

        "Mês": list(range(1, meses + 1)),
        "Valor": historico

    })

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(
            x=grafico["Mês"],
            y=grafico["Valor"],
            mode="lines"
        )

    )

    fig.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# RELATÓRIOS
# =========================================================

elif pagina == "Relatórios":

    st.title("📑 Relatórios")

    total_receitas = receitas["valor"].sum()

    total_despesas = despesas["valor"].sum()

    total_fixos = (
        fixos["valor_parcela"] *
        (
            fixos["parcelas_total"] -
            fixos["parcelas_pagas"]
        )
    ).sum()

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
            "Patrimônio"
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

    csv = relatorio.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Baixar Relatório CSV",
        data=csv,
        file_name="relatorio.csv",
        mime="text/csv"
    )
