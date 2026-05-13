import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Finances and Economy",
    layout="wide",
    page_icon="💰"
)

# =====================================================
# ESTILO
# =====================================================
st.markdown("""
<style>

[data-testid="stSidebar"]{
    display:none;
}

.stApp{
    background:#0f172a;
    color:white;
}

div[data-testid="stMetric"]{
    background:#1e293b;
    border:1px solid #334155;
    padding:20px;
    border-radius:18px;
}

.stTabs [data-baseweb="tab"]{
    background:#1e293b;
    border-radius:12px;
    color:white;
    padding:10px;
}

.stButton button{
    border-radius:12px;
    background:#2563eb;
    color:white;
    border:none;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE
# =====================================================
DB = "financeiro_pro.db"


def conectar():
    return sqlite3.connect(DB, check_same_thread=False)


def init_db():
    conn = conectar()
    c = conn.cursor()

    # CONFIG USER
    c.execute("""
    CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        meta_reserva REAL,
        salario_mensal REAL
    )
    """)

    # PATRIMONIO
    c.execute("""
    CREATE TABLE IF NOT EXISTS patrimonio (
        id INTEGER PRIMARY KEY,
        saldo REAL,
        investimentos REAL
    )
    """)

    # MOVIMENTAÇÕES
    c.execute("""
    CREATE TABLE IF NOT EXISTS mov (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        descricao TEXT,
        valor REAL,
        categoria TEXT,
        tipo TEXT
    )
    """)

    # DEFAULT CONFIG
    c.execute("SELECT COUNT(*) FROM config")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO config
        VALUES (1,'Usuário',10000,0)
        """)

    # DEFAULT PATRIMONIO
    c.execute("SELECT COUNT(*) FROM patrimonio")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO patrimonio
        VALUES (1,0,0)
        """)

    conn.commit()
    conn.close()


init_db()

# =====================================================
# LOAD DATA
# =====================================================
def carregar():

    conn = conectar()

    config = pd.read_sql(
        "SELECT * FROM config WHERE id=1",
        conn
    ).iloc[0]

    patrimonio = pd.read_sql(
        "SELECT * FROM patrimonio WHERE id=1",
        conn
    ).iloc[0]

    mov = pd.read_sql(
        "SELECT * FROM mov ORDER BY id DESC",
        conn
    )

    conn.close()

    return config, patrimonio, mov


config, p, m = carregar()

# =====================================================
# LOGIN
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:

    st.markdown(
        "<h1 style='text-align:center;'>💰 Finances and Economy</h1>",
        unsafe_allow_html=True
    )

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", use_container_width=True):

        if usuario == "giovanne" and senha == "8708":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Usuário inválido")

    st.stop()

# =====================================================
# HEADER
# =====================================================
st.title(f"📈 Painel Financeiro - {config['nome']}")

saldo = float(p["saldo"])
investimentos = float(p["investimentos"])
meta = float(config["meta_reserva"])

rendimento = investimentos * 0.0004

# =====================================================
# METRICS
# =====================================================
c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "💵 Saldo",
    f"R$ {saldo:,.2f}"
)

c2.metric(
    "📈 Investimentos",
    f"R$ {investimentos:,.2f}"
)

c3.metric(
    "🎯 Meta",
    f"R$ {meta:,.2f}"
)

c4.metric(
    "💸 Rendimento Diário",
    f"R$ {rendimento:,.2f}"
)

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "💎 Gestão",
    "📊 Evolução",
    "🎯 Metas",
    "⚙️ Configurações"
])

# =====================================================
# GESTÃO
# =====================================================
with tab1:

    st.subheader("Novo Lançamento")

    col1, col2 = st.columns(2)

    with col1:

        descricao = st.text_input("Descrição")

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            format="%.2f"
        )

    with col2:

        tipo = st.selectbox(
            "Tipo",
            [
                "Gasto",
                "Entrada",
                "Investimento"
            ]
        )

        # TOTALMENTE EDITÁVEL
        categorias_padrao = [
            "Alimentação",
            "Lazer",
            "Transporte",
            "Contas",
            "Salário",
            "Investimento",
            "Outros"
        ]

        categoria = st.selectbox(
            "Categoria",
            categorias_padrao
        )

    if st.button("Salvar Lançamento", use_container_width=True):

        conn = conectar()
        c = conn.cursor()

        c.execute("""
        INSERT INTO mov
        (data, descricao, valor, categoria, tipo)
        VALUES (?,?,?,?,?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            descricao,
            valor,
            categoria,
            tipo
        ))

        # ATUALIZA SALDO
        if tipo == "Entrada":
            c.execute("""
            UPDATE patrimonio
            SET saldo = saldo + ?
            WHERE id=1
            """, (valor,))

        elif tipo == "Gasto":
            c.execute("""
            UPDATE patrimonio
            SET saldo = saldo - ?
            WHERE id=1
            """, (valor,))

        elif tipo == "Investimento":

            c.execute("""
            UPDATE patrimonio
            SET saldo = saldo - ?,
                investimentos = investimentos + ?
            WHERE id=1
            """, (valor, valor))

        conn.commit()
        conn.close()

        st.success("Lançamento salvo!")
        st.rerun()

    st.divider()

    st.subheader("Editar / Excluir Lançamentos")

    if not m.empty:

        id_escolhido = st.selectbox(
            "Selecione o ID",
            m["id"]
        )

        registro = m[m["id"] == id_escolhido].iloc[0]

        nova_desc = st.text_input(
            "Descrição",
            registro["descricao"]
        )

        novo_valor = st.number_input(
            "Valor Atualizado",
            value=float(registro["valor"])
        )

        if st.button("Atualizar Registro"):

            conn = conectar()
            c = conn.cursor()

            c.execute("""
            UPDATE mov
            SET descricao=?,
                valor=?
            WHERE id=?
            """, (
                nova_desc,
                novo_valor,
                id_escolhido
            ))

            conn.commit()
            conn.close()

            st.success("Registro atualizado!")
            st.rerun()

        if st.button("Excluir Registro"):

            conn = conectar()
            c = conn.cursor()

            c.execute("""
            DELETE FROM mov
            WHERE id=?
            """, (id_escolhido,))

            conn.commit()
            conn.close()

            st.success("Registro removido!")
            st.rerun()

# =====================================================
# EVOLUÇÃO
# =====================================================
with tab2:

    st.subheader("Dashboard Financeiro")

    if not m.empty:

        # PIE
        gastos = m[m["tipo"] == "Gasto"]

        if not gastos.empty:

            fig1 = px.pie(
                gastos,
                values="valor",
                names="categoria",
                hole=0.5,
                title="Distribuição de Gastos"
            )

            fig1.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )

            st.plotly_chart(
                fig1,
                use_container_width=True
            )

        # HISTÓRICO
        fig2 = px.line(
            m.sort_values("id"),
            x="data",
            y="valor",
            color="tipo",
            title="Fluxo Financeiro"
        )

        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

        st.subheader("Histórico Completo")

        st.dataframe(
            m,
            use_container_width=True
        )

    else:
        st.info("Nenhum dado cadastrado.")

# =====================================================
# METAS
# =====================================================
with tab3:

    st.subheader("Reserva de Emergência")

    if meta <= 0:
        meta = 1

    progresso = min(investimentos / meta, 1.0)

    st.write(f"Meta Atual: R$ {meta:,.2f}")

    st.progress(progresso)

    st.write(
        f"{progresso*100:.1f}% concluído"
    )

    nova_meta = st.number_input(
        "Alterar Meta",
        value=float(meta)
    )

    if st.button("Salvar Nova Meta"):

        conn = conectar()
        c = conn.cursor()

        c.execute("""
        UPDATE config
        SET meta_reserva=?
        WHERE id=1
        """, (nova_meta,))

        conn.commit()
        conn.close()

        st.success("Meta atualizada!")
        st.rerun()

# =====================================================
# CONFIG
# =====================================================
with tab4:

    st.subheader("Configurações do Usuário")

    novo_nome = st.text_input(
        "Nome do Usuário",
        config["nome"]
    )

    novo_salario = st.number_input(
        "Salário Mensal",
        value=float(config["salario_mensal"])
    )

    saldo_manual = st.number_input(
        "Editar Saldo Manualmente",
        value=float(saldo)
    )

    investimento_manual = st.number_input(
        "Editar Investimentos",
        value=float(investimentos)
    )

    if st.button("Salvar Configurações", use_container_width=True):

        conn = conectar()
        c = conn.cursor()

        c.execute("""
        UPDATE config
        SET nome=?,
            salario_mensal=?
        WHERE id=1
        """, (
            novo_nome,
            novo_salario
        ))

        c.execute("""
        UPDATE patrimonio
        SET saldo=?,
            investimentos=?
        WHERE id=1
        """, (
            saldo_manual,
            investimento_manual
        ))

        conn.commit()
        conn.close()

        st.success("Configurações atualizadas!")
        st.rerun()

    st.divider()

    if st.button("Sair do Sistema"):
        st.session_state.auth = False
        st.rerun()
