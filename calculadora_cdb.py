import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta

# ===================== CONFIGURAÇÃO DA PÁGINA =====================
st.set_page_config(page_title="Traders Corretora - Calculadora CDB", layout="centered")

# ===================== LOGO + TÍTULO =====================
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    # Seu logo oficial direto do Google Drive (link corrigido para download direto)
    st.image("https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png", width=120)
with col_titulo:
    st.markdown("<h1 style='margin-top: 25px; color: #6B48FF; font-weight: 800;'>traders</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #222; margin-top: -10px;'>Calculadora de CDB Pré e Pós-fixado</h2>", unsafe_allow_html=True)

st.markdown("Simulação personalizada de renda fixa com imposto de renda regressivo e IOF", unsafe_allow_html=True)
st.markdown("---")

# ===================== INFORMAÇÕES DO CLIENTE =====================
st.subheader("Dados da Simulação")

col1, col2 = st.columns(2)
with col1:
    nome_cliente = st.text_input("Nome do Cliente", value="João Silva", help="Nome completo do cliente")
    nome_assessor = st.text_input("Nome do Assessor", value="Seu Nome", help="Seu nome como assessor")
with col2:
    data_simulacao = st.date_input("Data da Simulação", value=datetime.date.today())

st.markdown("---")

# ===================== PARÂMETROS DO INVESTIMENTO =====================
with st.expander("Parâmetros do Investimento", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        investimento = st.number_input("Valor investido (R$)", min_value=100.0, value=500000.0, step=1000.0, format="%.2f")
        data_aplicacao = st.date_input("Data da aplicação", value=datetime.date.today())
    with col_b:
        data_vencimento = st.date_input("Data do resgate/vencimento", value=data_aplicacao + relativedelta(months=+12))
        considerar_iof = st.checkbox("Considerar IOF (resgate antes de 30 dias)", value=False)

    tipo_cdb = st.radio("Tipo de CDB", ["Pré-fixado", "Pós-fixado (% do CDI)"], horizontal=True)

    if tipo_cdb == "Pós-fixado (% do CDI)":
        col_cdi1, col_cdi2 = st.columns(2)
        with col_cdi1:
            taxa_cdi = st.number_input("Taxa CDI anual (%)", min_value=0.01, value=13.65, step=0.05)
        with col_cdi2:
            perc_cdi = st.number_input("Percentual do CDI (%)", min_value=1.0, value=110.0, step=1.0)
        taxa_anual = taxa_cdi * (perc_cdi / 100)
        dias_ano = 252
        st.success(f"Taxa efetiva: **{taxa_anual:.2f}% a.a.** ({perc_cdi}% do CDI)")
    else:
        taxa_anual = st.number_input("Taxa pré-fixada anual (%)", min_value=0.01, value=17.00, step=0.05)
        dias_ano = 360

# ===================== CÁLCULO DO PRAZO (30/360) =====================
prazo_meses = (data_vencimento.year - data_aplicacao.year) * 12 + (data_vencimento.month - data_aplicacao.month)
if data_vencimento.day < data_aplicacao.day:
    prazo_meses -= 1
prazo_dias = prazo_meses * 30

if prazo_dias <= 0:
    st.error("A data de resgate deve ser posterior à data da aplicação.")
    st.stop()

# ===================== CÁLCULOS =====================
taxa_diaria = (1 + taxa_anual / 100) ** (1 / dias_ano) - 1
montante_bruto = investimento * (1 + taxa_diaria) ** prazo_dias
rendimento_bruto = montante_bruto - investimento

# IOF
rendimento_apos_iof = rendimento_bruto
if considerar_iof and prazo_dias < 30:
    tabela_iof = [0.96,0.93,0.90,0.86,0.83,0.80,0.76,0.73,0.70,0.66,
                  0.63,0.60,0.56,0.53,0.50,0.46,0.43,0.40,0.36,0.33,
                  0.30,0.26,0.23,0.20,0.16,0.13,0.10,0.06,0.03,0.00]
    aliquota_iof = tabela_iof[prazo_dias - 1]
    rendimento_apos_iof = rendimento_bruto * (1 - aliquota_iof)

# IR regressivo (360 dias = 20%)
if prazo_dias <= 180:
    aliquota_ir = 22.5
elif prazo_dias <= 360:
    aliquota_ir = 20.0
elif prazo_dias <= 720:
    aliquota_ir = 17.5
else:
    aliquota_ir = 15.0

valor_ir = rendimento_apos_iof * (aliquota_ir / 100)
montante_liquido = investimento + rendimento_apos_iof - valor_ir
rendimento_liquido = montante_liquido - investimento

# ===================== RESULTADO =====================
st.markdown("---")
st.markdown("<h2 style='text-align: center; color: #6B48FF;'>Resultado da Simulação</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("Montante Bruto", f"R$ {montante_bruto:,.2f}")
col2.metric("Rendimento Bruto", f"R$ {rendimento_bruto:,.2f}")
col3.metric("Montante Líquido", f"R$ {montante_liquido:,.2f}", delta=f"+R$ {rendimento_liquido:,.2f}")

st.markdown("---")
st.subheader("Detalhamento da Proposta")

c1, c2 = st.columns(2)
with c1:
    st.write(f"**Cliente:** {nome_cliente}")
    st.write(f"**Assessor:** {nome_assessor}")
    st.write(f"**Data da simulação:** {data_simulacao.strftime('%d/%m/%Y')}")
    st.write(f"**Aplicação:** {data_aplicacao.strftime('%d/%m/%Y')} → **Vencimento:** {data_vencimento.strftime('%d/%m/%Y')}")
    st.write(f"**Prazo:** {prazo_dias} dias ({prazo_dias/360:.2f} anos)")
    st.write(f"**Taxa contratada:** {taxa_anual:.2f}% a.a.")
    if tipo_cdb == "Pós-fixado (% do CDI)":
        st.write(f"→ {perc_cdi}% do CDI")

with c2:
    if considerar_iof and prazo_dias < 30:
        st.write(f"**IOF:** {(1-aliquota_iof):.0%} do rendimento")
    st.write(f"**Alíquota IR:** {aliquota_ir}%")
    st.write(f"**Imposto de Renda:** R$ {valor_ir:,.2f}")
    st.write(f"**Rendimento líquido:** R$ {rendimento_liquido:,.2f}")

# ===================== RODAPÉ =====================
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; padding: 20px; background-color: #f8f5ff; border-radius: 10px; margin-top: 20px;'>"
    f"<p style='margin: 5px; font-size: 15px;'><strong>Simulação elaborada por {nome_assessor}</strong><br>"
    f"em {data_simulacao.strftime('%d/%m/%Y')} para <strong>{nome_cliente}</strong></p>"
    f"<p style='margin: 10px; color: #6B48FF; font-size: 18px; font-weight: bold;'>traders Corretora • Assessoria de Investimentos</p>"
    f"</div>",
    unsafe_allow_html=True
)

if st.button("Nova simulação", type="primary"):
    st.experimental_rerun()
