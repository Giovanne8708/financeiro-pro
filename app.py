import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from dateutil.relativedelta import relativedelta
from pathlib import Path

# ---------- CONFIGURAÇÃO PREMIUM ----------
st.set_page_config(page_title="Financeiro PRO | Assistente", layout="wide")

st.markdown("""
<style>
    .stApp {background-color: #0e1117; color: #ffffff}
    [data-testid="stMetricValue"] {font-size: 2rem; color: #00d1b2; font-weight: 700}
    .main-card {
        background-color: #161b22; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid #30363d;
        margin-bottom: 15px;
    }
    .alert-card {
        background-color: #2a1215;
        border: 1px solid #f85149;
        padding: 10px;
        border-radius: 10px;
        color: #ff7b72;
        margin-bottom: 10px;
    }
    .stButton>button {width: 100%; border-radius: 10px; background-color: #00d1b2; color: #000; font-weight: bold; border: none}
</style>
""", unsafe_allow_html=True)

# ---------- MOTOR DE DADOS ----------
ARQS = {
    "receitas.csv": ["data", "origem", "valor", "conta"],
    "despesas.csv": ["data", "categoria", "descricao", "valor", "conta", "paga"],
    "cartoes.csv": ["banco_cartao", "limite", "vencimento"],
    "investimentos.csv": ["ativo", "valor", "tipo"],
    "patrimonio.csv": ["salario", "extra", "inter", "itau"],
    "parcelamentos.csv": ["descricao", "valor_total", "valor_parcela", "total_parc", "cartao", "data_inicio"]
}

def init_db():
    for arq, colunas in ARQS.items():
        if not Path(arq).exists():
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)
        else:
            df = pd.read_csv(arq)
            for col in colunas:
                if col not in df.columns:
                    df[col] = False if col == "paga" else (0 if "valor" in col else "")
                    df.to_csv(arq, index=False)

def load(arq):
    df = pd.read_csv(arq)
    if "data" in df.columns: df["data"] = pd.to_datetime(df["data"]).dt.date
    if "paga" in df.columns: df["paga"] = df["paga"].fillna(False).astype(bool)
    return df

init_db()
desp, rec, cart, inv, pat, parc = load("despesas.csv"), load("receitas.csv"), load("cartoes.csv"), load("investimentos.csv"), load("patrimonio.csv"), load("parcelamentos.csv")

# ---------- INTELIGÊNCIA FINANCEIRA ----------
hoje = date.today()
mes_atual = hoje.month
renda_total = pat["salario"].sum() + pat["extra"].sum()
gastos_mes = desp[(pd.to_datetime(desp['data']).dt.month == mes_atual)]["valor"].sum()
saldo_real = rec["valor"].sum() - desp[desp["paga"] == True]["valor"].sum()
comprometimento = (gastos_mes / renda_total * 100) if renda_total > 0 else 0

# ---------- NAVEGAÇÃO STYLE BANCO ----------
if "pg" not in st.session_state: st.session_state.pg = "Home"
c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("🏠 Home"): st.session_state.pg = "Home"
if c2.button("💳 Cartões"): st.session_state.pg = "Cartoes"
if c3.button("📊 Inteligência"): st.session_state.pg = "Analise"
if c4.button("📈 Invest"): st.session_state.pg = "Invest"
if c5.button("🏦 Patrimônio"): st.session_state.pg = "Pat"
st.divider()

# ---------- TELA HOME (ASSISTENTE) ----------
if st.session_state.pg == "Home":
    st.subheader(f"Olá! Este é o seu resumo de {hoje.strftime('%B')}")
    
    # ALERTAS INTELIGENTES (O diferencial PRO)
    if comprometimento > 70:
        st.markdown(f'<div class="alert-card">⚠️ Atenção: Você já comprometeu {comprometimento:.1f}% da sua renda mensal!</div>', unsafe_allow_html=True)
    
    # Cards de Insights
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Real", f"R$ {saldo_real:,.2f}")
    col2.metric("Faturas em Aberto", f"R$ {desp[(desp['conta'].str.contains('Cartão')) & (desp['paga']==False)]['valor'].sum():,.2f}")
    col3.metric("Renda Comprometida", f"{comprometimento:.1f}%")
    col4.metric("Patrimônio Total", f"R$ {(pat['inter'].sum() + pat['itau'].sum() + inv['valor'].sum()):,.2f}")

    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown("### ⚡ Ações Rápidas")
        with st.form("quick_add", clear_on_submit=True):
            c_a, c_b, c_c = st.columns(3)
            v = c_a.number_input("Valor", min_value=0.0)
            d = c_b.text_input("Descrição")
            ct = c_c.selectbox("Conta", ["Inter", "Itaú"] + [f"Cartão {b}" for b in cart["banco_cartao"]])
            
            c_d, c_e = st.columns(2)
            cat = c_d.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Máquinas", "Fixo"])
            is_p = c_e.checkbox("Parcelar?")
            n_p = c_e.number_input("Vezes", 1, 48) if is_p else 1
            
            if st.form_submit_button("Confirmar Lançamento"):
                v_p = v / n_p
                novos = []
                for i in range(n_p):
                    data_v = hoje + relativedelta(months=i)
                    novos.append([data_v, cat, f"{d} ({i+1}/{n_p})" if n_p > 1 else d, v_p, ct, False])
                pd.concat([desp, pd.DataFrame(novos, columns=ARQS["despesas.csv"])]).to_csv("despesas.csv", index=False)
                if is_p:
                    p_info = pd.DataFrame([[d, v, v_p, n_p, ct, hoje]], columns=ARQS["parcelamentos.csv"])
                    pd.concat([parc, p_info]).to_csv("parcelamentos.csv", index=False)
                st.rerun()

    with col_r:
        st.markdown("### 🔔 Pendências")
        pendentes = desp[desp["paga"] == False].sort_values("data").head(4)
        for i, r in pendentes.iterrows():
            col_p1, col_p2 = st.columns([2,1])
            col_p1.markdown(f"**{r['descricao']}**\n{r['data'].strftime('%d/%m')}")
            if col_p2.button("Pagar", key=f"p_{i}"):
                desp.at[i, "paga"] = True
                desp.to_csv("despesas.csv", index=False)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- TELA CARTÕES ----------
elif st.session_state.pg == "Cartoes":
    st.title("Gestão de Crédito")
    for _, r in cart.iterrows():
        fatura_total = desp[(desp["conta"] == f"Cartão {r['banco_cartao']}") & (desp["paga"] == False)]["valor"].sum()
        uso_perc = (fatura_total / r['limite']) * 100 if r['limite'] > 0 else 0
        
        with st.container():
            st.markdown(f'<div class="main-card">', unsafe_allow_html=True)
            c_c1, c_c2, c_c3 = st.columns([1, 1, 2])
            c_c1.metric(f"Cartão {r['banco_cartao']}", f"R$ {fatura_total:,.2f}")
            c_c2.metric("Disponível", f"R$ {r['limite'] - fatura_total:,.2f}")
            c_c3.write(f"Uso do limite: {uso_perc:.1f}%")
            st.progress(min(uso_perc/100, 1.0))
            if uso_perc > 70: st.warning("Cuidado: Uso acima de 70% prejudica seu score e reserva.")
            st.markdown('</div>', unsafe_allow_html=True)

# ---------- TELA INTELIGÊNCIA (ANÁLISE) ----------
elif st.session_state.pg == "Analise":
    st.title("Para onde vai o dinheiro?")
    if not desp.empty:
        c_an1, c_an2 = st.columns(2)
        fig_pie = px.pie(desp, values="valor", names="categoria", hole=.5, color_discrete_sequence=px.colors.sequential.Mint)
        c_an1.plotly_chart(fig_pie, use_container_width=True)
        
        # Comparativo Cartão vs Débito
        desp['Tipo'] = desp['conta'].apply(lambda x: 'Crédito' if 'Cartão' in str(x) else 'Débito/Pix')
        fig_bar = px.bar(desp.groupby('Tipo')['valor'].sum().reset_index(), x='Tipo', y='valor', color='Tipo')
        c_an2.plotly_chart(fig_bar, use_container_width=True)

# ---------- TELA PATRIMÔNIO ----------
elif st.session_state.pg == "Pat":
    st.title("Evolução Patrimonial")
    with st.form("pat_update"):
        c_p1, c_p2 = st.columns(2)
        sal = c_p1.number_input("Salário Mensal", value=float(pat['salario'].iloc[0]) if not pat.empty else 0.0)
        ext = c_p2.number_input("Renda Extra", value=float(pat['extra'].iloc[0]) if not pat.empty else 0.0)
        inter = c_p1.number_input("Saldo Inter", value=float(pat['inter'].iloc[0]) if not pat.empty else 0.0)
        itau = c_p2.number_input("Saldo Itaú", value=float(pat['itau'].iloc[0]) if not pat.empty else 0.0)
        if st.form_submit_button("Atualizar Dados"):
            pd.DataFrame([[sal, ext, inter, itau]], columns=ARQS["patrimonio.csv"]).to_csv("patrimonio.csv", index=False)
            st.rerun()

    total_p = inter + itau + inv["valor"].sum()
    st.subheader(f"Seu patrimônio hoje: R$ {total_p:,.2f}")
