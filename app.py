import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from dateutil.relativedelta import relativedelta
from pathlib import Path

# ---------- CONFIGURAÇÃO E ESTILO ----------
st.set_page_config(page_title="Financeiro PRO", layout="wide")

st.markdown("""
<style>
    .stApp {background-color: #0e1117; color: #ffffff}
    [data-testid="stMetricValue"] {font-size: 1.8rem; color: #00d1b2}
    .stButton>button {width: 100%; border-radius: 8px; height: 3em; background-color: #00d1b2; color: black; font-weight: bold}
</style>
""", unsafe_allow_html=True)

# ---------- GESTÃO DE DADOS (CSV) ----------
ARQS = {
    "receitas.csv": ["data", "origem", "valor", "conta"],
    "despesas.csv": ["data", "categoria", "descricao", "valor", "conta", "paga"],
    "cartoes.csv": ["banco_cartao", "limite", "vencimento"],
    "investimentos.csv": ["ativo", "valor", "tipo"],
    "patrimonio.csv": ["salario", "extra", "origem_extra", "inter", "itau"],
    "parcelamentos.csv": ["descricao", "valor_parcela", "total_parcelas", "parcelas_pagas", "cartao", "data_inicio"]
}

def init_db():
    for arq, colunas in ARQS.items():
        if not Path(arq).exists():
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)
        else:
            # Lógica de Auto-Reparo: Adiciona colunas faltantes sem apagar dados
            df_existente = pd.read_csv(arq)
            mudou = False
            for col in colunas:
                if col not in df_existente.columns:
                    # Se a coluna faltante for 'paga', inicia como False, senão vazio
                    df_existente[col] = False if col == "paga" else ""
                    mudou = True
            if mudou:
                df_existente.to_csv(arq, index=False)

def load_data(arq):
    df = pd.read_csv(arq)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"]).dt.date
    return df

def save_data(df, arq):
    df.to_csv(arq, index=False)

# Inicialização
init_db()

# Carregamento e Tratamento de Erros de Coluna
rec = load_data("receitas.csv")
desp = load_data("despesas.csv")
cart = load_data("cartoes.csv")
inv = load_data("investimentos.csv")
pat = load_data("patrimonio.csv")
parc = load_data("parcelamentos.csv")

# Garante que a coluna 'paga' seja tratada como booleana para evitar o KeyError
if "paga" in desp.columns:
    desp["paga"] = desp["paga"].fillna(False).astype(bool)

# ---------- LÓGICA FINANCEIRA ----------
hoje = date.today()
mes_atual = hoje.month

# Saldo considerando apenas o que já foi pago
saldo_atual = rec["valor"].sum() - desp[desp["paga"] == True]["valor"].sum()
contas_pendentes_mes = desp[(pd.to_datetime(desp['data']).dt.month == mes_atual) & (desp["paga"] == False)]["valor"].sum()

# ---------- MENU SUPERIOR ----------
if "pagina" not in st.session_state:
    st.session_state.pagina = "Home"

c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("🏠 Home"): st.session_state.pagina = "Home"
if c2.button("💳 Cartões"): st.session_state.pagina = "Cartoes"
if c3.button("📊 Análise"): st.session_state.pagina = "Analise"
if c4.button("📈 Invest"): st.session_state.pagina = "Invest"
if c5.button("🏦 Patrimônio"): st.session_state.pagina = "Pat"

st.divider()
pagina = st.session_state.pagina

# ---------- TELA HOME ----------
if pagina == "Home":
    st.title("Visão Geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("Saldo Real", f"R$ {saldo_atual:,.2f}")
    col2.metric("A Pagar (Este Mês)", f"R$ {contas_pendentes_mes:,.2f}", delta_color="inverse")
    
    # Lançamento
    col_esq, col_dir = st.columns([2, 1])
    
    with col_esq:
        st.subheader("📝 Novo Lançamento")
        with st.form("form_despesa", clear_on_submit=True):
            c1, c2 = st.columns(2)
            valor = c1.number_input("Valor", min_value=0.0)
            desc = c2.text_input("Descrição")
            
            c3, c4 = st.columns(2)
            cat = c3.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Fixo", "Máquinas", "Outros"])
            conta = c4.selectbox("Conta/Cartão", ["Inter", "Itaú"] + [f"Cartão {b}" for b in cart["banco_cartao"]])
            
            is_parc = st.checkbox("Compra Parcelada?")
            n_parc = st.number_input("Nº de Parcelas", min_value=1, value=1) if is_parc else 1
            
            if st.form_submit_button("Salvar Despesa"):
                v_parc = valor / n_parc
                novos = []
                for i in range(n_parc):
                    data_v = hoje + relativedelta(months=i)
                    d_texto = f"{desc} ({i+1}/{n_parc})" if n_parc > 1 else desc
                    novos.append([data_v, cat, d_texto, v_parc, conta, False])
                
                df_novos = pd.DataFrame(novos, columns=ARQS["despesas.csv"])
                save_data(pd.concat([desp, df_novos]), "despesas.csv")
                st.rerun()

    with col_dir:
        st.subheader("⏳ Próximos Vencimentos")
        proximos = desp[desp["paga"] == False].sort_values("data").head(5)
        for i, r in proximos.iterrows():
            st.markdown(f"**{r['descricao']}** \n`R$ {r['valor']:,.2f}` | {r['data']}")
            if st.button("Marcar como Pago", key=f"btn_{i}"):
                desp.at[i, "paga"] = True
                save_data(desp, "despesas.csv")
                st.rerun()

# ---------- TELA CARTÕES ----------
elif pagina == "Cartoes":
    st.title("Meus Cartões")
    with st.expander("Cadastrar Cartão"):
        with st.form("novo_cartao"):
            b = st.text_input("Banco")
            l = st.number_input("Limite")
            v = st.number_input("Vencimento (Dia)", 1, 31)
            if st.form_submit_button("Salvar"):
                save_data(pd.concat([cart, pd.DataFrame([[b,l,v]], columns=ARQS["cartoes.csv"])]), "cartoes.csv")
                st.rerun()

    for _, r in cart.iterrows():
        fatura = desp[(desp["conta"] == f"Cartão {r['banco_cartao']}") & (desp["paga"] == False)].valor.sum()
        st.metric(f"Fatura {r['banco_cartao']}", f"R$ {fatura:,.2f}", f"Limite: R$ {r['limite']:,.2f}")
        st.progress(min(fatura/r['limite'], 1.0) if r['limite'] > 0 else 0)

# ---------- TELA ANÁLISE ----------
elif pagina == "Analise":
    st.title("Análise de Gastos")
    if not desp.empty:
        fig_pizza = px.pie(desp, values="valor", names="categoria", title="Gastos por Categoria", hole=.4)
        st.plotly_chart(fig_pizza, use_container_width=True)

# ---------- TELA PATRIMÔNIO ----------
elif pagina == "Pat":
    st.title("Patrimônio Total")
    with st.form("form_pat"):
        c1, c2 = st.columns(2)
        inter = c1.number_input("Saldo Inter", value=float(pat['inter'].iloc[0]) if not pat.empty else 0.0)
        itau = c2.number_input("Saldo Itaú", value=float(pat['itau'].iloc[0]) if not pat.empty else 0.0)
        if st.form_submit_button("Atualizar Saldos"):
            save_data(pd.DataFrame([[0, 0, "", inter, itau]], columns=ARQS["patrimonio.csv"]), "patrimonio.csv")
            st.rerun()
    
    total = inter + itau + inv["valor"].sum()
    st.header(f"Total: R$ {total:,.2f}")
