import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path

# ---------- CONFIGURAÇÃO E ESTILO ----------
st.set_page_config(page_title="Financeiro PRO", layout="wide")

st.markdown("""
<style>
    .stApp {background-color: #0e1117; color: #ffffff;}
    [data-testid="stMetricValue"] {font-size: 1.8rem; color: #00d1b2;}
    .card {
        background-color: #1e2127; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #00d1b2;
        margin-bottom: 10px;
    }
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #00d1b2; color: black;}
</style>
""", unsafe_allow_html=True)

# ---------- GESTÃO DE DADOS (CSV) ----------
ARQS = {
    "receitas.csv": ["data", "origem", "valor", "conta"],
    "despesas.csv": ["data", "categoria", "descricao", "valor", "conta", "paga"],
    "cartoes.csv": ["banco_cartao", "limite", "vencimento"],
    "investimentos.csv": ["ativo", "valor", "tipo"],
    "patrimonio.csv": ["salario", "extra", "origem_extra", "inter", "itau"],
    "parcelamentos.csv": ["descricao", "valor_parcela", "total_parcelas", "parcelas_pagas", "cartao", "data_inicio"]
}

def init_db():
    for arq, colunas in ARQS.items():
        if not Path(arq).exists():
            pd.DataFrame(columns=colunas).to_csv(arq, index=False)

def load_data(arq):
    df = pd.read_csv(arq)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"]).dt.date
    return df

def save_data(df, arq):
    df.to_csv(arq, index=False)

init_db()

# Carregamento Inicial
rec = load_data("receitas.csv")
desp = load_data("despesas.csv")
cart = load_data("cartoes.csv")
inv = load_data("investimentos.csv")
pat = load_data("patrimonio.csv")
parc = load_data("parcelamentos.csv")

# ---------- LÓGICA FINANCEIRA ----------
hoje = date.today()
mes_atual = hoje.month
ano_atual = hoje.year

# Cálculos de Saldo e Fatura
saldo_atual = rec["valor"].sum() - desp[desp["paga"] == True]["valor"].sum()
faturas_globais = desp[(desp["conta"].str.contains("Cartão")) & (desp["paga"] == False)].valor.sum()

# ---------- MENU SUPERIOR HORIZONTAL ----------
if "pagina" not in st.session_state:
    st.session_state.pagina = "Home"

menu_cols = st.columns(5)
botoes = ["🏠 Home", "💳 Cartões", "📊 Análise", "📈 Invest", "🏦 Patrimônio"]
paginas = ["Home", "Cartoes", "Analise", "Invest", "Pat"]

for col, nome, pg in zip(menu_cols, botoes, paginas):
    if col.button(nome):
        st.session_state.pagina = pg

st.divider()
pagina = st.session_state.pagina

# ---------- TELA HOME ----------
if pagina == "Home":
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo em Conta", f"R$ {saldo_atual:,.2f}")
    c2.metric("Contas a Pagar (Mês)", f"R$ {faturas_globais:,.2f}", delta_color="inverse")
    
    renda_total = pat["salario"].sum() + pat["extra"].sum()
    if renda_total > 0:
        perc = (desp[pd.to_datetime(desp['data']).dt.month == mes_atual]['valor'].sum() / renda_total) * 100
        c3.metric("% Renda Comprometida", f"{perc:.1f}%")

    col_esq, col_dir = st.columns([2, 1])

    with col_esq:
        st.subheader("🚀 Lançamento Rápido")
        tab1, tab2 = st.tabs(["Despesa", "Receita"])
        
        with tab1:
            with st.form("nova_despesa"):
                c1, c2 = st.columns(2)
                v_total = c1.number_input("Valor Total", min_value=0.0, step=10.0)
                desc = c2.text_input("Descrição / Loja")
                
                c3, c4 = st.columns(2)
                cat = c3.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Fixo", "Outros"])
                conta = c4.selectbox("Forma de Pagamento", ["Inter", "Itaú"] + [f"Cartão {b}" for b in cart["banco_cartao"]])
                
                is_parc = st.checkbox("Essa compra é parcelada?")
                num_parc = st.number_input("Quantidade de Parcelas", min_value=1, value=1) if is_parc else 1
                
                if st.form_submit_button("Lançar Despesa"):
                    v_parcela = v_total / num_parc
                    novas_linhas = []
                    
                    for i in range(num_parc):
                        data_venc = hoje + relativedelta(months=i)
                        novas_linhas.append([data_venc, cat, f"{desc} ({i+1}/{num_parc})", v_parcela, conta, False])
                    
                    # Salva em despesas
                    nova_desp_df = pd.DataFrame(novas_linhas, columns=ARQS["despesas.csv"])
                    save_data(pd.concat([desp, nova_desp_df]), "despesas.csv")
                    
                    # Salva em parcelamentos se aplicável
                    if is_parc:
                        novo_p = pd.DataFrame([[desc, v_parcela, num_parc, 0, conta, hoje]], columns=ARQS["parcelamentos.csv"])
                        save_data(pd.concat([parc, novo_p]), "parcelamentos.csv")
                    
                    st.success("Lançado com sucesso!")
                    st.rerun()

    with col_dir:
        st.subheader("📅 Próximas Contas")
        pendentes = desp[desp["paga"] == False].sort_values("data").head(5)
        for i, r in pendentes.iterrows():
            with st.container():
                st.markdown(f"**{r['descricao']}** \n`R$ {r['valor']:,.2f}` - {r['data']}")
                if st.button("Marcar como Pago", key=f"pago_{i}"):
                    desp.at[i, "paga"] = True
                    save_data(desp, "despesas.csv")
                    st.rerun()

# ---------- TELA CARTÕES ----------
elif pagina == "Cartoes":
    st.title("Gerenciamento de Cartões")
    
    with st.expander("➕ Cadastrar Novo Cartão"):
        with st.form("cad_cartao"):
            b = st.text_input("Banco")
            l = st.number_input("Limite Total")
            v = st.number_input("Dia de Vencimento", 1, 31)
            if st.form_submit_button("Salvar"):
                save_data(pd.concat([cart, pd.DataFrame([[b,l,v]], columns=ARQS["cartoes.csv"])]), "cartoes.csv")
                st.rerun()

    for _, r in cart.iterrows():
        fatura_atual = desp[(desp["conta"] == f"Cartão {r['banco_cartao']}") & (desp["paga"] == False)].valor.sum()
        disponivel = r['limite'] - fatura_atual
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"Fatura {r['banco_cartao']}", f"R$ {fatura_atual:,.2f}")
        with col2:
            st.metric("Limite Disponível", f"R$ {disponivel:,.2f}")
        with col3:
            progresso = min(fatura_atual / r['limite'], 1.0) if r['limite'] > 0 else 0
            st.write(f"Uso do Limite: {progresso*100:.1f}%")
            st.progress(progresso)
        st.divider()

# ---------- TELA ANÁLISE ----------
elif pagina == "Analise":
    st.title("Inteligência Financeira")
    
    if not desp.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(desp, values="valor", names="categoria", title="Gastos por Categoria", hole=.4))
        with c2:
            # Evolução Mensal
            desp['data'] = pd.to_datetime(desp['data'])
            evolucao = desp.groupby(desp['data'].dt.strftime('%Y-%m')).sum(numeric_only=True).reset_index()
            st.plotly_chart(px.line(evolucao, x='data', y='valor', title="Evolução de Gastos"))

        # Cards Resumo
        res1, res2, res3 = st.columns(3)
        res1.info(f"Total Cartão: R$ {faturas_globais:,.2f}")
        res2.info(f"Total Débito/Pix: R$ {desp[~desp['conta'].str.contains('Cartão')]['valor'].sum():,.2f}")
        res3.success(f"Economia Total: R$ {saldo_atual:,.2f}")

# ---------- TELA PATRIMÔNIO ----------
elif pagina == "Pat":
    st.title("Meu Patrimônio")
    
    with st.form("patrimonio"):
        c1, c2 = st.columns(2)
        sal = c1.number_input("Salário Mensal", value=float(pat['salario'].iloc[0]) if not pat.empty else 0.0)
        ext = c2.number_input("Renda Extra", value=float(pat['extra'].iloc[0]) if not pat.empty else 0.0)
        
        c3, c4 = st.columns(2)
        b_inter = c3.number_input("Saldo Inter", value=float(pat['inter'].iloc[0]) if not pat.empty else 0.0)
        b_itau = c4.number_input("Saldo Itaú", value=float(pat['itau'].iloc[0]) if not pat.empty else 0.0)
        
        if st.form_submit_button("Atualizar Patrimônio"):
            novo_pat = pd.DataFrame([[sal, ext, "Geral", b_inter, b_itau]], columns=ARQS["patrimonio.csv"])
            save_data(novo_pat, "patrimonio.csv")
            st.rerun()

    if not pat.empty:
        total_pat = b_inter + b_itau + inv["valor"].sum()
        st.subheader(f"Patrimônio Líquido: R$ {total_pat:,.2f}")

# Rodapé de exportação
st.sidebar.divider()
if st.sidebar.button("📥 Exportar Relatório CSV"):
    st.sidebar.download_button("Baixar Despesas", desp.to_csv(index=False), "despesas.csv", "text/csv")
