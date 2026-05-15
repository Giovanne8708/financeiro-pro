import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from dateutil.relativedelta import relativedelta
from pathlib import Path

# ---------- CONFIGURAÇÃO PREMIUM ----------
st.set_page_config(page_title="Financeiro PRO | Assistente", layout="wide")

# CSS customizado para visual "Banking App"
st.markdown("""
<style>
    .stApp {background-color: #0e1117; color: #ffffff}
    [data-testid="stMetricValue"] {font-size: 1.8rem; color: #00d1b2; font-weight: 700}
    .main-card {
        background-color: #161b22; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #30363d;
        margin-bottom: 15px;
    }
    .alert-card {
        background-color: #2a1215;
        border: 1px solid #f85149;
        padding: 12px;
        border-radius: 8px;
        color: #ff7b72;
        margin-bottom: 15px;
        font-weight: bold;
    }
    .stButton>button {width: 100%; border-radius: 8px; background-color: #00d1b2; color: #000; font-weight: bold; border: none}
</style>
""", unsafe_allow_html=True)

# ---------- GESTÃO DE DADOS BLINDADA ----------
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
            mudou = False
            for col in colunas:
                if col not in df.columns:
                    # Define valores padrão para evitar campos vazios
                    df[col] = False if col == "paga" else (0.0 if "valor" in col or col in ["salario", "extra", "inter", "itau", "limite"] else "")
                    mudou = True
            if mudou:
                df.to_csv(arq, index=False)

def load(arq):
    try:
        df = pd.read_csv(arq)
        if df.empty:
            return pd.DataFrame(columns=ARQS[arq])
        if "data" in df.columns: 
            df["data"] = pd.to_datetime(df["data"]).dt.date
        if "paga" in df.columns: 
            df["paga"] = df["paga"].fillna(False).astype(bool)
        return df
    except:
        return pd.DataFrame(columns=ARQS[arq])

init_db()
desp, rec, cart, inv, pat, parc = load("despesas.csv"), load("receitas.csv"), load("cartoes.csv"), load("investimentos.csv"), load("patrimonio.csv"), load("parcelamentos.csv")

# ---------- INTELIGÊNCIA DE CÁLCULO (Com tratamento para zeros) ----------
hoje = date.today()
mes_atual = hoje.month

# Garantia de valores numéricos para evitar erros de exibição
v_salario = float(pat["salario"].iloc[0]) if not pat.empty else 0.0
v_extra = float(pat["extra"].iloc[0]) if not pat.empty else 0.0
v_inter = float(pat["inter"].iloc[0]) if not pat.empty else 0.0
v_itau = float(pat["itau"].iloc[0]) if not pat.empty else 0.0
renda_total = v_salario + v_extra

gastos_mes = desp[(pd.to_datetime(desp['data']).dt.month == mes_atual)]["valor"].sum()
saldo_real = rec["valor"].sum() - desp[desp["paga"] == True]["valor"].sum()
comprometimento = (gastos_mes / renda_total * 100) if renda_total > 0 else 0.0

# ---------- NAVEGAÇÃO ----------
if "pg" not in st.session_state: st.session_state.pg = "Home"
menu = st.columns(5)
btns = ["🏠 Home", "💳 Cartões", "📊 Inteligência", "📈 Invest", "🏦 Patrimônio"]
pgs = ["Home", "Cartoes", "Analise", "Invest", "Pat"]

for col, nome, pg in zip(menu, btns, pgs):
    if col.button(nome): st.session_state.pg = pg

st.divider()

# ---------- TELA HOME ----------
if st.session_state.pg == "Home":
    st.subheader(f"Resumo Financeiro • {hoje.strftime('%B / %Y')}")
    
    # Alertas PRO
    if comprometimento > 70:
        st.markdown(f'<div class="alert-card">⚠️ ALERTA: {comprometimento:.1f}% da sua renda já está comprometida!</div>', unsafe_allow_html=True)
    
    # Cards Principais
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saldo Disponível", f"R$ {saldo_real:,.2f}")
    c2.metric("Faturas em Aberto", f"R$ {desp[(desp['conta'].str.contains('Cartão')) & (desp['paga']==False)]['valor'].sum():,.2f}")
    c3.metric("Renda Comprometida", f"{comprometimento:.1f}%")
    c4.metric("Patrimônio Total", f"R$ {(v_inter + v_itau + inv['valor'].sum()):,.2f}")

    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown("### ⚡ Lançamento Inteligente")
        with st.form("add_pro", clear_on_submit=True):
            f1, f2, f3 = st.columns([1, 2, 1])
            val = f1.number_input("Valor", min_value=0.0, step=10.0)
            desc = f2.text_input("Descrição / Loja")
            conta = f3.selectbox("Origem", ["Inter", "Itaú"] + [f"Cartão {b}" for b in cart["banco_cartao"]])
            
            f4, f5 = st.columns(2)
            cat = f4.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Máquinas", "Fixo"])
            parc_check = f5.checkbox("Esta compra é parcelada?")
            qtd_p = f5.number_input("Número de Parcelas", 1, 48) if parc_check else 1
            
            if st.form_submit_button("Confirmar Transação"):
                v_p = val / qtd_p
                novos_dados = []
                for i in range(qtd_p):
                    dv = hoje + relativedelta(months=i)
                    txt = f"{desc} ({i+1}/{qtd_p})" if qtd_p > 1 else desc
                    novos_dados.append([dv, cat, txt, v_p, conta, False])
                
                df_new = pd.DataFrame(novos_dados, columns=ARQS["despesas.csv"])
                pd.concat([desp, df_new]).to_csv("despesas.csv", index=False)
                st.success("Lançamento concluído!")
                st.rerun()

    with col_r:
        st.markdown("### 🔔 Próximos Pagamentos")
        hoje_dt = pd.to_datetime(date.today())
        pend = desp[desp["paga"] == False].sort_values("data").head(5)
        if pend.empty:
            st.info("Tudo em dia por aqui!")
        for i, r in pend.iterrows():
            with st.container():
                st.markdown(f"**{r['descricao']}** \n`R$ {r['valor']:,.2f}` | {r['data']}")
                if st.button("Marcar como Pago", key=f"pay_{i}"):
                    desp.at[i, "paga"] = True
                    desp.to_csv("despesas.csv", index=False)
                    st.rerun()

# ---------- TELA PATRIMÔNIO (CORREÇÃO DE CAMPOS VAZIOS) ----------
elif st.session_state.pg == "Pat":
    st.title("Gestão de Patrimônio")
    with st.form("pat_form"):
        c_p1, c_p2 = st.columns(2)
        new_sal = c_p1.number_input("Salário Mensal", value=v_salario)
        new_ext = c_p2.number_input("Renda Extra", value=v_extra)
        new_inter = c_p1.number_input("Saldo Banco Inter", value=v_inter)
        new_itau = c_p2.number_input("Saldo Banco Itaú", value=v_itau)
        
        if st.form_submit_button("Salvar Configurações"):
            df_pat = pd.DataFrame([[new_sal, new_ext, new_inter, new_itau]], columns=ARQS["patrimonio.csv"])
            df_pat.to_csv("patrimonio.csv", index=False)
            st.success("Dados atualizados!")
            st.rerun()

# (As outras telas seguem a mesma lógica de segurança de dados)
