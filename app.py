import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from pathlib import Path

# =========================================================
# 1. CONFIGURAÇÕES, ESTILO E SEGURANÇA
# =========================================================
st.set_page_config(page_title="Financeiro PRO", page_icon="💰", layout="wide")

st.markdown("""
<style>
    .main { background-color: #0E1117; color: white; }
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 15px; border-radius: 15px;
    }
    h1, h2, h3 { color: #00ff88 !important; }
    .stButton>button { width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "giovanne" and s == "8708":
            st.session_state.logado = True
            st.rerun()
    st.stop()

# =========================================================
# 2. CÉREBRO: GESTÃO DE DADOS (CSVs)
# =========================================================
ARQUIVOS = {
    "receitas.csv": ["data", "origem", "valor", "conta"],
    "despesas.csv": ["data", "categoria", "descricao", "valor", "conta"],
    "fixos.csv": ["descricao", "valor_parcela", "parcelas_total", "parcelas_pagas"],
    "cartoes.csv": ["banco_cartao", "limite_total", "dia_vencimento"],
    "investimentos.csv": ["data", "ativo", "tipo", "valor", "instituicao"]
}

def init_db():
    for arq, cols in ARQUIVOS.items():
        if not Path(arq).exists():
            pd.DataFrame(columns=cols).to_csv(arq, index=False)

@st.cache_data
def carregar(arq):
    df = pd.read_csv(arq)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors='coerce').dt.date
    return df

def salvar(df, arq):
    df.to_csv(arq, index=False)
    st.cache_data.clear()

init_db()

# --- VARIÁVEIS GLOBAIS ---
LISTA_BANCOS = ["Nubank", "Inter", "Itaú", "Santander", "Carteira"]
LISTA_CATEGORIAS = ["Transporte", "Comida", "Feira", "Jogos", "Lazer", "Saúde", "Fixos", "Investimento"]

# =========================================================
# 3. BARRA LATERAL (MENU)
# =========================================================
with st.sidebar:
    st.title("💰 Menu")
    menu = st.radio("Navegar para:", ["Dashboard", "Receitas", "Despesas", "Fixos", "Cartões", "Investimentos"])
    st.markdown("---")
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# =========================================================
# 4. TELAS DO SISTEMA
# =========================================================

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Painel Geral")
    df_rec = carregar("receitas.csv")
    df_des = carregar("despesas.csv")
    
    saldo_total = df_rec["valor"].sum() - df_des["valor"].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Líquido Total", f"R$ {saldo_total:,.2f}")
    c2.metric("Total Receitas", f"R$ {df_rec['valor'].sum():,.2f}")
    c3.metric("Total Despesas", f"R$ {df_des['valor'].sum():,.2f}", delta_color="inverse")
    
    st.markdown("---")
    col_e, col_d = st.columns(2)
    with col_e:
        st.subheader("Gastos por Categoria")
        if not df_des.empty:
            fig = px.pie(df_des, values='valor', names='categoria', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    with col_d:
        st.subheader("Distribuição por Banco")
        # Lógica de saldo por banco
        saldos_bancos = []
        for b in LISTA_BANCOS:
            s = df_rec[df_rec["conta"] == b]["valor"].sum() - df_des[df_des["conta"] == b]["valor"].sum()
            saldos_bancos.append({"Banco": b, "Saldo": s})
        fig_b = px.bar(pd.DataFrame(saldos_bancos), x="Banco", y="Saldo", template="plotly_dark")
        st.plotly_chart(fig_b, use_container_width=True)

# --- RECEITAS ---
elif menu == "Receitas":
    st.title("💰 Receitas")
    df = carregar("receitas.csv")
    
    # Visores de banco
    cols = st.columns(len(LISTA_BANCOS))
    for i, b in enumerate(LISTA_BANCOS):
        cols[i].metric(b, f"R$ {df[df['conta'] == b]['valor'].sum():,.2f}")
        
    with st.expander("Lançar Receita"):
        with st.form("f_rec"):
            v = st.number_input("Valor", min_value=0.0)
            b = st.selectbox("Banco", LISTA_BANCOS)
            o = st.selectbox("Origem", ["Salário", "Extra", "Investimento"])
            if st.form_submit_button("Salvar"):
                nova = pd.DataFrame([{"data": date.today(), "origem": o, "valor": v, "conta": b}])
                salvar(pd.concat([df, nova]), "receitas.csv")
                st.rerun()
    
    st.subheader("Histórico")
    for idx, row in df.sort_index(ascending=False).iterrows():
        c1, c2, c3, c4 = st.columns([1, 1, 1, 0.5])
        c1.text(row["data"])
        c2.text(f"{row['origem']} ({row['conta']})")
        c3.text(f"R$ {row['valor']:,.2f}")
        if c4.button("🗑️", key=f"del_rec_{idx}"):
            salvar(df.drop(idx), "receitas.csv")
            st.rerun()

# --- DESPESAS ---
elif menu == "Despesas":
    st.title("💸 Despesas")
    df = carregar("despesas.csv")
    
    with st.form("f_des"):
        c1, c2, c3 = st.columns(3)
        v = c1.number_input("Valor", min_value=0.0)
        b = c2.selectbox("Sair de onde?", LISTA_BANCOS + [f"Cartão {c}" for c in LISTA_BANCOS])
        cat = c3.selectbox("Categoria", LISTA_CATEGORIAS)
        desc = st.text_input("Descrição")
        if st.form_submit_button("Registrar Gasto"):
            nova = pd.DataFrame([{"data": date.today(), "categoria": cat, "descricao": desc, "valor": v, "conta": b}])
            salvar(pd.concat([df, nova]), "despesas.csv")
            st.rerun()

    st.subheader("Histórico de Gastos")
    for idx, row in df.sort_index(ascending=False).iterrows():
        c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1, 0.5])
        c1.text(row["data"])
        c2.text(row["categoria"])
        c3.text(row["descricao"])
        c4.text(f"R$ {row['valor']:,.2f}")
        if c5.button("🗑️", key=f"del_des_{idx}"):
            salvar(df.drop(idx), "despesas.csv")
            st.rerun()

# --- FIXOS ---
elif menu == "Fixos":
    st.title("📌 Fixos e Parcelas")
    df = carregar("fixos.csv")
    with st.expander("Novo Agendamento"):
        with st.form("f_fix"):
            desc = st.text_input("O que é?")
            val = st.number_input("Valor")
            tipo = st.radio("Tipo", ["Mensal", "Parcelado"])
            tot = st.number_input("Total Parcelas", min_value=0) if tipo == "Parcelado" else 0
            if st.form_submit_button("Agendar"):
                nova = pd.DataFrame([{"descricao": desc, "valor_parcela": val, "parcelas_total": tot, "parcelas_pagas": 0}])
                salvar(pd.concat([df, nova]), "fixos.csv")
                st.rerun()

    for idx, row in df.iterrows():
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        c1.write(f"**{row['descricao']}**")
        c2.write(f"R$ {row['valor_parcela']:,.2f}")
        b_p = c3.selectbox("Banco", LISTA_BANCOS, key=f"b_f_{idx}")
        if c4.button("✅ Pagar", key=f"pay_f_{idx}"):
            df_d = carregar("despesas.csv")
            n_d = pd.DataFrame([{"data": date.today(), "categoria": "Fixos", "descricao": f"PAGTO: {row['descricao']}", "valor": row['valor_parcela'], "conta": b_p}])
            salvar(pd.concat([df_d, n_d]), "despesas.csv")
            if row['parcelas_total'] > 0:
                df.at[idx, 'parcelas_pagas'] += 1
                salvar(df, "fixos.csv")
            st.rerun()

# --- CARTÕES ---
elif menu == "Cartões":
    st.title("💳 Faturas")
    df_c = carregar("cartoes.csv")
    df_d = carregar("despesas.csv")
    
    with st.expander("Novo Cartão"):
        with st.form("f_car"):
            b = st.selectbox("Banco", LISTA_BANCOS)
            l = st.number_input("Limite")
            v = st.number_input("Vencimento", 1, 31)
            if st.form_submit_button("Salvar"):
                salvar(pd.concat([df_c, pd.DataFrame([{"banco_cartao":b, "limite_total":l, "dia_vencimento":v}])]), "cartoes.csv")
                st.rerun()

    for idx, r in df_c.iterrows():
        nome_c = f"Cartão {r['banco_cartao']}"
        fatura = df_d[df_d["conta"] == nome_c]["valor"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric(nome_c, f"R$ {fatura:,.2f}")
        b_p = c2.selectbox("Pagar com:", LISTA_BANCOS, key=f"b_c_{idx}")
        if c3.button("Liquidar Fatura", key=f"liq_{idx}"):
            # Registrar pagamento no banco e "limpar" cartão
            n_d = pd.DataFrame([{"data":date.today(), "categoria":"Fatura", "descricao":f"Pago {nome_c}", "valor":fatura, "conta":b_p}])
            df_d.loc[df_d["conta"] == nome_c, "conta"] = f"PAGO {nome_c}"
            salvar(pd.concat([df_d, n_d]), "despesas.csv")
            st.rerun()

# --- INVESTIMENTOS ---
elif menu == "Investimentos":
    st.title("📈 Investimentos")
    df_i = carregar("investimentos.csv")
    with st.expander("Novo Aporte"):
        with st.form("f_inv"):
            at = st.text_input("Ativo")
            v = st.number_input("Valor")
            b = st.selectbox("Origem", LISTA_BANCOS)
            t = st.selectbox("Tipo", ["Tesouro", "Liquidez Diária", "Ações"])
            if st.form_submit_button("Investir"):
                # Salva no inv e gera despesa no banco
                salvar(pd.concat([df_i, pd.DataFrame([{"data":date.today(), "ativo":at, "tipo":t, "valor":v, "instituicao":b}])]), "investimentos.csv")
                df_d = carregar("despesas.csv")
                salvar(pd.concat([df_d, pd.DataFrame([{"data":date.today(), "categoria":"Investimento", "descricao":f"Aporte {at}", "valor":v, "conta":b}])]), "despesas.csv")
                st.rerun()
    if not df_i.empty:
        st.plotly_chart(px.pie(df_i, values='valor', names='tipo', template="plotly_dark"), use_container_width=True)
        st.dataframe(df_i, use_container_width=True)
