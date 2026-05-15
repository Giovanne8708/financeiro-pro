import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

st.set_page_config(page_title="Financeiro PRO", layout="wide")

# ========= CSS DARK PREMIUM =========
st.markdown("""
<style>
.stApp {background:#0F1115;color:white;font-family:Segoe UI;}
.card{background:#1B1F27;padding:18px;border-radius:18px;margin-bottom:15px;}
.card-destaque{background:linear-gradient(135deg,#FF7A00,#FF9A3C);
padding:25px;border-radius:20px;margin-bottom:20px;}
.stButton>button{background:#FF7A00;color:white;border:none;
border-radius:10px;height:45px;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ========= LOGIN =========
if "logado" not in st.session_state:
    st.session_state.logado=False

if not st.session_state.logado:
    st.title("🔐 Financeiro PRO")
    u=st.text_input("Usuário")
    s=st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u=="giovanne" and s=="8708":
            st.session_state.logado=True
            st.rerun()
    st.stop()

# ========= BANCO CSV =========
ARQS={
"receitas.csv":["data","origem","valor","conta"],
"despesas.csv":["data","categoria","descricao","valor","conta"],
"fixos.csv":["descricao","valor_parcela","parcelas_total","parcelas_pagas"],
"cartoes.csv":["banco_cartao","limite_total","dia_vencimento"],
"investimentos.csv":["data","ativo","tipo","valor","instituicao"]
}

def init():
    for a,c in ARQS.items():
        if not Path(a).exists():
            pd.DataFrame(columns=c).to_csv(a,index=False)

def load(a):
    try:return pd.read_csv(a)
    except:return pd.DataFrame(columns=ARQS[a])

def save(df,a):
    df.to_csv(a,index=False)

init()

# ========= MENU HORIZONTAL =========
if "pagina" not in st.session_state:
    st.session_state.pagina="Home"

c1,c2,c3,c4,c5=st.columns(5)
if c1.button("🏠 Home"): st.session_state.pagina="Home"
if c2.button("💳 Cartões"): st.session_state.pagina="Cartões"
if c3.button("📊 Análise"): st.session_state.pagina="Analise"
if c4.button("🏦 Patrimônio"): st.session_state.pagina="Patrimonio"
if c5.button("🚪 Sair"):
    st.session_state.logado=False
    st.rerun()

st.divider()
pagina=st.session_state.pagina

# ========= DADOS BASE =========
rec=load("receitas.csv")
desp=load("despesas.csv")
fixos=load("fixos.csv")
cart=load("cartoes.csv")
inv=load("investimentos.csv")

saldo=rec["valor"].sum()-desp["valor"].sum()

# ========= HOME =========
if pagina=="Home":
    st.markdown(f"""
    <div class="card-destaque">
    <h2>💰 Saldo Hoje</h2>
    <h1>R$ {saldo:,.2f}</h1>
    </div>
    """,unsafe_allow_html=True)

    # FATURA CARTÕES
    if not cart.empty:
        for _,r in cart.iterrows():
            fatura=desp[desp["conta"]==f"Cartão {r['banco_cartao']}"]["valor"].sum()
            st.markdown(f"""
            <div class="card">
            <b>💳 Fatura {r['banco_cartao']}</b>
            <h3>R$ {fatura:,.2f}</h3>
            </div>
            """,unsafe_allow_html=True)

    # FIXOS A PAGAR
    st.subheader("⚠️ Contas Fixas Pendentes")
    for idx,r in fixos.iterrows():
        if r["parcelas_total"]==0 or r["parcelas_pagas"]<r["parcelas_total"]:
            col1,col2=st.columns([4,1])
            col1.markdown(f"""
            <div class="card">
            <b>{r['descricao']}</b><br>
            R$ {r['valor_parcela']:,.2f}
            </div>""",unsafe_allow_html=True)
            if col2.button("Pagar",key=idx):
                nova=pd.DataFrame([{
                "data":date.today(),
                "categoria":"Fixos",
                "descricao":r["descricao"],
                "valor":r["valor_parcela"],
                "conta":"Inter"}])
                save(pd.concat([desp,nova]),"despesas.csv")
                fixos.at[idx,"parcelas_pagas"]+=1
                save(fixos,"fixos.csv")
                st.rerun()

    # LANÇAMENTOS RÁPIDOS
    st.subheader("➕ Lançamento Rápido")
    with st.form("rapido"):
        c1,c2,c3=st.columns(3)
        v=c1.number_input("Valor",0.0)
        cat=c2.selectbox("Categoria",["Comida","Transporte","Lazer","Saúde"])
        conta=c3.selectbox("Conta",["Inter","Itaú"])
        if st.form_submit_button("Lançar Gasto"):
            nova=pd.DataFrame([{
            "data":date.today(),
            "categoria":cat,
            "descricao":cat,
            "valor":v,
            "conta":conta}])
            save(pd.concat([desp,nova]),"despesas.csv")
            st.rerun()

    st.subheader("🕘 Últimos Lançamentos")
    ult=desp.sort_values("data",ascending=False).head(5)
    for _,r in ult.iterrows():
        st.markdown(f"""
        <div class="card">
        {r['descricao']} • {r['data']}
        <h3>R$ {r['valor']:,.2f}</h3>
        </div>""",unsafe_allow_html=True)

# ========= CARTÕES =========
elif pagina=="Cartões":
    for _,r in cart.iterrows():
        fatura=desp[desp["conta"]==f"Cartão {r['banco_cartao']}"]["valor"].sum()
        st.markdown(f"""
        <div class="card">
        <h3>{r['banco_cartao']}</h3>
        Fatura: R$ {fatura:,.2f}
        </div>
        """,unsafe_allow_html=True)

# ========= ANALISE =========
elif pagina=="Analise":
    if not desp.empty:
        fig=px.pie(desp,values="valor",names="categoria",
        template="plotly_dark")
        st.plotly_chart(fig,use_container_width=True)

# ========= PATRIMONIO =========
elif pagina=="Patrimonio":
    total=inv["valor"].sum()
    st.markdown(f"""
    <div class="card-destaque">
    <h2>🏦 Patrimônio Total</h2>
    <h1>R$ {total:,.2f}</h1>
    </div>
    """,unsafe_allow_html=True)
