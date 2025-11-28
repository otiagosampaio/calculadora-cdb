import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
import requests
from PIL import Image as PILImage
from io import BytesIO as PIOBytesIO 
import re

# ===================== CONFIGURAÇÃO DE CORES (TEMA CLARO PADRÃO) =====================
URL_LOGO_WHITE = "https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png"
TEXTO_PRINCIPAL_ST = "#222222"  # Preto/Escuro para títulos no Streamlit
TEXTO_SECUNDARIO_ST = "#666666" # Cinza escuro para textos menores
FUNDO_GRAFICO = "white"         # Fundo Gráfico Claro
COR_EIXO_GRAFICO = "#333333"    # Cor de Eixo Gráfico Claro

VERDE_DESTAQUE = '#2E8B57'      # Cor de destaque (Verde)
AZUL_TABELA_PDF = colors.HexColor("#0f172a") # Cor escura para tabelas no PDF (mantido o original)


# ===================== FUNÇÃO PARA LOGO COM PROPORÇÃO CORRETA =====================
def carregar_logo():
    # Usando a URL do logo com fundo branco (padrão do tema claro)
    url = URL_LOGO_WHITE 
    response = requests.get(url)
    img = PILImage.open(PIOBytesIO(response.content))
    largura, altura = img.size
    proporcao = altura / largura
    largura_desejada = 200 
    altura_calculada = largura_desejada * proporcao
    return Image(PIOBytesIO(response.content), width=largura_desejada, height=altura_calculada)

# ===================== FUNÇÃO DE FORMATAÇÃO MONETÁRIA =====================
def formatar_moeda(valor_str):
    valor_limpo = re.sub(r'[^\d,]', '', valor_str)
    
    if ',' in valor_limpo:
        partes = valor_limpo.split(',')
        if len(partes) > 2:
            valor_limpo = partes[0] + ',' + partes[1]
        
    valor_sem_pontos = valor_limpo.replace('.', '')
    
    if not valor_sem_pontos:
        return "0,00"

    try:
        if ',' in valor_sem_pontos:
            inteiro, decimal = valor_sem_pontos.split(',')
            decimal = decimal[:2] 
            decimal = decimal.ljust(2, '0') 
            valor_float = float(f"{inteiro}.{decimal}")
        else:
            valor_float = float(valor_sem_pontos)

        return f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except ValueError:
        return valor_str 

def desformatar_moeda(valor_formatado):
    valor_float_str = valor_formatado.replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(valor_float_str)
    except ValueError:
        return 0.0

# ===================== CONFIGURAÇÃO =====================
st.set_page_config(page_title="Traders Corretora - CDB", layout="centered")

# ===================== LOGO + TÍTULO (Streamlit Display) =====================
st.markdown(
    f"""<div style="text-align: center; margin: 10px 0;">
        <img src="{URL_LOGO_WHITE}" width="500">
    </div>""",
    unsafe_allow_html=True
)
# Título principal com cor do tema claro
st.markdown(f"<h2 style='text-align: center; color: {TEXTO_PRINCIPAL_ST};'>Calculadora de Investimentos</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {TEXTO_SECUNDARIO_ST}; font-size: 17px; margin-bottom: 30px;'>Simule rendimentos com a calculadora de CDB e descubra o retorno esperado para o cliente!</p>", unsafe_allow_html=True)
st.markdown("---")

# ===================== PARÂMETROS E ESTADOS INICIAIS =====================
taxa_cdi_mercado = 14.90 
taxa_cdi = taxa_cdi_mercado 
perc_cdi = 0.0
taxa_anual = 0.0

if 'valor_input' not in st.session_state:
    st.session_state['valor_input'] = "500.000,00"

# ===================== DADOS DA SIMULAÇÃO (AJUSTADOS) =====================
st.subheader("Dados da Simulação")
c1, c2 = st.columns(2)

with c1:
    nome_cliente = st.text_input("Nome do Cliente", "João Silva")
    nome_assessor = st.text_input("Nome do Assessor", "Seu Nome")

    valor_investido_str = st.text_input(
        label="Valor investido", 
        value=st.session_state['valor_input'], 
        placeholder="Digite o valor (Ex: 500000,00)",
        key="valor_bruto_input"
    )
    
    valor_formatado_display = formatar_moeda(valor_investido_str)
    
    if valor_investido_str != valor_formatado_display:
        st.session_state['valor_input'] = valor_formatado_display
    
    valor_investido = desformatar_moeda(valor_formatado_display)
    
    # Cor de destaque (Verde)
    st.markdown(f"<h3 style='color:{VERDE_DESTAQUE}'>R$ {st.session_state['valor_input']}</h3>", unsafe_allow_html=True)
    
with c2:
    data_simulacao = st.date_input("Data da Simulação", datetime.date.today(), format="DD/MM/YYYY")
    tipo_cdb = st.selectbox("Tipo de CDB", ["Pré-fixado", "Pós-fixado (% do CDI)"])

    # Input de Taxa 
    if tipo_cdb == "Pós-fixado (% do CDI)":
        taxa_cdi = st.number_input("Taxa CDI anual (Benchmark) (%)", value=taxa_cdi_mercado, step=0.05)
        perc_cdi = st.number_input("Percentual do CDI (%)", value=125.0, step=1.0)
        taxa_anual = taxa_cdi * (perc_cdi / 100)
        dias_ano = 252
    else:
        taxa_anual = st.number_input("Taxa pré-fixada anual (%)", value=17.00, step=0.05)
        dias_ano = 360
        perc_cdi = 0.0

st.markdown("---")

# ===================== PREFERÊNCIAS DO INVESTIMENTO (APENAS DATAS) =====================
with st.expander("Preferências do Investimento", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        data_aplicacao = st.date_input("Data da aplicação", datetime.date.today(), format="DD/MM/YYYY")
    with col2:
        data_vencimento = st.date_input("Data do resgate", data_aplicacao + relativedelta(months=+12), format="DD/MM/YYYY")

# ===================== CÁLCULOS CDB =====================
if valor_investido <= 0: st.warning("Valor investido deve ser maior que zero."); st.stop()

prazo_meses = (data_vencimento.year - data_aplicacao.year)*12 + (data_vencimento.month - data_aplicacao.month)
if data_vencimento.day < data_aplicacao.day: prazo_meses -= 1
prazo_dias = (data_vencimento - data_aplicacao).days
if prazo_dias <= 0: st.error("Data de resgate deve ser posterior"); st.stop()

taxa_diaria = (1 + taxa_anual/100)**(1/dias_ano) - 1
montante_bruto = valor_investido * (1 + taxa_diaria)**prazo_dias
rendimento_bruto = montante_bruto - valor_investido # RENTABILIDADE BRUTA

rendimento_apos_iof = rendimento_bruto
if prazo_dias < 30:
    iof_tab = [0.96,0.93,0.90,0.86,0.83,0.80,0.76,0.73,0.70,0.66,0.63,0.60,0.56,0.53,0.50,
               0.46,0.43,0.40,0.36,0.33,0.30,0.26,0.23,0.20,0.16,0.13,0.10,0.06,0.03,0.00]
    rendimento_apos_iof *= (1 - iof_tab[prazo_dias-1])

aliquota_ir = 22.5 if prazo_dias <= 180 else 20.0 if prazo_dias <= 360 else 17.5 if prazo_dias <= 720 else 15.0
ir = rendimento_apos_iof * (aliquota_ir/100)
montante_liquido = valor_investido + rendimento_apos_iof - ir
rendimento_liquido = montante_liquido - valor_investido # RENTABILIDADE LÍQUIDA

# ===================== CÁLCULOS BENCHMARKS =====================
taxa_cdi_anual = taxa_cdi / 100 
taxa_poupanca_anual = 0.0617
taxa_cdi_diaria_corrida = (1 + taxa_cdi_anual)**(1/365) - 1
taxa_poupanca_diaria_corrida = (1 + taxa_poupanca_anual)**(1/365) - 1

# ===================== GRÁFICO (Streamlit) =====================
st.markdown("### Projeção da Rentabilidade")
datas_graf, bruto_graf = [], []
bruto_cdi_graf, bruto_poupanca_graf = [], [] 
data_temp = data_aplicacao

for m in range(prazo_meses + 1):
    dias = (data_temp - data_aplicacao).days
    if m == 0: dias = 0
    if m == prazo_meses: dias = prazo_dias
        
    mont = valor_investido * (1 + taxa_diaria)**dias
    
    datas_graf.append(data_temp)
    bruto_graf.append(mont)
    
    mont_cdi = valor_investido * (1 + taxa_cdi_diaria_corrida)**dias
    mont_poupanca = valor_investido * (1 + taxa_poupanca_diaria_corrida)**dias
    
    bruto_cdi_graf.append(mont_cdi)
    bruto_poupanca_graf.append(mont_poupanca)
    
    data_temp += relativedelta(months=1)
    if data_temp > data_vencimento:
        data_temp = data_vencimento
        
if data_vencimento not in datas_graf:
    datas_graf.append(data_vencimento)
    bruto_graf.append(montante_bruto)
    
    bruto_cdi_graf.append(valor_investido * (1 + taxa_cdi_diaria_corrida)**prazo_dias)
    bruto_poupanca_graf.append(valor_investido * (1 + taxa_poupanca_diaria_corrida)**prazo_dias)

# Plotagem com tema claro
fig, ax = plt.subplots(figsize=(12, 6))
fig.set_facecolor(FUNDO_GRAFICO) 
ax.set_facecolor(FUNDO_GRAFICO)
ax.tick_params(axis='x', colors=COR_EIXO_GRAFICO)
ax.tick_params(axis='y', colors=COR_EIXO_GRAFICO)
ax.yaxis.label.set_color(COR_EIXO_GRAFICO)
ax.title.set_color(TEXTO_PRINCIPAL_ST)

ax.plot(datas_graf, bruto_graf, label="CDB Bruto", color="#6B48FF", linewidth=2, alpha=0.9)
ax.plot(datas_graf, bruto_cdi_graf, label="Benchmark: CDI", color="#FF5733", linestyle="--", linewidth=1.5)
ax.plot(datas_graf, bruto_poupanca_graf, label="Benchmark: Poupança", color="#337AFF", linestyle=":", linewidth=1.5)

ax.set_title("Projeção da Rentabilidade Bruta vs. Benchmarks", fontsize=16, pad=20)
ax.set_ylabel("Valor em R$")
ax.legend(fontsize=10, loc='upper left', facecolor=FUNDO_GRAFICO, edgecolor=COR_EIXO_GRAFICO, labelcolor=COR_EIXO_GRAFICO)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# ANOTAÇÕES DE VALORES FINAIS NO GRÁFICO (cor adaptativa)
dados_finais = [
    (montante_bruto, "#6B48FF", "CDB"),
    (bruto_cdi_graf[-1], "#FF5733", "CDI"),
    (bruto_poupanca_graf[-1], "#337AFF", "Poupança"),
]

brl_anot = lambda v: f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

for valor, cor, nome in dados_finais:
    ax.annotate(brl_anot(valor),
                xy=(data_vencimento, valor),
                xytext=(5, 0),
                textcoords='offset points',
                color=TEXTO_PRINCIPAL_ST, 
                fontsize=9,
                fontweight='bold',
                ha='left',
                va='center')
    

plt.xticks(rotation=0, ha='center')
plt.tight_layout()
st.pyplot(fig)

# ===================== RESULTADO FINAL (STREAMLIT) =====================
st.markdown("---")
# Título com cor do tema claro
st.markdown(f"<h2 style='text-align:center; color:{TEXTO_PRINCIPAL_ST};'>Resultado Final</h2>", unsafe_allow_html=True)

# Exibição simplificada no Streamlit (mantendo o formato original de 3 colunas)
col1, col2, col3 = st.columns(3)
brl = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
col1.metric("Valor Bruto", brl(montante_bruto))
col2.metric("Impostos", brl(ir + (rendimento_bruto - rendimento_apos_iof)))
col3.metric("Valor Líquido", brl(montante_liquido), delta=brl(rendimento_liquido))

# ===================== GERAR PNG DO GRÁFICO (FUNDO BRANCO PARA PDF) =====================
def grafico_png():
    # Salva o gráfico com fundo branco para o PDF
    buf = BytesIO()
    current_title = ax.get_title()
    
    # Temporariamente ajusta o fundo do plot para branco antes de salvar para o PDF
    fig.set_facecolor('white') 
    ax.set_facecolor('white')
    ax.tick_params(axis='x', colors='#333333')
    ax.tick_params(axis='y', colors='#333333')
    ax.yaxis.label.set_color('#333333')
    ax.title.set_color('#000000')
    ax.legend(fontsize=10, loc='upper left', facecolor='white', edgecolor='#333333', labelcolor='#333333')

    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white') 
    
    # Restaura as cores originais do gráfico para a exibição no Streamlit
    fig.set_facecolor(FUNDO_GRAFICO) 
    ax.set_facecolor(FUNDO_GRAFICO)
    ax.tick_params(axis='x', colors=COR_EIXO_GRAFICO)
    ax.tick_params(axis='y', colors=COR_EIXO_GRAFICO)
    ax.yaxis.label.set_color(COR_EIXO_GRAFICO)
    ax.title.set_color(TEXTO_PRINCIPAL_ST)
    ax.legend(fontsize=10, loc='upper left', facecolor=FUNDO_GRAFICO, edgecolor=COR_EIXO_GRAFICO, labelcolor=COR_EIXO_GRAFICO)
    
    buf.seek(0)
    return buf

# ===================== PDF GERAÇÃO (Tema Claro com 4 Colunas no Resultado Final) =====================
def criar_pdf_perfeito():
    # 1. Configuração do Documento
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    story = []
    
    # 2. Estilos Personalizados (Branco/Padrão para o PDF)
    styles = getSampleStyleSheet()
    
    # Cores fixas para PDF (Tema Claro)
    styles.add(ParagraphStyle(name='TitlePDF', fontSize=18, fontName='Helvetica-Bold', alignment=1, spaceAfter=7*mm, textColor=colors.HexColor('#000000')))
    styles.add(ParagraphStyle(name='SubTitlePDF', fontSize=10, alignment=1, textColor=colors.HexColor('#666666'), spaceAfter=10*mm)) 
    styles.add(ParagraphStyle(name='SectionTitle', fontSize=10, fontName='Helvetica-Bold', spaceAfter=5*mm, textColor=colors.HexColor('#333333'), alignment=0)) 
    styles.add(ParagraphStyle(name='DataLabel', fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#666666'), alignment=0))
    styles.add(ParagraphStyle(name='DataValue', fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#333333'), alignment=0))
    styles.add(ParagraphStyle(name='Footer', fontSize=9, alignment=1, textColor=colors.HexColor('#666666')))
    styles.add(ParagraphStyle(name='PrefValue', fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#333333'), alignment=0, spaceBefore=3)) 
    
    styles.add(ParagraphStyle(name='ResumoStyle',
        fontName='Helvetica',
        fontSize=11, 
        textColor=colors.black,
        alignment=1, 
        spaceBefore=5,
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(name='FundamentosStyle', 
        fontName='Helvetica',
        fontSize=9, 
        textColor=colors.HexColor('#444444'),
        alignment=4, 
        spaceBefore=5,
        spaceAfter=5
    ))
    
    styles.add(ParagraphStyle(
        name='Disclaimer', 
        fontSize=7, 
        fontName='Helvetica-Oblique', 
        alignment=4, 
        textColor=colors.HexColor('#666666'), 
        spaceBefore=3*mm, 
        spaceAfter=0*mm
    ))
    
    # NOVO ESTILO: Título de Resultado Final com fonte maior (18pt) e padding ajustado
    styles.add(ParagraphStyle(
        name='ResultTitleLarge', 
        fontSize=18, 
        fontName='Helvetica-Bold', 
        alignment=1, 
        textColor=colors.white, 
        backColor=AZUL_TABELA_PDF, 
        leftPadding=15, 
        rightPadding=15, 
        topPadding=12, # AUMENTADO
        bottomPadding=12, # AUMENTADO
        spaceAfter=0
    ))
    
    brl_pdf = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # 3. Logo (Sempre usando o logo BG-WHITE no PDF)
    url_logo_pdf = URL_LOGO_WHITE
    response_pdf = requests.get(url_logo_pdf)
    img_pil_pdf = PILImage.open(PIOBytesIO(response_pdf.content))
    largura_pdf, altura_pdf = img_pil_pdf.size
    proporcao_pdf = altura_pdf / largura_pdf
    largura_desejada_pdf = 200 
    altura_calculada_pdf = largura_desejada_pdf * proporcao_pdf
    logo = Image(PIOBytesIO(response_pdf.content), width=largura_desejada_pdf, height=altura_calculada_pdf)
    logo.hAlign = 'CENTER'
    story.append(logo)
    story.append(Spacer(1, 10*mm)) 
    
    # 4. Título Principal
    story.append(Paragraph("Simulação de Investimento - CDB Pré e Pós-fixado", styles['TitlePDF']))
    story.append(Paragraph("Projeção personalizada considerando IR e IOF", styles['SubTitlePDF']))
    
    story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.lightgrey, spaceBefore=5, spaceAfter=10))

    # 5. DADOS DA SIMULAÇÃO
    story.append(Paragraph("DADOS DA SIMULAÇÃO", styles['SectionTitle']))
    
    taxa_retorno_pdf = f"{taxa_anual:.2f}% a.a." if tipo_cdb == "Pré-fixado" else f"{perc_cdi:.2f}% do CDI"
    
    data_formatada = [
        [Paragraph("Nome do cliente", styles['DataLabel']), 
         Paragraph(nome_cliente, styles['DataValue']), 
         Paragraph("Data da simulação", styles['DataLabel']), 
         Paragraph(data_simulacao.strftime('%d/%m/%Y'), styles['DataValue'])],
        
        [Paragraph("Valor investido", styles['DataLabel']), 
         Paragraph(brl_pdf(valor_investido), styles['DataValue']), 
         Paragraph("Tipo de CDB", styles['DataLabel']), 
         Paragraph(tipo_cdb.split('(')[0].strip(), styles['DataValue'])],
         
        [Paragraph("Taxa de Retorno", styles['DataLabel']), 
         Paragraph(taxa_retorno_pdf, styles['DataValue']), 
         Paragraph("Benchmark CDI", styles['DataLabel']), 
         Paragraph(f"{taxa_cdi:.2f}% a.a.", styles['DataValue'])]
    ]
    
    total_width = A4[0] - 30*mm 
    colWidths = [total_width * 0.22, total_width * 0.28, total_width * 0.22, total_width * 0.28] 
    t_dados = Table(data_formatada, colWidths=colWidths)
    
    t_dados.hAlign = 'LEFT' 

    t_dados.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_dados)
    
    story.append(Spacer(1, 5*mm)) 

    story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.lightgrey, spaceBefore=5, spaceAfter=10))
    
    # 6. PREFERÊNCIAS DO INVESTIMENTO
    story.append(Paragraph("PREFERÊNCIAS DO INVESTIMENTO", styles['SectionTitle']))
    
    icone_data_app = Paragraph("<font face='ZapfDingbats' size='10' color='#1e3a8a'>d</font>", styles['DataLabel'])
    icone_data_venc = Paragraph("<font face='ZapfDingbats' size='10' color='#1e3a8a'>d</font>", styles['DataLabel'])
    icone_consideracoes = Paragraph("<font face='ZapfDingbats' size='10' color='#1e3a8a'>I</font>", styles['DataLabel'])
    
    prefs_data = [
        [icone_data_app, Paragraph("Data da Aplicação", styles['DataLabel']), 
         icone_data_venc, Paragraph("Data do Vencimento", styles['DataLabel']), 
         icone_consideracoes, Paragraph("Considerações", styles['DataLabel'])],
        
        [Spacer(1,1), Paragraph(data_aplicacao.strftime('%d/%m/%Y'), styles['PrefValue']), 
         Spacer(1,1), Paragraph(data_vencimento.strftime('%d/%m/%Y'), styles['PrefValue']), 
         Spacer(1,1), Paragraph("IR, IOF", styles['PrefValue'])]
    ]
    
    largura_pref = total_width / 3
    colWidths_prefs = [8*mm, largura_pref - 8*mm, 8*mm, largura_pref - 8*mm, 8*mm, largura_pref - 8*mm]
    
    t_prefs = Table(prefs_data, colWidths=colWidths_prefs)
    t_prefs.hAlign = 'LEFT'
    
    t_prefs.setStyle(TableStyle([
        ('GRID', (0,0), (1,1), 0.5, colors.lightgrey), 
        ('GRID', (2,0), (3,1), 0.5, colors.lightgrey), 
        ('GRID', (4,0), (5,1), 0.5, colors.lightgrey), 
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (0,1), 'TOP'),
        ('VALIGN', (2,0), (2,1), 'TOP'),
        ('VALIGN', (4,0), (4,1), 'TOP'),
    ]))
    
    story.append(t_prefs)
    
    story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.lightgrey, spaceBefore=10, spaceAfter=10)) 

    # 7. RESUMO DA OPERAÇÃO
    story.append(Paragraph("RESUMO DA OPERAÇÃO", styles['SectionTitle'])) 
    
    meses = prazo_meses 
    
    valor_liquido_formatado = f"<b><font color='{VERDE_DESTAQUE}'>{brl_pdf(montante_liquido)}</font></b>" 
    
    taxa_retorno_resumo = f"{taxa_anual:.2f}% a.a." if tipo_cdb == "Pré-fixado" else f"{perc_cdi:.2f}% do CDI"
    
    resumo_texto = f"Com um investimento inicial de {brl_pdf(valor_investido)} em um CDB com taxa de {taxa_retorno_resumo} por um período de {meses} meses, o valor líquido será de {valor_liquido_formatado}."

    resumo_paragrafo = Paragraph(resumo_texto, styles['ResumoStyle'])

    t_resumo = Table([[resumo_paragrafo]], colWidths=[total_width])
    t_resumo.hAlign = 'CENTER'

    t_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERPADDING', (0,0), (-1,-1), 0), 
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    story.append(t_resumo)
    
    story.append(Spacer(1, 5*mm)) 

    # 8. RESULTADO FINAL (NOVO FORMATO: 4 Colunas com Ajustes de Fonte/Espaçamento)
    
    # NOVOS DADOS (Incluindo o Principal, conforme solicitado)
    valor_final_bruto = montante_bruto  # Valor Bruto = Principal + Rentabilidade Bruta
    valor_final_liquido = montante_liquido # Valor Líquido = Principal + Rentabilidade Líquida
    impostos_totais = ir + (rendimento_bruto - rendimento_apos_iof)

    resultado_completo = [
        # Linha 1: Título principal (Ajustado o Padding para mais espaço)
        [Paragraph("<b>RESULTADO FINAL</b>", styles['ResultTitleLarge']), 
         "", 
         "", 
         ""],
        
        # Linha 2: Cabeçalho das 4 colunas (Novos títulos e fonte menor)
        ["VALOR INVESTIDO", "VALOR BRUTO", "IMPOSTOS", "VALOR LÍQUIDO"], 
        
        # Linha 3: Valores das 4 colunas (agora contêm o principal e fonte menor)
        [brl_pdf(valor_investido), 
         brl_pdf(valor_final_bruto), 
         brl_pdf(impostos_totais), 
         brl_pdf(valor_final_liquido)],
    ]
    
    colWidths_4 = [total_width/4] * 4
    t_res_final = Table(resultado_completo, colWidths=colWidths_4)
    t_res_final.hAlign = 'CENTER'

    t_res_final.setStyle(TableStyle([
        # Título principal (RESULTADO FINAL)
        ('SPAN', (0,0), (3,0)), 
        ('BACKGROUND', (0,0), (3,0), AZUL_TABELA_PDF), 
        ('LINEBELOW', (0,0), (3,0), 1, colors.white), 
        
        # Cabeçalho das 4 colunas (Diminuindo a fonte para caber)
        ('BACKGROUND', (0,1), (3,1), AZUL_TABELA_PDF), 
        ('TEXTCOLOR', (0,1), (3,1), colors.white),
        ('FONTSIZE', (0,1), (3,1), 9), # FONTE DIMINUÍDA
        ('FONTNAME', (0,1), (3,1), 'Helvetica-Bold'),
        ('TOPPADDING', (0,1), (3,1), 4),
        ('BOTTOMPADDING', (0,1), (3,1), 4),
        
        # Valores das 4 colunas (Diminuindo a fonte para caber)
        ('BACKGROUND', (0,2), (3,2), AZUL_TABELA_PDF), 
        ('TEXTCOLOR', (0,2), (3,2), colors.white),
        ('FONTSIZE', (0,2), (3,2), 14), # FONTE DIMINUÍDA
        ('FONTNAME', (0,2), (3,2), 'Helvetica-Bold'),
        ('TOPPADDING', (0,2), (3,2), 8),
        ('BOTTOMPADDING', (0,2), (3,2), 8),
        
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0, colors.transparent),
    ]))
    story.append(t_res_final)
    
    story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.lightgrey, spaceBefore=10, spaceAfter=10)) 

    # 9. FUNDAMENTOS DO CDB
    story.append(Paragraph("FUNDAMENTOS DO CDB", styles['SectionTitle'])) 
    
    fundamentos_texto_p1 = (
        "O <b>CDB</b> (Certificado de Depósito Bancário) é um título de renda fixa emitido por bancos para "
        "captar recursos. É considerado um investimento de baixo risco e conta com a garantia do "
        "<b>FGC</b> (Fundo Garantidor de Créditos), que cobre até R$ 250.000 por CPF e por instituição financeira, "
        "oferecendo segurança ao investidor. A rentabilidade pode ser **Pré-fixada** (taxa definida no início) "
        "ou **Pós-fixada** (geralmente atrelada a um percentual do CDI)."
    )
    story.append(Paragraph(fundamentos_texto_p1, styles['FundamentosStyle']))

    story.append(Spacer(1, 3*mm)) 

    fundamentos_texto_p2 = (
        "Em relação às características de resgate, a **Liquidez** do CDB pode ser diária (ideal para reserva de emergência) "
        "ou apenas no vencimento (oferecendo historicamente maior retorno). A tributação segue a tabela regressiva do "
        "<b>Imposto de Renda (IR)</b>, onde o imposto diminui quanto maior o prazo do investimento (chegando a 15% após 720 dias). "
        "O <b>Imposto sobre Operações Financeiras (IOF)</b> é isento para resgates feitos após 30 dias."
    )
    story.append(Paragraph(fundamentos_texto_p2, styles['FundamentosStyle']))
    
    story.append(Spacer(1, 5*mm)) 
    
    story.append(PageBreak()) 
    
    # 10. PROJEÇÃO DA RENTABILIDADE (Gráfico com Benchmarks) - Página 2
    story.append(Paragraph("PROJEÇÃO DA RENTABILIDADE BRUTA vs. BENCHMARKS", styles['SectionTitle']))
    
    img = Image(grafico_png(), width=180*mm, height=90*mm)
    img.hAlign = 'CENTER'
    story.append(img)
    
    nota_benchmarks = (
        f"Benchmarks: CDI ({taxa_cdi:.2f}% a.a.) e Poupança (Proxy 6.17% a.a.). " 
        "Projeção baseada em taxas atuais, podendo variar conforme mercado. Rentabilidades dos benchmarks são brutas (sem IR)."
    )
    
    story.append(Paragraph(nota_benchmarks, 
                           ParagraphStyle(name='GraphNote', fontSize=9, alignment=1, textColor=colors.HexColor('#666666'), spaceAfter=10*mm))) 

    # 11. BLOCO: COMPARAÇÃO DE RESULTADOS BRUTOS
    story.append(Paragraph("COMPARATIVO DE RESULTADOS BRUTOS (No Vencimento)", styles['SectionTitle'])) 

    valor_bruto_cdb = montante_bruto
    valor_bruto_cdi = bruto_cdi_graf[-1] 
    valor_bruto_poupanca = bruto_poupanca_graf[-1]

    valores_comparacao = [valor_bruto_cdb, valor_bruto_cdi, valor_bruto_poupanca]
    max_valor = max(valores_comparacao)
    
    def formatar_valor_comparacao(valor):
        cor = VERDE_DESTAQUE if valor == max_valor else '#333333'
        return Paragraph(f"<b><font size='12' color='{cor}'>{brl_pdf(valor)}</font></b>", 
                         ParagraphStyle(name='CompValue', alignment=1, fontName='Helvetica'))

    dados_comparacao = [
        ["CDB (Simulado)", "CDI (Benchmark)", "Poupança (Benchmark)"],
        [formatar_valor_comparacao(valor_bruto_cdb), 
         formatar_valor_comparacao(valor_bruto_cdi),
         formatar_valor_comparacao(valor_bruto_poupanca)]
    ]
    
    colWidths_comp = [total_width/3] * 3
    t_comparacao = Table(dados_comparacao, colWidths=colWidths_comp)
    t_comparacao.hAlign = 'CENTER'

    t_comparacao.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')), 
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#333333')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,1), colors.white), 
    ]))
    
    story.append(t_comparacao)
    
    story.append(Spacer(1, 10*mm)) 
    
    # 12. Rodapé personalizado (Assessor)
    story.append(Paragraph(f"Simulação elaborada por <b>{nome_assessor}</b> em {data_simulacao.strftime('%d/%m/%Y')}", styles['Footer']))

    # 13. Disclaimer Legal com Título
    story.append(Spacer(1, 5*mm)) 
    story.append(Paragraph("DISCLAIMER", styles['SectionTitle'])) 
    
    disclaimer_text = (
        "A Traders Distribuidora de Valores Mobiliários Ltda., com CNPJ sob o nº 62.280.490/0001-84 é uma instituição financeira autorizada a funcionar pelo Banco Central do Brasil, que atua como Participante de Negociação (PN) e realiza suas operações através de um Participante de Negociação Pleno (PNP), Terra Investimentos Ltda. Toda comunicação através da rede mundial de computadores está sujeita a interrupções ou atrasos, podendo impedir ou prejudicar o envio das ordens ou a recepção de informações atualizadas. Antes de tomar qualquer decisão de investimento, recomendamos que os investidores avaliem cuidadosamente seus objetivos financeiros e seu perfil de risco. A Traders DTVM exime-se de responsabilidade por danos sofridos por seus clientes, por força de falha de serviços disponibilizados por terceiros e não se responsabiliza por eventuais perdas financeiras decorrentes da negociação de ativos, nem garante a rentabilidade dos investimentos. O histórico de desempenho de qualquer ativo não assegura resultados futuros. A negociação em mercados financeiros está sujeita a volatilidade e pode envolver riscos significantes, incluindo, mas não se limitando ao risco de mercado, risco de liquidez e risco de crédito."
    )
    story.append(Paragraph(disclaimer_text, styles['Disclaimer']))


    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ===================== BOTÃO PDF =====================
st.markdown("---")
if st.button("BAIXAR PROPOSTA PREMIUM", type="primary", use_container_width=True):
    with st.spinner("Gerando sua proposta premium..."):
        pdf_data = criar_pdf_perfeito()
        b64 = base64.b64encode(pdf_data).decode()
        nome_arq = f"Proposta_CDB_{nome_cliente.replace(' ', '_')}.pdf"
        href = f'<a href="data:application/pdf;base64,{b64}" download="{nome_arq}"><h3 style="text-align:center; color:white;">BAIXAR PROPOSTA PREMIUM</h3></a>'
        st.markdown(href, unsafe_allow_html=True)
        st.balloons()
        st.success("Proposta premium gerada com sucesso!")

# ===================== RODAPÉ STREAMLIT =====================
st.markdown(
    f"<p style='text-align:center; color:{TEXTO_SECUNDARIO_ST}; margin-top:40px;'>Simulação elaborada por <b>{nome_assessor}</b> em {data_simulacao.strftime('%d/%m/%Y')}</p>",
    unsafe_allow_html=True
)
