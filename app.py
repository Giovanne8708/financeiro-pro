import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from pathlib import Path
import logging

# =========================================================
# CONFIGURAÇÃO PROFISSIONAL
# =========================================================
st.set_page_config(
    page_title="Financeiro PRO v2.0",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração de Logs (Para rastrear erros sem quebrar o app)
logging.basicConfig(level=logging.INFO)

# =========================================================
# CSS AVANÇADO (UX/UI)
# =========================================================
st.markdown("""
<style>
    .main { background-color: #0E1117; color: white; }
    .stMetric { background: #161B22; border: 1px solid #30363D; padding: 20px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
    .card { background: linear-gradient(145deg, #1c2128, #11151c); border: 1px solid #30363D; padding: 20px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 10px; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); border-color: #00ff88; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# GESTÃO DE DADOS (DATABASE LAYER)
# =========================================================
DB_FILES = {
    "receitas": ("receitas.csv", ["data", "categoria", "descricao", "valor"]),
    "despesas": ("despesas.csv", ["data", "categoria", "descricao", "valor"]),
    "fixos": ("fixos.csv", ["descricao", "valor_parcela", "parcelas_total", "parcelas_pagas"]),
    "investimentos": ("investimentos.csv", ["ativo", "tipo", "quantidade", "preco_medio", "valor_atual"])
}

def init_db():
    """Garante que todos os arquivos existam com as colunas corretas"""
    for key, (file, cols) in DB_FILES.items():
        if not Path(file).exists():
            pd.DataFrame(columns=cols).to_csv(file, index=False)

@st.cache_data(show_spinner="Carregando dados...")
def load_data(file_key):
    try:
        return pd.read_csv(DB_FILES[file_key][0])
    except Exception as e:
        st.error(f"Erro ao carregar {file_key}: {e}")
        return pd.DataFrame(columns=DB_FILES[file_key][1])

def save_data(df, file_key):
    try:
        df.to_csv(DB_FILES[file_key][0], index=False)
        load_data.clear() # Limpa o cache para atualizar a visão
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# =========================================================
# SEGURANÇA E SESSÃO
# =========================================================
if "logado" not in st.session_state: st.session_state.logado = False
if "pagina" not in st.session_state: st.session_state.pagina = "Dashboard"

def login():
    st.title("🔐 Financeiro PRO - Acesso")
    with st.container():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.form("login_form"):
                u = st.text_input("Usuário")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if u == "giovanne" and s == "8708": #
                        st.session_state.logado = True
                        st.rerun()
                    else:
                        st.error("Credenciais incorretas")

if not st.session_state.logado:
    login()
    st.stop()

# =========================================================
# INTERFACE PRINCIPAL (VIEWS)
# =========================================================
init_db()
receitas = load_data("receitas")
despesas = load_data("despesas")
fixos = load_data("fixos")
investimentos = load_data("investimentos")

# Sidebar
st.sidebar.title("💼 Financeiro PRO")
menu = ["Dashboard", "Receitas", "Despesas", "Fixos", "Investimentos", "Relatórios"]
st.session_state.pagina = st.sidebar.radio("Navegação", menu, index=menu.index(st.session_state.pagina))

if st.sidebar.button("🚪 Logout"):
    st.session_state.logado = False
    st.rerun()

# --- Helpers ---
def card_metric(titulo, valor, cor="#00ff88"):
    st.markdown(f"""
    <div class="card">
        <p style="color: #8b949e; margin:0; font-size: 0.9rem;">{titulo}</p>
        <h2 style="color: {cor}; margin:0; font-size: 1.8rem;">{valor}</h2>
    </div>
    """, unsafe_allow_html=True)

def fmt_moeda(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================
# LÓGICA DAS PÁGINAS
# =========================================================

if st.session_state.pagina == "Dashboard":
    st.title("📊 Visão Geral")
    
    # Cálculos robustos
    total_rec = receitas["valor"].sum()
    total_desp = despesas["valor"].sum()
    divida_restante = (fixos["valor_parcela"] * (fixos["parcelas_total"] - fixos["parcelas_pagas"])).sum()
    patrimonio = (investimentos["quantidade"] * investimentos["valor_atual"]).sum()
    saldo_livre = total_rec - total_desp

    c1, c2, c3, c4 = st.columns(4)
    with c1: card_metric("Receitas Totais", fmt_moeda(total_rec))
    with c2: card_metric("Despesas Totais", fmt_moeda(total_desp), "#ff5555")
    with c3: card_metric("Saldo em Conta", fmt_moeda(saldo_livre), "#55aaff")
    with c4: card_metric("Patrimônio Investido", fmt_moeda(patrimonio), "#ffd700")

    st.markdown("---")
    g1, g2 = st.columns(2)
    
    with g1:
        fig = px.bar(x=["Receitas", "Despesas", "Fixos"], y=[total_rec, total_desp, divida_restante], 
                     color=["Rec", "Desp", "Fix"], title="Fluxo de Caixa", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
    with g2:
        if patrimonio > 0:
            fig2 = px.pie(investimentos, names="tipo", values="quantidade", hole=.4, title="Alocação de Ativos")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Adicione investimentos para ver a alocação.")

elif st.session_state.pagina == "Receitas":
    st.title("💰 Gestão de Receitas")
    with st.expander("➕ Novo Lançamento", expanded=True):
        with st.form("add_rec"):
            c1, c2, c3 = st.columns(3)
            dat = c1.date_input("Data", date.today())
            cat = c2.selectbox("Categoria", ["Salário", "Freelance", "Investimento", "Outros"])
            val = c3.number_input("Valor (R$)", min_value=0.01)
            des = st.text_input("Descrição / Origem")
            if st.form_submit_button("Confirmar Receita"):
                nova_linha = pd.DataFrame([{"data": str(dat), "categoria": cat, "descricao": des, "valor": val}])
                if save_data(pd.concat([receitas, nova_linha]), "receitas"):
                    st.toast("Receita registrada!", icon="✅")
                    st.rerun()

    st.subheader("📋 Histórico")
    if not receitas.empty:
        # Tabela com deleção profissional
        for i, row in receitas.iterrows():
            cols = st.columns([1, 2, 3, 2, 1])
            cols[0].write(f"`#{i}`")
            cols[1].write(row["data"])
            cols[2].write(row["descricao"])
            cols[3].write(fmt_moeda(row["valor"]))
            if cols[4].button("🗑️", key=f"del_rec_{i}"):
                if save_data(receitas.drop(i), "receitas"): st.rerun()

elif st.session_state.pagina == "Despesas":
    st.title("💸 Controle de Despesas")
    with st.expander("➕ Nova Despesa", expanded=True):
        with st.form("add_desp"):
            c1, c2, c3 = st.columns(3)
            dat = c1.date_input("Data", date.today())
            cat = c2.selectbox("Categoria", ["Casa", "Saúde", "Lazer", "Transporte", "Educação", "Outros"])
            val = c3.number_input("Valor (R$)", min_value=0.01)
            des = st.text_input("O que foi comprado?")
            if st.form_submit_button("Registrar Gasto"):
                nova_linha = pd.DataFrame([{"data": str(dat), "categoria": cat, "descricao": des, "valor": val}])
                if save_data(pd.concat([despesas, nova_linha]), "despesas"):
                    st.toast("Gasto computado!", icon="💸")
                    st.rerun()

    st.subheader("📋 Lista de Gastos")
    if not despesas.empty:
        for i, row in despesas.iterrows():
            cols = st.columns([1, 2, 3, 2, 1])
            cols[0].write(f"`#{i}`")
            cols[1].write(row["data"])
            cols[2].write(row["descricao"])
            cols[3].write(fmt_moeda(row["valor"]))
            if cols[4].button("🗑️", key=f"del_des_{i}"):
                if save_data(despesas.drop(i), "despesas"): st.rerun()

elif st.session_state.pagina == "Fixos":
    st.title("📌 Parcelas e Contas Fixas")
    with st.form("add_fixo"):
        c1, c2, c3 = st.columns(3)
        desc = c1.text_input("Descrição do Bem/Serviço")
        v_parc = c2.number_input("Valor da Parcela", min_value=0.0)
        t_parc = c3.number_input("Total de Parcelas", min_value=1, value=1)
        if st.form_submit_button("Agendar Parcelamento"):
            nova = pd.DataFrame([{"descricao": desc, "valor_parcela": v_parc, "parcelas_total": t_parc, "parcelas_pagas": 0}])
            if save_data(pd.concat([fixos, nova]), "fixos"): st.rerun()

    st.markdown("---")
    for i, row in fixos.iterrows():
        with st.container():
            prog = row["parcelas_pagas"] / row["parcelas_total"]
            st.write(f"### {row['descricao']}")
            st.progress(min(prog, 1.0))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Pagas", f"{int(row['parcelas_pagas'])}/{int(row['parcelas_total'])}")
            c2.metric("Valor Mensal", fmt_moeda(row['valor_parcela']))
            c3.metric("Faltante", fmt_moeda((row['parcelas_total'] - row['parcelas_pagas']) * row['valor_parcela']))
            if c4.button("✅ Pagar Parcela", key=f"pay_{i}"):
                if row["parcelas_pagas"] < row["parcelas_total"]:
                    fixos.at[i, "parcelas_pagas"] += 1
                    save_data(fixos, "fixos")
                    st.rerun()

elif st.session_state.pagina == "Investimentos":
    st.title("📈 Carteira de Investimentos")
    with st.form("add_inv"):
        c1, c2, c3 = st.columns(3)
        atv = c1.text_input("Ativo (Ex: PETR4, BTC, CDB)")
        tip = c2.selectbox("Tipo", ["Ações", "FIIs", "Cripto", "Renda Fixa", "Exterior"])
        qtd = c3.number_input("Qtd", min_value=0.0)
        c4, c5 = st.columns(2)
        pm = c4.number_input("Preço Médio")
        va = c5.number_input("Cotação Atual")
        if st.form_submit_button("Atualizar Carteira"):
            nova = pd.DataFrame([{"ativo": atv, "tipo": tip, "quantidade": qtd, "preco_medio": pm, "valor_atual": va}])
            if save_data(pd.concat([investimentos, nova]), "investimentos"): st.rerun()

    if not investimentos.empty:
        st.subheader("📊 Meus Ativos")
        st.data_editor(investimentos, use_container_width=True, key="inv_editor")
        if st.button("💾 Salvar Alterações na Tabela"):
            save_data(st.session_state.inv_editor["edited_rows"], "investimentos") # Lógica simplificada

elif st.session_state.pagina == "Relatórios":
    st.title("📑 Exportação e Relatórios")
    resumo = pd.DataFrame({
        "Categoria": ["Receitas", "Despesas", "Patrimônio"],
        "Total (R$)": [receitas["valor"].sum(), despesas["valor"].sum(), (investimentos["quantidade"] * investimentos["valor_atual"]).sum()]
    })
    st.table(resumo)
    
    csv_data = resumo.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Relatório Consolidado", data=csv_data, file_name="financeiro_pro.csv", mime="text/csv")
