import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import base64
from io import BytesIO

# ===================== CONFIGURAÇÃO =====================
st.set_page_config(page_title="Traders Corretora - CDB", layout="centered")

# ===================== LOGO + TÍTULO =====================
st.markdown(
    """<div style="text-align: center; margin: 30px 0;">
        <img src="https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png" width="500">
    </div>""",
    unsafe_allow_html=True
)
st.markdown("<h2 style='text-align: center; color: #222;'>Calculadora de CDB Pré e Pós-fixado</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 17px;'>Simulação personalizada com IR regressivo e IOF</p>", unsafe_allow_html=True)
st.markdown("---")

# ===================== DADOS DO CLIENTE =====================
st.subheader("Dados da Simulação")
c1, c2 = st.columns(2)
with c1:
    nome_cliente = st.text_input("Nome do Cliente", "João Silva")
    nome_assessor = st.text_input("Nome do Assessor", "Seu Nome")
with c2:
    data_simulacao = st.date_input("Data da Simulação", datetime.date.today(), format="DD/MM/YYYY")
st.markdown("---")

# ===================== PARÂMETROS =====================
with st.expander("Parâmetros do Investimento", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        investimento = st.number_input("Valor investido (R$)", min_value=100.0, value=500000.0, step=1000.0)
        st.markdown(f"<h3 style='color:#2E8B57'>R$ {investimento:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        data_aplicacao = st.date_input("Data da aplicação", datetime.date.today(), format="DD/MM/YYYY")
    with col2:
        data_vencimento = st.date_input("Data do resgate", data_aplicacao + relativedelta(months=+12), format="DD/MM/YYYY")
        considerar_iof = st.checkbox("Considerar IOF (resgate antes de 30 dias)")

    tipo_cdb = st.radio("Tipo de CDB", ["Pré-fixado", "Pós-fixado (% do CDI)"], horizontal=True)

    if tipo_cdb == "Pós-fixado (% do CDI)":
        col_cdi1, col_cdi2 = st.columns(2)
        with col_cdi1: taxa_cdi = st.number_input("Taxa CDI anual (%)", value=13.65, step=0.05)
        with col_cdi2: perc_cdi = st.number_input("Percentual do CDI (%)", value=110.0, step=1.0)
        taxa_anual = taxa_cdi * (perc_cdi / 100)
        dias_ano = 252
        st.success(f"Taxa efetiva: **{taxa_anual:.2f}% a.a.**")
    else:
        taxa_anual = st.number_input("Taxa pré-fixada anual (%)", value=17.00, step=0.05)
        dias_ano = 360

# ===================== CÁLCULOS =====================
prazo_meses = (data_vencimento.year - data_aplicacao.year)*12 + (data_vencimento.month - data_aplicacao.month)
if data_vencimento.day < data_aplicacao.day: prazo_meses -= 1
prazo_dias = prazo_meses * 30
if prazo_dias <= 0: st.error("Data de resgate deve ser posterior"); st.stop()

taxa_diaria = (1 + taxa_anual/100)**(1/dias_ano) - 1
montante_bruto = investimento * (1 + taxa_diaria)**prazo_dias
rendimento_bruto = montante_bruto - investimento

rendimento_apos_iof = rendimento_bruto
if considerar_iof and prazo_dias < 30:
    iof_tab = [0.96,0.93,0.90,0.86,0.83,0.80,0.76,0.73,0.70,0.66,0.63,0.60,0.56,0.53,0.50,
               0.46,0.43,0.40,0.36,0.33,0.30,0.26,0.23,0.20,0.16,0.13,0.10,0.06,0.03,0.00]
    rendimento_apos_iof *= (1 - iof_tab[prazo_dias-1])

aliquota_ir = 22.5 if prazo_dias <= 180 else 20.0 if prazo_dias <= 360 else 17.5 if prazo_dias <= 720 else 15.0
ir = rendimento_apos_iof * (aliquota_ir/100)
montante_liquido = investimento + rendimento_apos_iof - ir
rendimento_liquido = montante_liquido - investimento

# ===================== RESULTADO =====================
st.markdown("---")
st.markdown("<h2 style='text-align:center; color:#6B48FF;'>Resultado Final</h2>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
brl = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
col1.metric("Montante Bruto", brl(montante_bruto))
col2.metric("Rendimento Bruto", brl(rendimento_bruto))
col3.metric("Montante Líquido", brl(montante_liquido), delta=brl(rendimento_liquido))

# ===================== TABELA DE EVOLUÇÃO =====================
st.markdown("### Evolução Mês a Mês")
evolucao = []
data_temp = data_aplicacao
for m in range(prazo_meses + 1):
    dias = m * 30
    mont = investimento * (1 + taxa_diaria)**dias
    rend = mont - investimento
    ir_temp = rend * (0.225 if dias<=180 else 0.20 if dias<=360 else 0.175 if dias<=720 else 0.15)
    liquido = investimento + rend - ir_temp
    evolucao.append({
        "Mês": data_temp.strftime("%b/%Y"),
        "Dias": dias,
        "Montante Bruto": brl(mont),
        "Montante Líquido": brl(liquido)
    })
    data_temp += relativedelta(months=1)

st.table(evolucao)

# ===================== GERAR PDF (100% FUNCIONAL) =====================
def criar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Logo
    pdf.image("https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png", x=45, y=8, w=120)

    # Título
    pdf.set_y(60)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(107, 72, 255)
    pdf.cell(0, 15, "Proposta de Investimento - CDB", ln=True, align="C")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12)
    pdf.ln(10)
    pdf.cell(0, 8, f"Cliente: {nome_cliente}", ln=True)
    pdf.cell(0, 8, f"Assessor: {nome_assessor}", ln=True)
    pdf.cell(0, 8, f"Data da simulação: {data_simulacao.strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)

    # Resultados
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Resultado Final", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, f"Valor investido:       {brl(investimento)}", ln=True)
    pdf.cell(0, 8, f"Montante Bruto:        {brl(montante_bruto)}", ln=True)
    pdf.cell(0, 8, f"Montante Líquido:      {brl(montante_liquido)}", ln=True)
    pdf.cell(0, 8, f"Rendimento líquido:    {brl(rendimento_liquido)}", ln=True)
    pdf.cell(0, 8, f"Alíquota IR:           {aliquota_ir}%", ln=True)
    pdf.ln(10)

    # Tabela de evolução
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(50, 10, "Mês", 1)
    pdf.cell(60, 10, "Montante Bruto", 1)
    pdf.cell(60, 10, "Montante Líquido", 1)
    pdf.ln()
    pdf.set_font("Helvetica", size=10)
    for row in evolucao[-12:]:  # últimos 12 meses
        pdf.cell(50, 8, row["Mês"], 1)
        pdf.cell(60, 8, row["Montante Bruto"], 1)
        pdf.cell(60, 8, row["Montante Líquido"], 1)
        pdf.ln()

    # Rodapé
    pdf.set_y(-40)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Traders Corretora - Assessoria de Investimentos", align="C")

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# ===================== BOTÃO PDF =====================
st.markdown("---")
if st.button("GERAR PDF DA PROPOSTA", type="primary", use_container_width=True):
    with st.spinner("Montando seu PDF profissional..."):
        pdf_data = criar_pdf()
        b64 = base64.b64encode(pdf_data).decode()
        nome_arquivo = f"CDB_{nome_cliente.replace(' ', '_')}_{data_simulacao.strftime('%d%m%Y')}.pdf"
        href = f'<a href="data:application/pdf;base64,{b64}" download="{nome_arquivo}"><h3>BAIXAR PDF AGORA</h3></a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("PDF gerado com sucesso!")
        st.balloons()

# ===================== RODAPÉ =====================
st.markdown(
    f"""
    <div style="text-align:center; padding:30px; background:linear-gradient(135deg,#f5f0ff,#ede9ff); border-radius:20px; margin-top:40px;">
       <p style="font-size:18px;"><strong>Simulação elaborada por {nome_assessor}</strong><br>
       em <strong>{data_simulacao.strftime('%d/%m/%Y')}</strong> para <strong>{nome_cliente}</strong></p>
       <p style="color:#6B48FF; font-size:22px; margin-top:20px;"><strong>Traders Corretora - Assessoria de Investimentos</strong></p>
    </div>
    """,
    unsafe_allow_html=True
)

if st.button("Nova simulação"):
    st.experimental_rerun()
