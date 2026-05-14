import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from pathlib import Path

# =========================================================
# CONFIGURAÇÃO E INTERFACE
# =========================================================
st.set_page_config(page_title="Financeiro PRO v3.0", page_icon="💰", layout="wide")

st.markdown("""
<style>
    .main { background-color: #0E1117; color: white; }
    .stMetric { background: #161B22; border: 1px solid #30363D; padding: 20px; border-radius: 16px; }
    .card { background: linear-gradient(145deg, #1c2128, #11151c); border: 1px solid #30363D; padding: 20px; border-radius: 20px; margin-bottom: 20px; }
    h1, h2, h3 { color: #00ff88; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SISTEMA DE DADOS (BANCO DE DADOS)
# =========================================================
FILES = {
    "receitas": ["data", "categoria", "descricao", "valor", "conta"],
    "despesas": ["data", "categoria", "descricao", "valor", "conta"],
    "fixos": ["descricao", "valor_parcela", "parcelas_total", "parcelas_pagas", "dia_vencimento"],
    "investimentos": ["ativo", "tipo", "quantidade", "preco_medio", "valor_atual"]
}

def init_db():
    for file, cols in FILES.items():
        path = f"{file}.csv"
        if not Path(path).exists():
            pd.DataFrame(columns=cols).to_csv(path, index=False)

@st.cache_data
def load_data(name):
    df = pd.read_csv(f"{name}.csv")
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"])
    return df

def save_data(df, name):
    df.to_csv(f"{name}.csv", index=False)
    load_data.clear()

init_db()

# =========================================================
# LOGIN E SESSÃO
# =========================================================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso Restrito")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "giovanne" and s == "8708":
            st.session_state.logado = True
            st.rerun()
    st.stop()

# =========================================================
# BARRA LATERAL (FILTROS PRO)
# =========================================================
st.sidebar.title("💼 Financeiro PRO")
menu = ["Dashboard", "Receitas", "Despesas", "Fixos", "Investimentos"]
escolha = st.sidebar.radio("Navegação", menu)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Filtro de Período")
hoje = datetime.now()
mes_selecionado = st.sidebar.selectbox("Mês", list(range(1, 13)), index=hoje.month - 1)
ano_selecionado = st.sidebar.selectbox("Ano", [2024, 2025, 2026], index=1)

LISTA_CONTAS = ["Carteira (Dinheiro)", "Nubank", "Inter", "Santander", "Outros"]

# =========================================================
# CARREGAMENTO FILTRADO
# =========================================================
df_rec = load_data("receitas")
df_des = load_data("despesas")
df_fix = load_data("fixos")
df_inv = load_data("investimentos")

# Filtrar dados pelo mês/ano selecionado
rec_mes = df_rec[(df_rec['data'].dt.month == mes_selecionado) & (df_rec['data'].dt.year == ano_selecionado)]
des_mes = df_des[(df_des['data'].dt.month == mes_selecionado) & (df_des['data'].dt.year == ano_selecionado)]

# =========================================================
# LÓGICA DE SALDO (SUBTRAÇÃO AUTOMÁTICA)
# =========================================================
total_rec = rec_mes["valor"].sum()
total_des = des_mes["valor"].sum()
# Fixos são considerados despesas do mês atual
total_fix = df_fix["valor_parcela"].sum() 

# O Saldo é a subtração real
saldo_final = total_rec - total_des - total_fix
patrimonio = (df_inv["quantidade"] * df_inv["valor_atual"]).sum()

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================
# PÁGINAS
# =========================================================

if escolha == "Dashboard":
    st.title(f"📊 Resumo de {mes_selecionado}/{ano_selecionado}")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Receitas", fmt(total_rec))
    with c2: st.metric("Despesas", fmt(total_des), delta=f"-{fmt(total_des)}", delta_color="inverse")
    with c3: st.metric("Fixos Mensais", fmt(total_fix), delta=f"-{fmt(total_fix)}", delta_color="inverse")
    with c4: 
        cor_saldo = "normal" if saldo_final >= 0 else "inverse"
        st.metric("Saldo do Mês", fmt(saldo_final), delta_color=cor_saldo)

    st.markdown("---")
    
    col_esq, col_dir = st.columns(2)
    with col_esq:
        st.subheader("Distribuição por Conta")
        df_contas = pd.concat([rec_mes, des_mes])
        if not df_contas.empty:
            fig = px.pie(df_contas, values='valor', names='conta', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
    with col_dir:
        st.subheader("Saúde Financeira")
        if total_rec > 0:
            porcentagem_gasta = ((total_des + total_fix) / total_rec) * 100
            st.write(f"Você comprometeu **{porcentagem_gasta:.1f}%** da sua renda este mês.")
            st.progress(min(porcentagem_gasta/100, 1.0))

elif escolha == "Receitas":
    st.title("💰 Entrada de Capital")
    with st.form("rec"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Data", date.today())
        v = c2.number_input("Valor", min_value=0.0)
        ct = c3.selectbox("Receber em qual conta?", LISTA_CONTAS)
        desc = st.text_input("Descrição")
        if st.form_submit_button("Lançar"):
            nova = pd.DataFrame([{"data": d, "categoria": "Geral", "descricao": desc, "valor": v, "conta": ct}])
            save_data(pd.concat([df_rec, nova]), "receitas")
            st.rerun()

    st.dataframe(rec_mes, use_container_width=True)

elif escolha == "Despesas":
    st.title("💸 Saída de Capital (Gastos)")
    with st.form("desp"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Data", date.today())
        v = c2.number_input("Valor", min_value=0.0)
        ct = c3.selectbox("Sair de qual conta?", LISTA_CONTAS)
        desc = st.text_input("Descrição do Gasto")
        if st.form_submit_button("Registrar Saída"):
            nova = pd.DataFrame([{"data": d, "categoria": "Geral", "descricao": desc, "valor": v, "conta": ct}])
            save_data(pd.concat([df_des, nova]), "despesas")
            st.rerun()

    st.subheader("Gastos deste mês")
    st.dataframe(des_mes, use_container_width=True)

elif escolha == "Fixos":
    st.title("📌 Contas Fixas e Parcelas")
    st.info("O valor total desta página é subtraído automaticamente do seu saldo mensal.")
    with st.form("fixo"):
        c1, c2, c3 = st.columns(3)
        desc = c1.text_input("Nome da Conta (Ex: Aluguel)")
        v_p = c2.number_input("Valor Mensal")
        t_p = c3.number_input("Total Parcelas (1 se for fixo)", min_value=1)
        if st.form_submit_button("Salvar Fixo"):
            nova = pd.DataFrame([{"descricao": desc, "valor_parcela": v_p, "parcelas_total": t_p, "parcelas_pagas": 0, "dia_vencimento": 5}])
            save_data(pd.concat([df_fix, nova]), "fixos")
            st.rerun()

    for i, r in df_fix.iterrows():
        cols = st.columns([3, 2, 2, 1])
        cols[0].write(f"**{r['descricao']}**")
        cols[1].write(fmt(r['valor_parcela']))
        cols[2].write(f"Parc: {r['parcelas_pagas']}/{r['parcelas_total']}")
        if cols[3].button("🗑️", key=f"del_{i}"):
            save_data(df_fix.drop(i), "fixos")
            st.rerun()

elif escolha == "Investimentos":
    st.title("📈 Minha Carteira")
    # Mantendo a lógica anterior, mas com visual limpo
    with st.expander("Adicionar Ativo"):
        with st.form("inv"):
            at = st.text_input("Ativo")
            c1, c2 = st.columns(2)
            q = c1.number_input("Quantidade")
            v_a = c2.number_input("Preço Atual")
            if st.form_submit_button("Adicionar"):
                nova = pd.DataFrame([{"ativo": at, "tipo": "Geral", "quantidade": q, "preco_medio": v_a, "valor_atual": v_a}])
                save_data(pd.concat([df_inv, nova]), "investimentos")
                st.rerun()
    
    st.metric("Patrimônio Total", fmt(patrimonio))
    st.table(df_inv)
