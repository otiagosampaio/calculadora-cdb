import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from fpdf2 import FPDF  # Agora funciona com acentos!

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

# ===================== GRÁFICO =====================
st.markdown("### Evolução do Investimento")
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
ax.plot(datas_graf, bruto_graf, label="Montante Bruto", color="#6B48FF", linewidth=4)
ax.plot(datas_graf, liquido_graf, label="Montante Líquido (após IR)", color="#2E8B57", linewidth=4, linestyle="--")
ax.set_title("Evolução do Investimento", fontsize=18, fontweight="bold", color="#222", pad=20)
ax.set_ylabel("Valor em R$", fontsize=12)
ax.legend(fontsize=12, fancybox=True, shadow=True)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

# ===================== RESULTADO =====================
st.markdown("---")
st.markdown("<h2 style='text-align:center; color:#6B48FF;'>Resultado Final</h2>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
brl = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
col1.metric("Montante Bruto", brl(montante_bruto))
col2.metric("Rendimento Bruto", brl(rendimento_bruto))
col3.metric("Montante Líquido", brl(montante_liquido), delta=brl(rendimento_liquido))

# ===================== PDF PREMIUM =====================
def grafico_png():
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    return buf

class PDF(FPDF):
    def header(self):
        self.image("https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png", 15, 10, 50)
        self.set_fill_color(107, 72, 255)
        self.rect(0, 35, 210, 10, 'F')
        self.set_font("Helvetica", "B", 26)
        self.set_text_color(255, 255, 255)
        self.set_y(38)
        self.cell(0, 10, "SIMULAÇÃO DE INVESTIMENTO", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "Traders Corretora • Assessoria de Investimentos", align="C")

def criar_pdf():
    pdf = PDF()
    pdf.add_page()

    # Cliente em destaque
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(107, 72, 255)
    pdf.cell(0, 15, nome_cliente.upper(), ln=True, align="C")
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, f"Simulação elaborada por {nome_assessor} • {data_simulacao.strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(20)

    # Resultados
    pdf.set_fill_color(248, 245, 255)
    pdf.set_draw_color(107, 72, 255)
    pdf.rect(15, pdf.get_y(), 180, 80, 'FD')

    pdf.set_xy(20, pdf.get_y() + 12)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(107, 72, 255)
    pdf.cell(0, 10, "Resultado da Aplicação", ln=True)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, f"Valor Investido:           {brl(investimento)}", ln=True)
    pdf.set_text_color(107, 72, 255)
    pdf.cell(0, 10, f"Montante Bruto:            {brl(montante_bruto)}", ln=True)
    pdf.set_text_color(46, 139, 87)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, f"Montante Líquido:          {brl(montante_liquido)}", ln=True)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, f"Rendimento Líquido:        +{brl(rendimento_liquido)}", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Alíquota de IR aplicada: {aliquota_ir}%", ln=True)
    pdf.ln(20)

    # Gráfico
    png = grafico_png()
    pdf.image(png, x=15, y=None, w=180)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# ===================== BOTÃO PDF =====================
st.markdown("---")
if st.button("GERAR PROPOSTA PREMIUM (PDF)", type="primary", use_container_width=True):
    with st.spinner("Gerando sua proposta premium..."):
        pdf_data = criar_pdf()
        b64 = base64.b64encode(pdf_data).decode()
        nome_arq = f"Proposta_CDB_{nome_cliente.replace(' ', '_')}_{data_simulacao.strftime('%d%m%Y')}.pdf"
        href = f'<a href="data:application/pdf;base64,{b64}" download="{nome_arq}"><h3>BAIXAR PROPOSTA PREMIUM</h3></a>'
        st.markdown(href, unsafe_allow_html=True)
        st.balloons()
        st.success("Proposta premium gerada com sucesso!")

# ===================== RODAPÉ =====================
st.markdown(
    f"""
    <div style="text-align:center; padding:30px; background:linear-gradient(135deg,#f5f0ff,#ede9ff); border-radius:20px; margin-top:40px;">
       <p style="font-size:18px;"><strong>Simulação elaborada por {nome_assessor}</strong><br>
       em <strong>{data_simulacao.strftime('%d/%m/%Y')}</strong> para <strong>{nome_cliente}</strong></p>
       <p style="color:#6B48FF; font-size:22px; margin-top:20px;"><strong>Traders Corretora • Assessoria de Investimentos</strong></p>
    </div>
    """,
    unsafe_allow_html=True
)

if st.button("Nova simulação"):
    st.experimental_rerun()
