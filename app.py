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
# SISTEMA DE DADOS (BANCO DE DADOS COM MIGRACAO)
# =========================================================
FILES = {
    "receitas": ["data", "categoria", "descricao", "valor", "conta"],
    "despesas": ["data", "categoria", "descricao", "valor", "conta"],
    "fixos": ["descricao", "valor_parcela", "parcelas_total", "parcelas_pagas", "dia_vencimento"],
    "investimentos": ["ativo", "tipo", "quantidade", "preco_medio", "valor_atual"]
}

def init_db():
    """Cria ou atualiza os CSVs para garantir que todas as colunas existam"""
    for file, cols in FILES.items():
        path = f"{file}.csv"
        if not Path(path).exists():
            pd.DataFrame(columns=cols).to_csv(path, index=False)
        else:
            # Migração: Adiciona colunas que podem estar faltando em arquivos antigos
            df_check = pd.read_csv(path)
            for col in cols:
                if col not in df_check.columns:
                    df_check[col] = "Não Informado" if col == "conta" else 0
            df_check.to_csv(path, index=False)

@st.cache_data
def load_data(name):
    try:
        df = pd.read_csv(f"{name}.csv")
        if "data" in df.columns:
            # O parâmetro errors='coerce' evita o erro da imagem se houver data inválida
            df["data"] = pd.to_datetime(df["data"], errors='coerce')
            df = df.dropna(subset=['data']) # Remove linhas com datas corrompidas
        return df
    except Exception as e:
        return pd.DataFrame(columns=FILES[name])

def save_data(df, name):
    df.to_csv(f"{name}.csv", index=False)
    load_data.clear()

# Inicializa antes de qualquer carregamento
init_db()

# =========================================================
# LOGIN
# =========================================================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso Restrito")
    with st.container():
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if u == "giovanne" and s == "8708":
                st.session_state.logado = True
                st.rerun()
    st.stop()

# =========================================================
# SIDEBAR E FILTROS
# =========================================================
st.sidebar.title("💼 Financeiro PRO")
menu = ["Dashboard", "Receitas", "Despesas", "Fixos", "Investimentos"]
escolha = st.sidebar.radio("Navegação", menu)

st.sidebar.markdown("---")
hoje = datetime.now()
mes_selecionado = st.sidebar.selectbox("Filtrar Mês", list(range(1, 13)), index=hoje.month - 1)
ano_selecionado = st.sidebar.selectbox("Filtrar Ano", [2024, 2025, 2026], index=2) # 2026 como padrão

LISTA_CONTAS = ["Carteira", "Nubank", "Inter", "Santander", "Outros"]

# =========================================================
# PROCESSAMENTO DE DADOS
# =========================================================
df_rec = load_data("receitas")
df_des = load_data("despesas")
df_fix = load_data("fixos")
df_inv = load_data("investimentos")

# Filtragem segura por período
rec_mes = df_rec[(df_rec['data'].dt.month == mes_selecionado) & (df_rec['data'].dt.year == ano_selecionado)]
des_mes = df_des[(df_des['data'].dt.month == mes_selecionado) & (df_des['data'].dt.year == ano_selecionado)]

# Cálculos de Saldo (Subtração Real)
total_rec = rec_mes["valor"].sum()
total_des = des_mes["valor"].sum()
total_fix = df_fix["valor_parcela"].sum() 

saldo_final = total_rec - total_des - total_fix
patrimonio = (df_inv["quantidade"] * df_inv["valor_atual"]).sum()

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================
# PÁGINAS
# =========================================================

if escolha == "Dashboard":
    st.title(f"📊 Resumo Financeiro")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Ganhos (Mês)", fmt(total_rec))
    with c2: st.metric("Gastos (Mês)", fmt(total_des), delta=f"-{fmt(total_des)}", delta_color="inverse")
    with c3: st.metric("Contas Fixas", fmt(total_fix), delta=f"-{fmt(total_fix)}", delta_color="inverse")
    with c4: st.metric("Saldo Líquido", fmt(saldo_final), delta_color="normal" if saldo_final >= 0 else "inverse")

    st.markdown("---")
    
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Balanço Mensal")
        fig = px.bar(x=["Receitas", "Despesas", "Fixos"], y=[total_rec, total_des, total_fix], 
                     color=["Rec", "Desp", "Fix"], template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
            
    with g2:
        st.subheader("Uso da Renda")
        if total_rec > 0:
            percent = min(((total_des + total_fix) / total_rec), 1.0)
            st.write(f"Você utilizou **{percent*100:.1f}%** do que recebeu.")
            st.progress(percent)
        else:
            st.warning("Sem receitas registradas para este mês.")

elif escolha == "Receitas":
    st.title("💰 Nova Receita")
    with st.form("f_rec"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Data", date.today())
        v = c2.number_input("Valor", min_value=0.0)
        ct = c3.selectbox("Conta de Destino", LISTA_CONTAS)
        desc = st.text_input("Descrição")
        if st.form_submit_button("Salvar"):
            nova = pd.DataFrame([{"data": d, "categoria": "Geral", "descricao": desc, "valor": v, "conta": ct}])
            save_data(pd.concat([df_rec, nova]), "receitas")
            st.rerun()
    st.dataframe(rec_mes, use_container_width=True)

elif escolha == "Despesas":
    st.title("💸 Novo Gasto")
    with st.form("f_desp"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Data", date.today())
        v = c2.number_input("Valor", min_value=0.0)
        ct = c3.selectbox("Origem do Dinheiro", LISTA_CONTAS)
        desc = st.text_input("Descrição")
        if st.form_submit_button("Salvar"):
            nova = pd.DataFrame([{"data": d, "categoria": "Geral", "descricao": desc, "valor": v, "conta": ct}])
            save_data(pd.concat([df_des, nova]), "despesas")
            st.rerun()
    st.dataframe(des_mes, use_container_width=True)

elif escolha == "Fixos":
    st.title("📌 Custos Fixos")
    with st.form("f_fix"):
        c1, c2, c3 = st.columns(3)
        desc = c1.text_input("Nome da Conta")
        v_p = c2.number_input("Valor da Parcela")
        t_p = c3.number_input("Total Parcelas", min_value=1)
        if st.form_submit_button("Adicionar"):
            nova = pd.DataFrame([{"descricao": desc, "valor_parcela": v_p, "parcelas_total": t_p, "parcelas_pagas": 0, "dia_vencimento": 5}])
            save_data(pd.concat([df_fix, nova]), "fixos")
            st.rerun()

    for i, r in df_fix.iterrows():
        exp = st.expander(f"{r['descricao']} - {fmt(r['valor_parcela'])}")
        c1, c2 = exp.columns(2)
        c1.write(f"Progresso: {int(r['parcelas_pagas'])} de {int(r['parcelas_total'])}")
        if c2.button("🗑️ Excluir", key=f"del_f_{i}"):
            save_data(df_fix.drop(i), "fixos")
            st.rerun()

elif escolha == "Investimentos":
    st.title("📈 Patrimônio")
    st.metric("Total em Ativos", fmt(patrimonio))
    edit = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Alterações"):
        save_data(edit, "investimentos")
        st.success("Carteira atualizada!")
