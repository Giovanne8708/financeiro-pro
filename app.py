Financeiro PRO — Versão Ultra

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Financeiro PRO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# CSS PREMIUM
# =====================================================
st.markdown("""
<style>

.stApp {
    background: #0b0f19;
    color: white;
}

.block-container {
    padding-top: 1rem;
}

.main-card {
    background: linear-gradient(145deg, #121826, #161d2e);
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 0 20px rgba(0,0,0,0.2);
}

.metric-card {
    background: #141b2d;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.06);
}

.alert-danger {
    background: rgba(255, 59, 48, 0.15);
    border: 1px solid #ff3b30;
    padding: 15px;
    border-radius: 14px;
    margin-bottom: 12px;
}

.alert-warning {
    background: rgba(255, 149, 0, 0.12);
    border: 1px solid #ff9500;
    padding: 15px;
    border-radius: 14px;
    margin-bottom: 12px;
}

.alert-success {
    background: rgba(52, 199, 89, 0.12);
    border: 1px solid #34c759;
    padding: 15px;
    border-radius: 14px;
    margin-bottom: 12px;
}

[data-testid="stMetricValue"] {
    font-size: 1.8rem;
    color: #00e0b8;
}

.stButton>button {
    border-radius: 12px;
    background: #00d4aa;
    color: black;
    border: none;
    font-weight: 700;
    height: 48px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE CSV
# =====================================================
ARQUIVOS = {
    "receitas.csv": ["data", "descricao", "valor", "conta"],
    "despesas.csv": ["data", "categoria", "descricao", "valor", "conta", "paga", "tipo"],
    "cartoes.csv": ["cartao", "limite", "fechamento", "vencimento"],
    "parcelamentos.csv": [
        "descricao",
        "cartao",
        "valor_total",
        "valor_parcela",
        "parcela_atual",
        "total_parcelas",
        "data"
    ],
    "investimentos.csv": ["data", "ativo", "tipo", "valor"],
    "patrimonio.csv": ["inter", "itau", "salario", "extra"],
    "fixos.csv": ["descricao", "valor", "dia", "categoria"]
}


def criar_banco():
    for arq, cols in ARQUIVOS.items():
        if not Path(arq).exists():
            pd.DataFrame(columns=cols).to_csv(arq, index=False)


criar_banco()


# =====================================================
# LOAD
# =====================================================
def carregar(nome):
    try:
        df = pd.read_csv(nome)

        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")

        return df
    except:
        return pd.DataFrame(columns=ARQUIVOS[nome])


receitas = carregar("receitas.csv")
despesas = carregar("despesas.csv")
cartoes = carregar("cartoes.csv")
parcelamentos = carregar("parcelamentos.csv")
investimentos = carregar("investimentos.csv")
patrimonio = carregar("patrimonio.csv")
fixos = carregar("fixos.csv")


# =====================================================
# VARIÁVEIS
# =====================================================
hoje = datetime.now()
mes = hoje.month
ano = hoje.year


# =====================================================
# PATRIMÔNIO
# =====================================================
if patrimonio.empty:
    patrimonio = pd.DataFrame([[0, 0, 0, 0]], columns=ARQUIVOS["patrimonio.csv"])

saldo_inter = float(patrimonio.iloc[0]["inter"])
saldo_itau = float(patrimonio.iloc[0]["itau"])
salario = float(patrimonio.iloc[0]["salario"])
renda_extra = float(patrimonio.iloc[0]["extra"])


# =====================================================
# FILTROS MÊS
# =====================================================
despesas_mes = despesas[
    (despesas["data"].dt.month == mes)
    & (despesas["data"].dt.year == ano)
]

receitas_mes = receitas[
    (receitas["data"].dt.month == mes)
    & (receitas["data"].dt.year == ano)
]


# =====================================================
# CÁLCULOS INTELIGENTES
# =====================================================
receita_total = receitas_mes["valor"].sum() + salario + renda_extra

gastos_total = despesas_mes["valor"].sum()

saldo_real = receita_total - gastos_total + saldo_inter + saldo_itau

comprometimento = (
    (gastos_total / receita_total) * 100
    if receita_total > 0 else 0
)

fatura_cartao = despesas_mes[
    despesas_mes["conta"].astype(str).str.contains("Cartão", na=False)
]["valor"].sum()

invest_total = investimentos["valor"].sum()

patrimonio_total = (
    saldo_inter
    + saldo_itau
    + invest_total
)

# =====================================================
# ALERTAS
# =====================================================
alertas = []

if comprometimento >= 70:
    alertas.append((
        "warning",
        f"⚠️ Você já comprometeu {comprometimento:.1f}% da sua renda este mês."
    ))

if comprometimento >= 90:
    alertas.append((
        "danger",
        "🚨 Seu orçamento está entrando em zona crítica."
    ))

# ALERTA CARTÃO
for _, row in cartoes.iterrows():

    nome = row["cartao"]
    limite = float(row["limite"])

    uso = despesas_mes[
        despesas_mes["conta"] == f"Cartão {nome}"
    ]["valor"].sum()

    if limite > 0:
        pct = (uso / limite) * 100

        if pct >= 70:
            alertas.append((
                "warning",
                f"💳 O cartão {nome} já consumiu {pct:.1f}% do limite."
            ))

# PREVISÃO
media_diaria = gastos_total / hoje.day if hoje.day > 0 else 0
previsao_final = media_diaria * 30

if previsao_final > receita_total:
    alertas.append((
        "danger",
        "📉 Se continuar nesse ritmo, você fechará o mês negativo."
    ))

# =====================================================
# MENU
# =====================================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "Home"

menu = st.columns(5)

botoes = [
    ("🏠 Home", "Home"),
    ("💳 Cartões", "Cartoes"),
    ("📊 Inteligência", "Analise"),
    ("📈 Investimentos", "Investimentos"),
    ("🏦 Patrimônio", "Patrimonio")
]

for col, item in zip(menu, botoes):
    nome, valor = item
    if col.button(nome):
        st.session_state.pagina = valor

st.divider()

# =====================================================
# HOME
# =====================================================
if st.session_state.pagina == "Home":

    st.title("🏦 Financeiro PRO")
    st.caption("Seu assistente financeiro pessoal inteligente")

    # ALERTAS
    for tipo, texto in alertas:

        if tipo == "danger":
            st.markdown(
                f'<div class="alert-danger">{texto}</div>',
                unsafe_allow_html=True
            )

        elif tipo == "warning":
            st.markdown(
                f'<div class="alert-warning">{texto}</div>',
                unsafe_allow_html=True
            )

        else:
            st.markdown(
                f'<div class="alert-success">{texto}</div>',
                unsafe_allow_html=True
            )

    # CARDS
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "💰 Saldo Real",
        f"R$ {saldo_real:,.2f}"
    )

    c2.metric(
        "💳 Fatura Atual",
        f"R$ {fatura_cartao:,.2f}"
    )

    c3.metric(
        "📉 Salário Comprometido",
        f"{comprometimento:.1f}%"
    )

    c4.metric(
        "📦 Parcelamentos",
        f"{len(parcelamentos)} ativos"
    )

    c5.metric(
        "🏦 Patrimônio",
        f"R$ {patrimonio_total:,.2f}"
    )

    st.divider()

    esquerda, direita = st.columns([2, 1])

    # =====================================================
    # LANÇAMENTO RÁPIDO
    # =====================================================
    with esquerda:

        st.subheader("⚡ Lançamento Inteligente")

        with st.form("lancamento"):

            col1, col2 = st.columns(2)

            tipo = col1.selectbox(
                "Tipo",
                ["Despesa", "Receita"]
            )

            valor = col2.number_input(
                "Valor",
                min_value=0.0,
                step=10.0
            )

            descricao = st.text_input("Descrição")

            categoria = st.selectbox(
                "Categoria",
                [
                    "Alimentação",
                    "Moradia",
                    "Transporte",
                    "Lazer",
                    "Saúde",
                    "Fixo",
                    "Outros"
                ]
            )

            conta = st.selectbox(
                "Conta",
                ["Inter", "Itaú"] +
                [f"Cartão {x}" for x in cartoes["cartao"]]
            )

            parcelado = st.checkbox("Compra parcelada?")

            parcelas = 1

            if parcelado:
                parcelas = st.number_input(
                    "Quantidade de parcelas",
                    2,
                    48,
                    2
                )

            enviar = st.form_submit_button("Salvar")

            if enviar:

                if tipo == "Receita":

                    novo = pd.DataFrame([
                        [
                            hoje,
                            descricao,
                            valor,
                            conta
                        ]
                    ], columns=ARQUIVOS["receitas.csv"])

                    receitas = pd.concat([receitas, novo])
                    receitas.to_csv("receitas.csv", index=False)

                else:

                    if parcelado:

                        valor_parcela = valor / parcelas

                        for i in range(parcelas):

                            data_parcela = hoje + relativedelta(months=i)

                            nova = pd.DataFrame([
                                [
                                    data_parcela,
                                    categoria,
                                    f"{descricao} ({i+1}/{parcelas})",
                                    valor_parcela,
                                    conta,
                                    False,
                                    "Parcelado"
                                ]
                            ], columns=ARQUIVOS["despesas.csv"])

                            despesas = pd.concat([despesas, nova])

                            novo_parc = pd.DataFrame([
                                [
                                    descricao,
                                    conta,
                                    valor,
                                    valor_parcela,
                                    i+1,
                                    parcelas,
                                    data_parcela
                                ]
                            ], columns=ARQUIVOS["parcelamentos.csv"])

                            parcelamentos = pd.concat([
                                parcelamentos,
                                novo_parc
                            ])

                        parcelamentos.to_csv(
                            "parcelamentos.csv",
                            index=False
                        )

                    else:

                        nova = pd.DataFrame([
                            [
                                hoje,
                                categoria,
                                descricao,
                                valor,
                                conta,
                                False,
                                "Única"
                            ]
                        ], columns=ARQUIVOS["despesas.csv"])

                        despesas = pd.concat([despesas, nova])

                    despesas.to_csv("despesas.csv", index=False)

                st.success("Movimentação registrada com sucesso")
                st.rerun()

    # =====================================================
    # CONTAS
    # =====================================================
    with direita:

        st.subheader("🔔 Próximos Vencimentos")

        pendentes = despesas[
            despesas["paga"] == False
        ].sort_values("data")

        proximas = pendentes.head(5)

        if proximas.empty:
            st.success("Nenhuma conta pendente")

        for i, row in proximas.iterrows():

            st.markdown(
                f"""
                <div class='main-card'>
                <b>{row['descricao']}</b><br>
                R$ {row['valor']:,.2f}<br>
                {row['data'].date()}
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("Marcar Pago", key=f"pay{i}"):
                despesas.at[i, "paga"] = True
                despesas.to_csv("despesas.csv", index=False)
                st.rerun()

# =====================================================
# CARTÕES
# =====================================================
elif st.session_state.pagina == "Cartoes":

    st.title("💳 Gestão de Cartões")

    col_a, col_b = st.columns([1, 2])

    with col_a:

        st.subheader("Novo Cartão")

        with st.form("novo_cartao"):

            nome = st.text_input("Nome")
            limite = st.number_input("Limite")
            fechamento = st.number_input("Fechamento")
            vencimento = st.number_input("Vencimento")

            salvar = st.form_submit_button("Adicionar")

            if salvar:

                novo = pd.DataFrame([
                    [nome, limite, fechamento, vencimento]
                ], columns=ARQUIVOS["cartoes.csv"])

                cartoes = pd.concat([cartoes, novo])
                cartoes.to_csv("cartoes.csv", index=False)

                st.success("Cartão cadastrado")
                st.rerun()

    with col_b:

        for _, row in cartoes.iterrows():

            gasto = despesas_mes[
                despesas_mes["conta"] == f"Cartão {row['cartao']}"
            ]["valor"].sum()

            limite = float(row["limite"])
            disponivel = limite - gasto
            pct = (gasto / limite) * 100 if limite > 0 else 0

            st.markdown("---")

            c1, c2, c3 = st.columns(3)

            c1.metric(row["cartao"], f"R$ {gasto:,.2f}")
            c2.metric("Disponível", f"R$ {disponivel:,.2f}")
            c3.metric("Uso", f"{pct:.1f}%")

# =====================================================
# ANÁLISE
# =====================================================
elif st.session_state.pagina == "Analise":

    st.title("📊 Inteligência Financeira")

    if not despesas_mes.empty:

        categoria = despesas_mes.groupby("categoria")["valor"].sum().reset_index()

        fig = px.pie(
            categoria,
            names="categoria",
            values="valor",
            hole=0.6,
            title="Para onde está indo seu dinheiro"
        )

        st.plotly_chart(fig, use_container_width=True)

        diario = despesas_mes.groupby(
            despesas_mes["data"].dt.day
        )["valor"].sum().reset_index()

        fig2 = px.line(
            diario,
            x="data",
            y="valor",
            title="Evolução dos gastos"
        )

        st.plotly_chart(fig2, use_container_width=True)

        gasto_cartao = despesas_mes[
            despesas_mes["conta"].astype(str).str.contains("Cartão", na=False)
        ]["valor"].sum()

        gasto_debito = gastos_total - gasto_cartao

        c1, c2 = st.columns(2)

        c1.metric(
            "💳 Gasto no Cartão",
            f"R$ {gasto_cartao:,.2f}"
        )

        c2.metric(
            "🏦 Débito/Pix",
            f"R$ {gasto_debito:,.2f}"
        )

        st.info(
            f"Você já gastou {comprometimento:.1f}% da sua renda mensal."
        )

    else:
        st.warning("Sem dados suficientes")

# =====================================================
# INVESTIMENTOS
# =====================================================
elif st.session_state.pagina == "Investimentos":

    st.title("📈 Investimentos")

    col1, col2 = st.columns([1, 2])

    with col1:

        with st.form("invest"):

            ativo = st.text_input("Ativo")
            tipo = st.selectbox(
                "Tipo",
                ["Ações", "FIIs", "Tesouro", "Cripto", "Reserva"]
            )
            valor = st.number_input("Valor")

            salvar = st.form_submit_button("Registrar")

            if salvar:

                novo = pd.DataFrame([
                    [hoje, ativo, tipo, valor]
                ], columns=ARQUIVOS["investimentos.csv"])

                investimentos = pd.concat([
                    investimentos,
                    novo
                ])

                investimentos.to_csv(
                    "investimentos.csv",
                    index=False
                )

                st.success("Investimento registrado")
                st.rerun()

    with col2:

        if not investimentos.empty:

            grp = investimentos.groupby("tipo")["valor"].sum().reset_index()

            fig = px.pie(
                grp,
                names="tipo",
                values="valor",
                title="Distribuição da carteira"
            )

            st.plotly_chart(fig, use_container_width=True)

            st.metric(
                "Patrimônio Investido",
                f"R$ {invest_total:,.2f}"
            )

# =====================================================
# PATRIMÔNIO
# =====================================================
elif st.session_state.pagina == "Patrimonio":

    st.title("🏦 Patrimônio")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Inter", f"R$ {saldo_inter:,.2f}")
    c2.metric("Itaú", f"R$ {saldo_itau:,.2f}")
    c3.metric("Investimentos", f"R$ {invest_total:,.2f}")
    c4.metric("Patrimônio", f"R$ {patrimonio_total:,.2f}")

    st.divider()

    with st.form("pat_form"):

        col1, col2 = st.columns(2)

        inter = col1.number_input("Saldo Inter", value=saldo_inter)
        itau = col2.number_input("Saldo Itaú", value=saldo_itau)
        sal = col1.number_input("Salário", value=salario)
        extra = col2.number_input("Renda Extra", value=renda_extra)

        salvar = st.form_submit_button("Salvar")

        if salvar:

            novo = pd.DataFrame([
                [inter, itau, sal, extra]
            ], columns=ARQUIVOS["patrimonio.csv"])

            novo.to_csv("patrimonio.csv", index=False)

            st.success("Patrimônio atualizado")
            st.rerun()

MELHORIAS IMPLEMENTADAS

Interface dark premium estilo banco digital

Home inteligente com métricas automáticas

Sistema de alertas financeiros

Controle completo de cartões

Parcelamentos automáticos

Previsão financeira do mês

Gestão patrimonial

Controle de investimentos

Gráficos inteligentes

Arquitetura modular

Persistência em CSV

UX moderna estilo fintech

Menu horizontal

Cards premium

Indicadores automáticos

Assistente financeiro ativo


EXECUTAR

streamlit run financeiropro.py
