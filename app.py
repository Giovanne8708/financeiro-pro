# ================= VISUAL DARK BANK =================
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

st.set_page_config(page_title="Financeiro PRO", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"]  {font-family: 'Segoe UI', sans-serif;}
.stApp {background-color: #0F1115;}
section[data-testid="stSidebar"] {background-color: #151922;}

.card {background: #1B1F27;padding:18px;border-radius:18px;
box-shadow:0 4px 20px rgba(0,0,0,0.4);margin-bottom:15px;}

.card-destaque {
background: linear-gradient(135deg,#FF7A00,#FF9A3C);
padding:22px;border-radius:20px;color:white;margin-bottom:20px;}

.stButton>button {
background:#FF7A00;color:white;border-radius:12px;
height:45px;border:none;font-weight:bold;}

.stTextInput>div>div>input,
.stNumberInput input,
.stSelectbox div {
background:#232938 !important;color:white !important;
border-radius:10px !important;}

[data-testid="stMetric"] {
background:#1B1F27;border-radius:16px;padding:18px;}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login Financeiro PRO")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "giovanne" and s == "8708":
            st.session_state.logado = True
            st.rerun()
    st.stop()

# ================= BANCO CSV =================
ARQUIVOS = {
    "receitas.csv": ["data","origem","valor","conta"],
    "despesas.csv": ["data","categoria","descricao","valor","conta"],
    "fixos.csv": ["descricao","valor_parcela","parcelas_total","parcelas_pagas"],
    "cartoes.csv": ["banco_cartao","limite_total","dia_vencimento"],
    "investimentos.csv": ["data","ativo","tipo","valor","instituicao"]
}

def init_db():
    for arq, cols in ARQUIVOS.items():
        if not Path(arq).exists():
            pd.DataFrame(columns=cols).to_csv(arq, index=False)

def carregar(arq):
    try: return pd.read_csv(arq)
    except: return pd.DataFrame(columns=ARQUIVOS[arq])

def salvar(df, arq):
    df.to_csv(arq, index=False)

init_db()
LISTA_BANCOS_PADRAO = ["Nubank","Inter","Itaú","Santander","Carteira"]

# ================= MENU =================
with st.sidebar:
    st.markdown("## 💰 Finance PRO")
    menu = st.radio("Navegar",
        ["Dashboard","Receitas","Despesas","Fixos","Cartões","Investimentos"])
    if st.button("Sair"):
        st.session_state.logado=False
        st.rerun()

# ================= DASHBOARD =================
if menu=="Dashboard":
    rec, desp = carregar("receitas.csv"), carregar("despesas.csv")
    saldo = rec["valor"].sum() - desp["valor"].sum()

    st.markdown('<div class="card-destaque">',unsafe_allow_html=True)
    st.markdown(f"### 💰 Saldo Total\n# R$ {saldo:,.2f}")
    st.markdown('</div>',unsafe_allow_html=True)

    c1,c2=st.columns(2)
    c1.metric("Ganhos", f"R$ {rec['valor'].sum():,.2f}")
    c2.metric("Gastos", f"R$ {desp['valor'].sum():,.2f}")

    if not desp.empty:
        st.plotly_chart(px.pie(desp,values='valor',names='categoria',
        template="plotly_dark"),use_container_width=True)

# ================= RECEITAS =================
elif menu=="Receitas":
    df=carregar("receitas.csv")

    st.markdown('<div class="card">',unsafe_allow_html=True)
    with st.form("f_rec"):
        val=st.number_input("Valor",0.0)
        banco=st.text_input("Banco")
        origem=st.selectbox("Origem",["Salário","Extra","Investimento"])
        if st.form_submit_button("Salvar"):
            nova=pd.DataFrame([{"data":date.today(),
            "origem":origem,"valor":val,"conta":banco}])
            salvar(pd.concat([df,nova]),"receitas.csv")
            st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)

    for _,r in df.iterrows():
        st.markdown(f"""
        <div class="card">
        <b>{r['origem']}</b><br>
        <span style='color:#9AA4B2'>{r['data']}</span>
        <h3>R$ {r['valor']:,.2f}</h3>
        </div>""",unsafe_allow_html=True)

# ================= DESPESAS =================
elif menu=="Despesas":
    df=carregar("despesas.csv")

    st.markdown('<div class="card">',unsafe_allow_html=True)
    with st.form("f_des"):
        v=st.number_input("Valor",0.0)
        b=st.selectbox("Conta",LISTA_BANCOS_PADRAO)
        cat=st.selectbox("Categoria",
        ["Transporte","Comida","Feira","Lazer","Saúde"])
        desc=st.text_input("Descrição")
        if st.form_submit_button("Registrar"):
            nova=pd.DataFrame([{"data":date.today(),
            "categoria":cat,"descricao":desc,
            "valor":v,"conta":b}])
            salvar(pd.concat([df,nova]),"despesas.csv")
            st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)

    for _,r in df.iterrows():
        st.markdown(f"""
        <div class="card">
        <b>{r['descricao']}</b><br>
        <span style='color:#9AA4B2'>{r['categoria']} • {r['data']}</span>
        <h3 style='color:#FF4D4F'>R$ {r['valor']:,.2f}</h3>
        </div>""",unsafe_allow_html=True)
