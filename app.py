import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

st.set_page_config(page_title="Financeiro PRO", layout="wide")

# ========= CSS DARK =========
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

# ========= CSV =========
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

rec=load("receitas.csv")
desp=load("despesas.csv")
fixos=load("fixos.csv")
cart=load("cartoes.csv")
inv=load("investimentos.csv")

saldo=rec["valor"].sum()-desp["valor"].sum()

# ========= MENU HORIZONTAL =========
if "pagina" not in st.session_state:
    st.session_state.pagina="Home"

c1,c2,c3,c4,c5,c6=st.columns(6)
if c1.button("🏠 Home"): st.session_state.pagina="Home"
if c2.button("💳 Cartões"): st.session_state.pagina="Cartões"
if c3.button("📊 Análise"): st.session_state.pagina="Analise"
if c4.button("🏦 Patrimônio"): st.session_state.pagina="Patrimonio"
if c5.button("📈 Investimentos"): st.session_state.pagina="Investimentos"
if c6.button("🚪 Sair"):
    st.session_state.logado=False
    st.rerun()

st.divider()
pagina=st.session_state.pagina

# ========= HOME =========
if pagina=="Home":
    st.markdown(f"""
    <div class="card-destaque">
    <h2>💰 Saldo Hoje</h2>
    <h1>R$ {saldo:,.2f}</h1>
    </div>
    """,unsafe_allow_html=True)

    st.subheader("⚠️ Contas Fixas Pendentes")
    for idx,r in fixos.iterrows():
        if r["parcelas_total"]==0 or r["parcelas_pagas"]<r["parcelas_total"]:
            col1,col2=st.columns([4,1])
            col1.markdown(f"""<div class="card">
            <b>{r['descricao']}</b><br>R$ {r['valor_parcela']:,.2f}
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
        st.markdown(f"""<div class="card">
        {r['descricao']} • {r['data']}
        <h3>R$ {r['valor']:,.2f}</h3>
        </div>""",unsafe_allow_html=True)

# ========= CARTÕES =========
elif pagina=="Cartões":
    st.title("💳 Cartões")
    for _,r in cart.iterrows():
        nome=r["banco_cartao"]
        limite=r["limite_total"]
        fatura=desp[desp["conta"]==f"Cartão {nome}"]["valor"].sum()
        disponivel=limite-fatura
        st.markdown(f"""<div class="card">
        <h3>{nome}</h3>
        Limite: R$ {limite:,.2f}<br>
        Fatura: R$ {fatura:,.2f}<br>
        Disponível: R$ {disponivel:,.2f}
        </div>""",unsafe_allow_html=True)

    st.subheader("➕ Novo Cartão")
    with st.form("novo_cartao"):
        b=st.text_input("Banco do Cartão")
        l=st.number_input("Limite",0.0)
        v=st.number_input("Vencimento",1,31)
        if st.form_submit_button("Salvar"):
            novo=pd.DataFrame([{
            "banco_cartao":b,"limite_total":l,"dia_vencimento":v}])
            save(pd.concat([cart,novo]),"cartoes.csv")
            st.rerun()

# ========= INVESTIMENTOS =========
elif pagina=="Investimentos":
    st.title("📈 Investimentos")

    with st.form("novo_inv"):
        c1,c2,c3=st.columns(3)
        ativo=c1.text_input("Ativo")
        valor=c2.number_input("Valor",0.0)
        tipo=c3.selectbox("Tipo",["Tesouro","Ações","Cripto","Liquidez"])
        if st.form_submit_button("Registrar Aporte"):
            novo=pd.DataFrame([{
            "data":date.today(),"ativo":ativo,
            "tipo":tipo,"valor":valor,"instituicao":"Carteira"}])
            save(pd.concat([inv,novo]),"investimentos.csv")

            nova_desp=pd.DataFrame([{
            "data":date.today(),"categoria":"Investimento",
            "descricao":f"Aporte {ativo}",
            "valor":valor,"conta":"Inter"}])
            save(pd.concat([desp,nova_desp]),"despesas.csv")
            st.rerun()

    for _,r in inv.iterrows():
        st.markdown(f"""<div class="card">
        {r['ativo']} ({r['tipo']})<br>
        R$ {r['valor']:,.2f}
        </div>""",unsafe_allow_html=True)

# ========= PATRIMONIO =========
elif pagina=="Patrimonio":
    st.title("🏦 Patrimônio")
    total=inv["valor"].sum()
    st.markdown(f"""<div class="card-destaque">
    <h2>Patrimônio Total</h2>
    <h1>R$ {total:,.2f}</h1>
    </div>""",unsafe_allow_html=True)

    if not inv.empty:
        resumo=inv.groupby("tipo")["valor"].sum().reset_index()
        fig=px.pie(resumo,values="valor",names="tipo",
        template="plotly_dark")
        st.plotly_chart(fig,use_container_width=True)

# ========= ANALISE =========
elif pagina=="Analise":
    if not desp.empty:
        fig=px.pie(desp,values="valor",names="categoria",
        template="plotly_dark")
        st.plotly_chart(fig,use_container_width=True)
