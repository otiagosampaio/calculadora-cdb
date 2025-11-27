import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

# ===================== CONFIGURAÇÃO =====================
st.set_page_config(page_title="Traders Corretora - CDB", layout="centered")

# ===================== LOGO + TÍTULO =====================
st.markdown(
    """<div style="text-align: center; margin: 20px 0;">
        <img src="https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png" width="500">
    </div>""",
    unsafe_allow_html=True
)
st.markdown("<h2 style='text-align: center; color: #222;'>Calculadora de CDB Pré e Pós-fixado</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 17px; margin-bottom: 30px;'>Simulação personalizada com IR regressivo e IOF</p>", unsafe_allow_html=True)
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
with st.expander("Preferências do Investimento", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        investimento = st.number_input("Valor aplicado", min_value=100.0, value=500000.0, step=1000.0)
        st.markdown(f"<h3 style='color:#2E8B57'>R$ {investimento:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        data_aplicacao = st.date_input("Data da aplicação", datetime.date.today(), format="DD/MM/YYYY")
    with col2:
        data_vencimento = st.date_input("Data do resgate", data_aplicacao + relativedelta(months=+12), format="DD/MM/YYYY")
        considerar_iof = st.checkbox("Considerações", value=True, help="IR e IOF")

    tipo_cdb = st.radio("Tipo de CDB", ["Pré-fixado", "Pós-fixado (% do CDI)"], horizontal=True)

    if tipo_cdb == "Pós-fixado (% do CDI)":
        col_cdi1, col_cdi2 = st.columns(2)
        with col_cdi1: taxa_cdi = st.number_input("Taxa CDI anual (%)", value=13.65, step=0.05)
        with col_cdi2: perc_cdi = st.number_input("Percentual do CDI (%)", value=110.0, step=1.0)
        taxa_anual = taxa_cdi * (perc_cdi / 100)
        dias_ano = 252
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

# ===================== GRÁFICO =====================
st.markdown("### Projeção da Rentabilidade")
datas_graf, bruto_graf, liquido_graf = [], [], []
data_temp = data_aplicacao
for m in range(prazo_meses + 1):
    dias = m * 30
    mont = investimento * (1 + taxa_diaria)**dias
    rend = mont - investimento
    ir_temp = rend * (0.225 if dias<=180 else 0.20 if dias<=360 else 0.175 if dias<=720 else 0.15)
    datas_graf.append(data_temp)
    bruto_graf.append(mont)
    liquido_graf.append(investimento + rend - ir_temp)
    data_temp += relativedelta(months=1)

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(datas_graf, bruto_graf, label="CDB Pré + IR (líquido)", color="#6B48FF", linewidth=4)
ax.plot(datas_graf, liquido_graf, label="CDB Pré + IR (líquido)", color="#2E8B57", linewidth=4, linestyle="--", alpha=0.8)
ax.set_title("Projeção da Rentabilidade", fontsize=16, pad=20)
ax.set_ylabel("Valor em R$")
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

# ===================== RESULTADO FINAL =====================
st.markdown("---")
st.markdown("<h2 style='text-align:center; color:#1e3a8a;'>Resultado Final</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
brl = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
col1.metric("Valor Bruto", brl(montante_bruto))
col2.metric("Impostos", brl(ir + (rendimento_bruto - rendimento_apos_iof)))
col3.metric("Valor Líquido", brl(montante_liquido), delta=brl(rendimento_liquido))

# ===================== GERAR PNG DO GRÁFICO =====================
def grafico_png():
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='#f8fafc')
    buf.seek(0)
    return buf

# ===================== PDF EXATAMENTE COMO A IMAGEM =====================
def criar_pdf_igual_imagem():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()

    story = []

    # Logo
    logo = Image("https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png", width=140*mm, height=30*mm)
    logo.hAlign = 'CENTER'
    story.append(logo)
    story.append(Spacer(1, 10*mm))

    # Título
    story.append(Paragraph("Simulação de Investimento - CDB Pré e Pós-fixado", ParagraphStyle(name='Title', fontSize=18, alignment=1, spaceAfter=10*mm)))
    story.append(Paragraph("Projeção personalizada considerando IR e IOF", ParagraphStyle(name='Sub', fontSize=12, alignment=1, textColor=colors.grey, spaceAfter=20*mm)))

    # Dados da simulação
    story.append(Paragraph("<b>DADOS DA SIMULAÇÃO</b>", styles['Heading3']))
    data_simulacao_table = [
        ["Nome do cliente", nome_cliente],
        ["Data da simulação", data_simulacao.strftime('%d/%m/%Y')],
        ["Valor investido", brl(investimento)],
        ["Tipo de CDB", tipo_cdb],
    ]
    t = Table(data_simulacao_table, colWidths=[80*mm, 80*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 15*mm))

    # Gráfico
    img = Image(grafico_png(), width=170*mm, height=80*mm)
    img.hAlign = 'CENTER'
    story.append(img)
    story.append(Spacer(1, 10*mm))

    # Resultado Final (caixa azul escura)
    story.append(Spacer(1, 15*mm))
    resultado = [
        ["VALOR BRUTO", "IMPOSTOS", "VALOR LÍQUIDO"],
        [brl(montante_bruto), brl(ir + (rendimento_bruto - rendimento_apos_iof)), brl(montante_liquido)],
    ]
    t_res = Table(resultado, colWidths=[56*mm, 56*mm, 56*mm])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,0), 14),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#1e40af")),
        ('TEXTCOLOR', (0,1), (-1,1), colors.white),
        ('FONTSIZE', (0,1), (-1,1), 18),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0, colors.transparent),
        ('ROUNDEDCORNERS', (0,0), (-1,-1), 15),
    ]))
    story.append(t_res)

    # Rodapé
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph(f"Simulação elaborada por <b>{nome_assessor}</b> em {data_simulacao.strftime('%d/%m/%Y')}", ParagraphStyle(name='Footer', fontSize=11, alignment=1, textColor=colors.grey)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ===================== BOTÃO PDF =====================
st.markdown("---")
if st.button("BAIXAR PROPOSTA PREMIUM", type="primary", use_container_width=True):
    with st.spinner("Gerando proposta premium..."):
        pdf_data = criar_pdf_igual_imagem()
        b64 = base64.b64encode(pdf_data).decode()
        nome_arq = f"Proposta_CDB_{nome_cliente.replace(' ', '_')}.pdf"
        href = f'<a href="data:application/pdf;base64,{b64}" download="{nome_arq}"><h3>BAIXAR PROPOSTA PREMIUM</h3></a>'
        st.markdown(href, unsafe_allow_html=True)
        st.balloons()
        st.success("Proposta premium gerada com sucesso!")

st.markdown(
    f"<p style='text-align:center; color:#666; margin-top:40px;'>Simulação elaborada por <b>{nome_assessor}</b> em {data_simulacao.strftime('%d/%m/%Y')}</p>",
    unsafe_allow_html=True
)
