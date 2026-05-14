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
.main { background-color: #0E1117; color: white; }
.block-container { padding-top: 1.5rem; }
.stMetric { background: #161B22; border: 1px solid #30363D; padding: 15px; border-radius: 16px; }
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
h1, h2, h3 { color: white; }
.card {
    background: linear-gradient(145deg, #161B22, #0E1117);
    border: 1px solid #30363D;
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0 0 25px rgba(0,0,0,0.4);
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================

if "logado" not in st.session_state:
    st.session_state.logado = False
if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"

USUARIO, SENHA = "giovanne", "8708"

if not st.session_state.logado:
    st.title("🔐 Financeiro PRO")
    with st.form("login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if u == USUARIO and s == SENHA:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    st.stop()

# =========================================================
# FUNÇÕES E BASES
# =========================================================

def criar_csv(file, cols):
    if not Path(file).exists():
        pd.DataFrame(columns=cols).to_csv(file, index=False)

@st.cache_data
def load_csv(file):
    return pd.read_csv(file)

def save_csv(df, file):
    df.to_csv(file, index=False)
    load_csv.clear()

def moeda(valor):
    return f"R$ {valor:,.2f}"

def card(titulo, valor):
    st.markdown(f'<div class="card"><h4>{titulo}</h4><h2>{valor}</h2></div>', unsafe_allow_html=True)

criar_csv("receitas.csv", ["data", "categoria", "descricao", "valor"])
criar_csv("despesas.csv", ["data", "categoria", "descricao", "valor"])
criar_csv("fixos.csv", ["descricao", "valor_parcela", "parcelas_total", "parcelas_pagas"])
criar_csv("investimentos.csv", ["ativo", "tipo", "quantidade", "preco_medio", "valor_atual"])

receitas = load_csv("receitas.csv")
despesas = load_csv("despesas.csv")
fixos = load_csv("fixos.csv")
investimentos = load_csv("investimentos.csv")

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("💼 Financeiro PRO")
menu = ["Dashboard", "Receitas", "Despesas", "Fixos", "Investimentos", "Relatórios"]
pagina = st.sidebar.radio("Menu", menu, index=menu.index(st.session_state.pagina))
st.session_state.pagina = pagina

if st.sidebar.button("🚪 Sair"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()

# =========================================================
# PÁGINAS
# =========================================================

if pagina == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    
    t_rec = receitas["valor"].sum()
    t_des = despesas["valor"].sum()
    t_fix = (fixos["valor_parcela"] * (fixos["parcelas_total"] - fixos["parcelas_pagas"])).sum()
    patrim = (investimentos["valor_atual"] * investimentos["quantidade"]).sum()
    saldo = t_rec - t_des - t_fix

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: card("💰 Receitas", moeda(t_rec))
    with c2: card("💸 Despesas", moeda(t_des))
    with c3: card("📌 Fixos", moeda(t_fix))
    with c4: card("🏦 Saldo", moeda(saldo))
    with c5: card("📈 Patrimônio", moeda(patrim))

    st.markdown("##")
    p1, p2 = st.columns(2)
    p1.success(f"📈 Projeção 6 meses: {moeda(saldo * 6)}")
    p2.success(f"🚀 Projeção 12 meses: {moeda(saldo * 12)}")

    st.markdown("##")
    g1, g2 = st.columns(2)
    with g1:
        fig = px.bar(x=["Receitas", "Despesas", "Fixos"], y=[t_rec, t_des, t_fix], template="plotly_dark", title="Resumo Mensal")
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig2 = px.pie(names=["Despesas", "Fixos", "Invest."], values=[t_des, t_fix, patrim], hole=0.5, template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

elif pagina == "Receitas":
    st.title("💰 Receitas")
    with st.form("rec_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d = c1.date_input("Data", date.today())
        cat = c1.selectbox("Categoria", ["Salário", "Freelance", "Investimentos", "Extra"])
        desc = c2.text_input("Descrição")
        val = c2.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar"):
            nova = pd.DataFrame([{"data": str(d), "categoria": cat, "descricao": desc, "valor": val}])
            save_csv(pd.concat([receitas, nova]), "receitas.csv")
            st.rerun()

    st.markdown("### 📋 Lançamentos")
    df_r = pd.read_csv("receitas.csv")
    for i, row in df_r.iterrows():
        cols = st.columns([1, 2, 3, 2, 1])
        cols[0].write(i)
        cols[1].write(row["data"])
        cols[2].write(row["descricao"])
        cols[3].write(moeda(row["valor"]))
        if cols[4].button("🗑️", key=f"del_r_{i}"):
            save_csv(df_r.drop(i), "receitas.csv")
            st.rerun()

elif pagina == "Despesas":
    st.title("💸 Despesas")
    with st.form("desp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d = c1.date_input("Data", date.today())
        cat = c1.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Saúde", "Outros"])
        desc = c2.text_input("Descrição")
        val = c2.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar"):
            nova = pd.DataFrame([{"data": str(d), "categoria": cat, "descricao": desc, "valor": val}])
            save_csv(pd.concat([despesas, nova]), "despesas.csv")
            st.rerun()

    st.markdown("### 📋 Lançamentos")
    df_d = pd.read_csv("despesas.csv")
    for i, row in df_d.iterrows():
        cols = st.columns([1, 2, 3, 2, 1])
        cols[0].write(i)
        cols[1].write(row["data"])
        cols[2].write(row["descricao"])
        cols[3].write(moeda(row["valor"]))
        if cols[4].button("🗑️", key=f"del_d_{i}"):
            save_csv(df_d.drop(i), "despesas.csv")
            st.rerun()

elif pagina == "Fixos":
    st.title("📌 Fixos e Parcelas")
    with st.form("fixo_form"):
        desc = st.text_input("Descrição")
        c1, c2, c3 = st.columns(3)
        v = c1.number_input("Valor Parcela")
        tt = c2.number_input("Total Parcelas", min_value=1)
        pg = c3.number_input("Pagas", min_value=0)
        if st.form_submit_button("Adicionar"):
            nova = pd.DataFrame([{"descricao": desc, "valor_parcela": v, "parcelas_total": tt, "parcelas_pagas": pg}])
            save_csv(pd.concat([fixos, nova]), "fixos.csv")
            st.rerun()

    for i, row in fixos.iterrows():
        st.write(f"**{row['descricao']}**")
        st.progress(min(row['parcelas_pagas']/row['parcelas_total'], 1.0))
        c1, c2, c3 = st.columns(3)
        c1.info(f"Pagas: {int(row['parcelas_pagas'])}/{int(row['parcelas_total'])}")
        c2.error(f"Restante: {moeda((row['parcelas_total']-row['parcelas_pagas'])*row['valor_parcela'])}")
        if c3.button("✅ Pagar Próxima", key=f"pg_{i}"):
            fixos.loc[i, "parcelas_pagas"] += 1
            save_csv(fixos, "fixos.csv")
            st.rerun()

elif pagina == "Investimentos":
    st.title("📈 Investimentos")
    with st.form("inv_form"):
        c1, c2 = st.columns(2)
        atv = c1.text_input("Ativo")
        tp = c1.selectbox("Tipo", ["Ações", "FII", "Crypto", "Renda Fixa"])
        qtd = c2.number_input("Qtd", min_value=0.0)
        pm = c2.number_input("Preço Médio")
        va = c2.number_input("Preço Atual")
        if st.form_submit_button("Adicionar"):
            nova = pd.DataFrame([{"ativo": atv, "tipo": tp, "quantidade": qtd, "preco_medio": pm, "valor_atual": va}])
            save_csv(pd.concat([investimentos, nova]), "investimentos.csv")
            st.rerun()

    if not investimentos.empty:
        st.data_editor(investimentos, use_container_width=True, key="edit_inv")
        st.subheader("🚀 Simulador de Juros Compostos")
        c1, c2, c3 = st.columns(3)
        ap, jr, an = c1.number_input("Aporte", 500.0), c2.number_input("Juros % (Ano)", 12.0), c3.number_input("Anos", 10)
        m_val, hist = 0, []
        for m in range(int(an*12)):
            m_val = (m_val * (1 + (jr/100/12))) + ap
            hist.append(m_val)
        st.success(f"Patrimônio Estimado: {moeda(m_val)}")
        st.line_chart(hist)

elif pagina == "Relatórios":
    st.title("📑 Relatórios")
    resumo = pd.DataFrame({
        "Indicador": ["Receitas", "Despesas", "Fixos", "Patrimônio"],
        "Total": [receitas["valor"].sum(), despesas["valor"].sum(), (fixos["valor_parcela"]*(fixos["parcelas_total"]-fixos["parcelas_pagas"])).sum(), (investimentos["quantidade"]*investimentos["valor_atual"]).sum()]
    })
    st.table(resumo)
    st.download_button("Exportar CSV", resumo.to_csv(index=False).encode('utf-8'), "financeiro.csv")
