import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import date, datetime
from pathlib import Path

# =========================================================
# CONFIGURAÇÃO E UI
# =========================================================
st.set_page_config(page_title="Financeiro PRO v4.0", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    .main { background-color: #0E1117; color: white; }
    .stMetric { background: #161B22; border: 1px solid #30363D; padding: 20px; border-radius: 16px; }
    .card-budget { border-left: 5px solid #00ff88; background: #1c2128; padding: 15px; border-radius: 10px; margin: 10px 0; }
    h1, h2, h3 { color: #00ff88; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# GESTÃO DE DADOS E MIGRAÇÕES
# =========================================================
FILES = {
    "receitas": ["data", "categoria", "descricao", "valor", "conta"],
    "despesas": ["data", "categoria", "descricao", "valor", "conta"],
    "fixos": ["descricao", "valor_parcela", "parcelas_total", "parcelas_pagas"],
    "investimentos": ["ativo", "tipo", "quantidade", "preco_medio"],
    "orcamentos": ["categoria", "limite"]
}

def init_db():
    for file, cols in FILES.items():
        path = f"{file}.csv"
        if not Path(path).exists():
            pd.DataFrame(columns=cols).to_csv(path, index=False)
        else:
            df = pd.read_csv(path)
            for col in cols:
                if col not in df.columns:
                    df[col] = 0 if col != "categoria" else "Geral"
            df.to_csv(path, index=False)

@st.cache_data
def load_data(name):
    df = pd.read_csv(f"{name}.csv")
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors='coerce')
    return df

def save_data(df, name):
    df.to_csv(f"{name}.csv", index=False)
    load_data.clear()

init_db()

# =========================================================
# LOGIN
# =========================================================
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 Financeiro PRO")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "giovanne" and s == "8708":
            st.session_state.logado = True
            st.rerun()
    st.stop()

# =========================================================
# LOGICA DE FILTROS E SALDOS
# =========================================================
st.sidebar.title("💼 Menu PRO")
menu = ["Dashboard", "Receitas", "Despesas", "Fixos", "Investimentos", "Orçamentos"]
escolha = st.sidebar.radio("Navegação", menu)

hoje = datetime.now()
mes_sel = st.sidebar.selectbox("Mês", list(range(1, 13)), index=hoje.month - 1)
ano_sel = st.sidebar.selectbox("Ano", [2024, 2025, 2026], index=2)
LISTA_CONTAS = ["Carteira", "Nubank", "Inter", "Santander"]

# Carregar Bases
df_rec = load_data("receitas")
df_des = load_data("despesas")
df_fix = load_data("fixos")
df_inv = load_data("investimentos")
df_orc = load_data("orcamentos")

# Filtragem Mensal
rec_mes = df_rec[(df_rec['data'].dt.month == mes_sel) & (df_rec['data'].dt.year == ano_sel)]
des_mes = df_des[(df_des['data'].dt.month == mes_sel) & (df_des['data'].dt.year == ano_sel)]

total_rec = rec_mes["valor"].sum()
total_des = des_mes["valor"].sum()
total_fix = df_fix["valor_parcela"].sum()
saldo_final = total_rec - total_des - total_fix

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================
# PÁGINAS COM NOVAS FUNCIONALIDADES
# =========================================================

if escolha == "Dashboard":
    st.title(f"📊 Dashboard - {mes_sel}/{ano_sel}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receitas", fmt(total_rec))
    c2.metric("Despesas", fmt(total_des), delta=f"-{fmt(total_des)}", delta_color="inverse")
    c3.metric("Fixos", fmt(total_fix), delta_color="inverse")
    c4.metric("Saldo Líquido", fmt(saldo_final))

    st.markdown("---")
    st.subheader("🎯 Acompanhamento de Orçamentos")
    
    if not df_orc.empty:
        cols = st.columns(len(df_orc))
        for idx, row in df_orc.iterrows():
            gasto_cat = des_mes[des_mes["categoria"] == row["categoria"]]["valor"].sum()
            percent = min(gasto_cat / row["limite"], 1.0) if row["limite"] > 0 else 0
            cor = "red" if percent >= 0.9 else "orange" if percent >= 0.7 else "green"
            
            with cols[idx % len(cols)]:
                st.markdown(f"**{row['categoria']}**")
                st.progress(percent)
                st.caption(f"{fmt(gasto_cat)} de {fmt(row['limite'])}")
    else:
        st.info("Configure seus orçamentos na aba 'Orçamentos'.")

elif escolha == "Fixos":
    st.title("📌 Automação de Contas Fixas")
    st.write("Dica: Clique em 'Pagar este mês' para gerar uma despesa automática.")
    
    for i, r in df_fix.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.write(f"**{r['descricao']}**")
            c2.write(fmt(r['valor_parcela']))
            c3.write(f"{int(r['parcelas_pagas'])}/{int(r['parcelas_total'])}")
            
            if c4.button(f"✅ Pagar {mes_sel}/{ano_sel}", key=f"pay_{i}"):
                # 1. Registra como Despesa
                nova_desp = pd.DataFrame([{
                    "data": date.today(), "categoria": "Contas Fixas", 
                    "descricao": f"PAGTO: {r['descricao']}", "valor": r['valor_parcela'], "conta": "Automático"
                }])
                save_data(pd.concat([df_des, nova_desp]), "despesas")
                
                # 2. Atualiza Parcela
                if r['parcelas_pagas'] < r['parcelas_total']:
                    df_fix.at[i, 'parcelas_pagas'] += 1
                    save_data(df_fix, "fixos")
                
                st.success(f"{r['descricao']} pago e registrado!")
                st.rerun()

elif escolha == "Investimentos":
    st.title("📈 Carteira com Cotação Real")
    
    if not df_inv.empty:
        patrimonio_total = 0
        for i, r in df_inv.iterrows():
            try:
                # Busca preço real via Yahoo Finance
                ticker = yf.Ticker(r['ativo'])
                preco_atual = ticker.history(period="1d")['Close'].iloc[-1]
            except:
                preco_atual = r['preco_medio'] # Fallback
            
            valor_posicao = r['quantidade'] * preco_atual
            patrimonio_total += valor_posicao
            
            exp = st.expander(f"{r['ativo']} - {r['tipo']}")
            c1, c2, c3 = exp.columns(3)
            c1.metric("Preço Atual", f"R$ {preco_atual:.2f}")
            c2.metric("Quantidade", r['quantidade'])
            c3.metric("Total na Carteira", fmt(valor_posicao))
            
        st.sidebar.metric("Patrimônio Total", fmt(patrimonio_total))
    
    st.subheader("Gerenciar Ativos")
    new_inv = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Carteira"):
        save_data(new_inv, "investimentos")
        st.rerun()

elif escolha == "Orçamentos":
    st.title("🎯 Metas de Gastos")
    st.write("Defina quanto você pretende gastar por categoria no máximo.")
    
    new_orc = st.data_editor(df_orc, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Metas"):
        save_data(new_orc, "orcamentos")
        st.success("Metas atualizadas!")

# ... (Mantendo lógicas básicas de Receitas/Despesas simplificadas para salvar espaço)
elif escolha in ["Receitas", "Despesas"]:
    tipo = "receitas" if escolha == "Receitas" else "despesas"
    st.title(f"📑 Gestão de {escolha}")
    with st.form(f"f_{tipo}"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Data", date.today())
        v = c2.number_input("Valor", min_value=0.0)
        ct = c3.selectbox("Conta", LISTA_CONTAS)
        cat = st.selectbox("Categoria", ["Salário", "Lazer", "Alimentação", "Saúde", "Extra", "Transporte"])
        desc = st.text_input("Descrição")
        if st.form_submit_button("Lançar"):
            df_atual = load_data(tipo)
            nova = pd.DataFrame([{"data": d, "categoria": cat, "descricao": desc, "valor": v, "conta": ct}])
            save_data(pd.concat([df_atual, nova]), tipo)
            st.rerun()
    st.dataframe(load_data(tipo), use_container_width=True)
