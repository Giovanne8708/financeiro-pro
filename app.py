import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

# =========================================================
# 1. CONFIGURAÇÃO VISUAL E LOGIN
# =========================================================
st.set_page_config(page_title="Financeiro PRO v6.0", layout="wide")

st.markdown("""
<style>
    .main { background-color: #0f1116; }
    .stApp { background-color: #0f1116; }
    [data-testid="stMetric"] { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; }
    .card-fixo { background: #1c2128; border-left: 5px solid #00ff88; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .card-inv { background: #1c2128; border-top: 4px solid #00d4ff; padding: 15px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 Login Financeiro")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "giovanne" and s == "8708":
            st.session_state.logado = True
            st.rerun()
    st.stop()

# =========================================================
# 2. CÉREBRO DE DADOS (CSVs)
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

def carregar(arq):
    try:
        df = pd.read_csv(arq)
        return df
    except:
        return pd.DataFrame(columns=ARQUIVOS[arq])

def salvar(df, arq):
    df.to_csv(arq, index=False)
    st.cache_data.clear()

init_db()
LISTA_BANCOS_PADRAO = ["Nubank", "Inter", "Itaú", "Santander", "Carteira"]

# =========================================================
# 3. MENU LATERAL
# =========================================================
with st.sidebar:
    st.title("💰 Finance PRO")
    menu = st.radio("Navegar", ["Dashboard", "Receitas", "Despesas", "Fixos", "Cartões", "Investimentos"])
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# =========================================================
# 4. TELAS
# =========================================================

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Painel Geral")
    rec, desp = carregar("receitas.csv"), carregar("despesas.csv")
    saldo = rec["valor"].sum() - desp["valor"].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Líquido", f"R$ {saldo:,.2f}")
    c2.metric("Ganhos", f"R$ {rec['valor'].sum():,.2f}")
    c3.metric("Gastos", f"R$ {desp['valor'].sum():,.2f}", delta_color="inverse")
    
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        if not desp.empty:
            st.plotly_chart(px.pie(desp, values='valor', names='categoria', title="Gastos por Categoria", template="plotly_dark"), use_container_width=True)
    with col_graf2:
        # Gráfico de barras por banco
        bancos_resumo = rec.groupby("conta")["valor"].sum() - desp.groupby("conta")["valor"].sum()
        if not bancos_resumo.empty:
            st.plotly_chart(px.bar(bancos_resumo, title="Saldo por Banco", template="plotly_dark"), use_container_width=True)

# --- RECEITAS ---
elif menu == "Receitas":
    st.title("💰 Receitas")
    df = carregar("receitas.csv")
    
    # Visores Inteligentes (Só mostra banco com dinheiro)
    saldos = df.groupby("conta")["valor"].sum()
    if not saldos.empty:
        cols = st.columns(len(saldos))
        for i, (b, v) in enumerate(saldos.items()):
            cols[i].metric(b, f"R$ {v:,.2f}")

    with st.expander("Novo Lançamento", expanded=True):
        with st.form("f_rec"):
            c1, c2, c3 = st.columns(3)
            val = c1.number_input("Valor", 0.0)
            banco = c2.text_input("Banco (ex: Nubank)")
            origem = c3.selectbox("Origem", ["Salário", "Extra", "Investimento"])
            if st.form_submit_button("Salvar"):
                nova = pd.DataFrame([{"data": date.today(), "origem": origem, "valor": val, "conta": banco.capitalize()}])
                salvar(pd.concat([df, nova]), "receitas.csv")
                st.rerun()

    st.subheader("Histórico")
    st.dataframe(df, use_container_width=True)

# --- DESPESAS ---
elif menu == "Despesas":
    st.title("💸 Despesas")
    df_des = carregar("despesas.csv")
    # Pega bancos das receitas e cartões cadastrados
    contas_disp = list(carregar("receitas.csv")["conta"].unique()) + [f"Cartão {c}" for c in carregar("cartoes.csv")["banco_cartao"].unique()]

    with st.form("f_des"):
        c1, c2, c3 = st.columns(3)
        v = c1.number_input("Valor", 0.0)
        b = c2.selectbox("Pagar com:", contas_disp if contas_disp else LISTA_BANCOS_PADRAO)
        cat = c3.selectbox("Categoria", ["Transporte", "Comida", "Feira", "Jogos", "Lazer", "Saúde"])
        desc = st.text_input("Descrição")
        if st.form_submit_button("Registrar"):
            nova = pd.DataFrame([{"data": date.today(), "categoria": cat, "descricao": desc, "valor": v, "conta": b}])
            salvar(pd.concat([df_des, nova]), "despesas.csv")
            st.rerun()
    
    st.dataframe(df_des, use_container_width=True)

# --- FIXOS ---
elif menu == "Fixos":
    st.title("📌 Contas Fixas")
    df = carregar("fixos.csv")
    with st.expander("Agendar Novo"):
        with st.form("f_fix"):
            d, v = st.text_input("Descrição"), st.number_input("Valor")
            tipo = st.radio("Tipo", ["Mensal", "Parcelado"])
            tot = st.number_input("Total Parcelas", 0) if tipo == "Parcelado" else 0
            if st.form_submit_button("Agendar"):
                salvar(pd.concat([df, pd.DataFrame([{"descricao":d,"valor_parcela":v,"parcelas_total":tot,"parcelas_pagas":0}])]), "fixos.csv")
                st.rerun()

    for idx, r in df.iterrows():
        with st.container():
            st.markdown(f'<div class="card-fixo"><b>{r["descricao"]}</b> - R$ {r["valor_parcela"]:.2f} ({int(r["parcelas_pagas"])}/{int(r["parcelas_total"])})</div>', unsafe_allow_html=True)
            c1, c2 = st.columns([2, 1])
            b_p = c1.selectbox("Banco para pagar", LISTA_BANCOS_PADRAO, key=f"b_{idx}")
            if c2.button("✅ Pagar", key=f"p_{idx}"):
                # Gera despesa e atualiza parcela
                df_d = carregar("despesas.csv")
                n_d = pd.DataFrame([{"data":date.today(),"categoria":"Fixos","descricao":f"Pago {r['descricao']}","valor":r['valor_parcela'],"conta":b_p}])
                salvar(pd.concat([df_d, n_d]), "despesas.csv")
                if r['parcelas_total'] > 0:
                    df.at[idx, 'parcelas_pagas'] += 1
                    salvar(df, "fixos.csv")
                st.rerun()

# --- INVESTIMENTOS ---
elif menu == "Investimentos":
    st.title("📈 Investimentos")
    df_i = carregar("investimentos.csv")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("f_inv"):
            at, vl = st.text_input("Ativo"), st.number_input("Valor")
            tp = st.selectbox("Tipo", ["Tesouro", "Liquidez Diária", "Ações", "Cripto"])
            b = st.selectbox("Banco Origem", LISTA_BANCOS_PADRAO)
            if st.form_submit_button("Investir"):
                salvar(pd.concat([df_i, pd.DataFrame([{"data":date.today(),"ativo":at,"tipo":tp,"valor":vl,"instituicao":b}])]), "investimentos.csv")
                df_d = carregar("despesas.csv")
                salvar(pd.concat([df_d, pd.DataFrame([{"data":date.today(),"categoria":"Investimento","descricao":f"Aporte {at}","valor":vl,"conta":b}])]), "despesas.csv")
                st.rerun()
    with c2:
        if not df_i.empty:
            st.plotly_chart(px.pie(df_i, values='valor', names='tipo', hole=0.5, template="plotly_dark"), use_container_width=True)
            for _, r in df_i.iterrows():
                st.markdown(f'<div class="card-inv"><b>{r["ativo"]}</b>: R$ {r["valor"]:.2f} ({r["tipo"]})</div>', unsafe_allow_html=True)

# --- CARTÕES ---
elif menu == "Cartões":
    st.title("💳 Cartões")
    df_c, df_d = carregar("cartoes.csv"), carregar("despesas.csv")
    with st.expander("Novo Cartão"):
        with st.form("f_c"):
            b, l, v = st.text_input("Banco"), st.number_input("Limite"), st.number_input("Vencimento", 1, 31)
            if st.form_submit_button("Salvar"):
                salvar(pd.concat([df_c, pd.DataFrame([{"banco_cartao":b,"limite_total":l,"dia_vencimento":v}])]), "cartoes.csv")
                st.rerun()

    for idx, r in df_c.iterrows():
        fatura = df_d[df_d["conta"] == f"Cartão {r['banco_cartao']}"]["valor"].sum()
        st.metric(f"Fatura {r['banco_cartao']}", f"R$ {fatura:,.2f}")
        b_p = st.selectbox("Pagar com", LISTA_BANCOS_PADRAO, key=f"bc_{idx}")
        if st.button("Liquidar Fatura", key=f"lq_{idx}"):
            # Transforma gastos do cartão em despesa paga no banco
            df_d.loc[df_d["conta"] == f"Cartão {r['banco_cartao']}", "conta"] = f"PAGO {r['banco_cartao']}"
            n_d = pd.DataFrame([{"data":date.today(),"categoria":"Fatura","descricao":f"Fatura {r['banco_cartao']}","valor":fatura,"conta":b_p}])
            salvar(pd.concat([df_d, n_d]), "despesas.csv")
            st.rerun()
