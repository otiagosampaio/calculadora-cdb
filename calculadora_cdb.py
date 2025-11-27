import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
import requests
from PIL import Image as PILImage
from io import BytesIO as PIOBytesIO

# ===================== FUNÇÃO PARA LOGO COM PROPORÇÃO CORRETA =====================
def carregar_logo():
    url = "https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png"
    response = requests.get(url)
    img = PILImage.open(PIOBytesIO(response.content))
    largura, altura = img.size
    proporcao = altura / largura
    largura_desejada = 200 
    altura_calculada = largura_desejada * proporcao
    return Image(PIOBytesIO(response.content), width=largura_desejada, height=altura_calculada)

# ===================== CONFIGURAÇÃO =====================
st.set_page_config(page_title="Traders Corretora - CDB", layout="centered")

# ===================== LOGO + TÍTULO (Streamlit Display) =====================
st.markdown(
    """<div style="text-align: center; margin: 10px 0;">
        <img src="https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png" width="500">
    </div>""",
    unsafe_allow_html=True
)
st.markdown("<h2 style='text-align: center; color: #222;'>Calculadora de CDB Pré e Pós-fixado</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 17px; margin-bottom: 30px;'>Simule rendimentos com a calculadora de CDB e descubra o retorno esperado para o cliente!</p>", unsafe_allow_html=True)
st.markdown("---")

# ===================== DADOS DO CLIENTE =====================
st.subheader("Dados da Simulação")
c1, c2 = st.columns(2)
with c1:
    nome_cliente = st.text_input("Nome do Cliente", "João Silva")
    nome_assessor = st.text_input("Nome do Assessor", "Seu Nome")
    valor_investido = st.number_input("Valor investido", min_value=100.0, value=500000.0, step=1000.0)
    st.markdown(f"<h3 style='color:#2E8B57'>R$ {valor_investido:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
with c2:
    data_simulacao = st.date_input("Data da Simulação", datetime.date.today(), format="DD/MM/YYYY")
    tipo_cdb = st.selectbox("Tipo de CDB", ["Pré-fixado", "Pós-fixado (% do CDI)"])

st.markdown("---")

# ===================== PARÂMETROS =====================
with st.expander("Preferências do Investimento", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        data_aplicacao = st.date_input("Data da aplicação", datetime.date.today(), format="DD/MM/YYYY")
    with col2:
        data_vencimento = st.date_input("Data do resgate", data_aplicacao + relativedelta(months=+12), format="DD/MM/YYYY")

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
prazo_dias = (data_vencimento - data_aplicacao).days
if prazo_dias <= 0: st.error("Data de resgate deve ser posterior"); st.stop()

taxa_diaria = (1 + taxa_anual/100)**(1/dias_ano) - 1
montante_bruto = valor_investido * (1 + taxa_diaria)**prazo_dias
rendimento_bruto = montante_bruto - valor_investido

rendimento_apos_iof = rendimento_bruto
if prazo_dias < 30:
    iof_tab = [0.96,0.93,0.90,0.86,0.83,0.80,0.76,0.73,0.70,0.66,0.63,0.60,0.56,0.53,0.50,
               0.46,0.43,0.40,0.36,0.33,0.30,0.26,0.23,0.20,0.16,0.13,0.10,0.06,0.03,0.00]
    rendimento_apos_iof *= (1 - iof_tab[prazo_dias-1])

aliquota_ir = 22.5 if prazo_dias <= 180 else 20.0 if prazo_dias <= 360 else 17.5 if prazo_dias <= 720 else 15.0
ir = rendimento_apos_iof * (aliquota_ir/100)
montante_liquido = valor_investido + rendimento_apos_iof - ir
rendimento_liquido = montante_liquido - valor_investido

# ===================== GRÁFICO =====================
st.markdown("### Projeção da Rentabilidade")
datas_graf, bruto_graf, liquido_graf = [], [], []
data_temp = data_aplicacao

# Gera pontos do gráfico
for m in range(prazo_meses + 1):
    dias = (data_temp - data_aplicacao).days
    if m == 0: dias = 0
    if m == prazo_meses: dias = prazo_dias
        
    mont = valor_investido * (1 + taxa_diaria)**dias
    rend = mont - valor_investido
    ir_temp = rend * (0.225 if dias<=180 else 0.20 if dias<=360 else 0.175 if dias<=720 else 0.15)
    
    datas_graf.append(data_temp)
    bruto_graf.append(mont)
    liquido_graf.append(valor_investido + rend - ir_temp)
    
    data_temp += relativedelta(months=1)
    if data_temp > data_vencimento:
        data_temp = data_vencimento
        
if data_vencimento not in datas_graf:
    datas_graf.append(data_vencimento)
    bruto_graf.append(montante_bruto)
    liquido_graf.append(montante_liquido)

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(datas_graf, bruto_graf, label="CDB Pré + Pós (Bruta)", color="#6B48FF", linewidth=2)
ax.plot(datas_graf, liquido_graf, label="CDB Pré + Pós (Líquida)", color="#2E8B57", linewidth=2, linestyle="--")
ax.set_title("Projeção da Rentabilidade", fontsize=16, pad=20)
ax.set_ylabel("Valor em R$")
ax.legend(fontsize=10, loc='upper left')
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.xticks(rotation=0, ha='center')
plt.tight_layout()
st.pyplot(fig)

# ===================== RESULTADO FINAL (STREAMLIT) =====================
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
    current_title = ax.get_title()
    ax.set_title('') 
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    ax.set_title(current_title)
    buf.seek(0)
    return buf

# ===================== PDF 100% IGUAL AO EXEMPLO (Final com Preferências Corrigidas) =====================
def criar_pdf_perfeito():
    # 1. Configuração do Documento
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    story = []
    
    # 2. Estilos Personalizados
    styles = getSampleStyleSheet()
    AZUL_MARINHO_FUNDO = colors.HexColor("#0f172a") 
    
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
        alignment=4, # Justificado
        spaceBefore=5,
        spaceAfter=5
    ))
    
    brl_pdf = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # 3. Logo
    logo = carregar_logo()
    logo.hAlign = 'CENTER'
    story.append(logo)
    story.append(Spacer(1, 10*mm)) 
    
    # 4. Título Principal
    story.append(Paragraph("Simulação de Investimento - CDB Pré e Pós-fixado", styles['TitlePDF']))
    story.append(Paragraph("Projeção personalizada considerando IR e IOF", styles['SubTitlePDF']))
    
    # Linha divisória
    story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.lightgrey, spaceBefore=5, spaceAfter=10))

    # 5. DADOS DA SIMULAÇÃO
    story.append(Paragraph("DADOS DA SIMULAÇÃO", styles['SectionTitle']))
    
    data_formatada = [
        [Paragraph("Nome do cliente", styles['DataLabel']), 
         Paragraph(nome_cliente, styles['DataValue']), 
         Paragraph("Data da simulação", styles['DataLabel']), 
         Paragraph(data_simulacao.strftime('%d/%m/%Y'), styles['DataValue'])],
        
        [Paragraph("Valor investido", styles['DataLabel']), 
         Paragraph(brl_pdf(valor_investido), styles['DataValue']), 
         Paragraph("Tipo de CDB", styles['DataLabel']), 
         Paragraph(tipo_cdb.split('(')[0].strip(), styles['DataValue'])] 
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

    # Linha divisória
    story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.lightgrey, spaceBefore=5, spaceAfter=10))
    
    # 6. PREFERÊNCIAS DO INVESTIMENTO
    story.append(Paragraph("PREFERÊNCIAS DO INVESTIMENTO", styles['SectionTitle']))
    
    icone_valor = Paragraph("<font face='ZapfDingbats' size='10' color='#1e3a8a'>5</font>", styles['DataLabel'])
    icone_data = Paragraph("<font face='ZapfDingbats' size='10' color='#1e3a8a'>d</font>", styles['DataLabel'])
    icone_consideracoes = Paragraph("<font face='ZapfDingbats' size='10' color='#1e3a8a'>I</font>", styles['DataLabel'])
    
    prefs_data = [
        [icone_valor, Paragraph("Valor aplicado", styles['DataLabel']), 
         icone_data, Paragraph("Data do Vencimento", styles['DataLabel']), 
         icone_consideracoes, Paragraph("Considerações", styles['DataLabel'])],
        
        [Spacer(1,1), Paragraph(brl_pdf(valor_investido), styles['PrefValue']), 
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
    
    # Linha divisória
    story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.lightgrey, spaceBefore=10, spaceAfter=10)) 

    # 7. RESUMO DA OPERAÇÃO
    story.append(Paragraph("RESUMO DA OPERAÇÃO", styles['SectionTitle'])) 
    
    VERDE_RENTABILIDADE_STR = '#2E8B57' 
    
    meses = prazo_meses 
    if tipo_cdb == "Pré-fixado":
        taxa_label = f"{taxa_anual:.2f}% a.a."
    else: 
        try:
            taxa_label = f"{perc_cdi:.2f}% do CDI"
        except NameError:
            taxa_label = f"Taxa de mercado ({taxa_anual:.2f}% a.a.)"
            
    valor_liquido_formatado = f"<b><font color='{VERDE_RENTABILIDADE_STR}'>{brl_pdf(montante_liquido)}</font></b>" 
    
    resumo_texto = f"Com um investimento inicial de {brl_pdf(valor_investido)} em um CDB com taxa de {taxa_label} por um período de {meses} meses, o valor líquido será de {valor_liquido_formatado}."

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

    # 8. RESULTADO FINAL (Layout Corrigido + Borda Branca)
    
    # Novo Layout: Combinar Título e Dados em uma única tabela
    resultado_completo = [
        [Paragraph("<b>RESULTADO FINAL</b>", ParagraphStyle(name='ResultTitle', fontSize=10, fontName='Helvetica-Bold', alignment=1, textColor=colors.white, backColor=AZUL_MARINHO_FUNDO, leftPadding=15, rightPadding=15, topPadding=8, bottomPadding=8, spaceAfter=0)), 
         Paragraph("<b>RESULTADO FINAL</b>", ParagraphStyle(name='ResultTitle', fontSize=10, fontName='Helvetica-Bold', alignment=1, textColor=colors.white, backColor=AZUL_MARINHO_FUNDO, leftPadding=15, rightPadding=15, topPadding=8, bottomPadding=8, spaceAfter=0)),
         Paragraph("<b>RESULTADO FINAL</b>", ParagraphStyle(name='ResultTitle', fontSize=10, fontName='Helvetica-Bold', alignment=1, textColor=colors.white, backColor=AZUL_MARINHO_FUNDO, leftPadding=15, rightPadding=15, topPadding=8, bottomPadding=8, spaceAfter=0))],
        
        ["VALOR BRUTO", "IMPOSTOS", "VALOR LÍQUIDO"],
        [brl_pdf(montante_bruto), brl_pdf(ir + (rendimento_bruto - rendimento_apos_iof)), brl_pdf(montante_liquido)],
    ]
    
    t_res_final = Table(resultado_completo, colWidths=[total_width/3, total_width/3, total_width/3])
    t_res_final.hAlign = 'CENTER'

    t_res_final.setStyle(TableStyle([
        # Mesclar células para o título (o fundo azul marinho do topo já cobre)
        ('SPAN', (0,0), (2,0)), 
        
        # Estilo da Linha do Título (Resultado Final)
        ('BACKGROUND', (0,0), (2,0), AZUL_MARINHO_FUNDO), 
        # Borda Branca de 1pt ABAIXO do título
        ('LINEBELOW', (0,0), (2,0), 1, colors.white), 

        # Estilo da Linha de Rótulos (Valor Bruto, Impostos, Valor Líquido)
        ('BACKGROUND', (0,1), (2,1), AZUL_MARINHO_FUNDO), 
        ('TEXTCOLOR', (0,1), (2,1), colors.white),
        ('FONTSIZE', (0,1), (2,1), 10),
        ('FONTNAME', (0,1), (2,1), 'Helvetica-Bold'),
        ('TOPPADDING', (0,1), (2,1), 5),
        ('BOTTOMPADDING', (0,1), (2,1), 5),
        
        # Estilo da Linha de Valores
        ('BACKGROUND', (0,2), (2,2), AZUL_MARINHO_FUNDO), 
        ('TEXTCOLOR', (0,2), (2,2), colors.white),
        ('FONTSIZE', (0,2), (2,2), 16),
        ('FONTNAME', (0,2), (2,2), 'Helvetica-Bold'),
        ('TOPPADDING', (0,2), (2,2), 10),
        ('BOTTOMPADDING', (0,2), (2,2), 10),
        
        # Alinhamentos
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0, colors.transparent),
    ]))
    story.append(t_res_final)
    
    # Linha divisória após o Resultado Final
    story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.lightgrey, spaceBefore=10, spaceAfter=10)) 

    # 9. FUNDAMENTOS DO CDB (Asteriscos ajustados para negrito)
    story.append(Paragraph("FUNDAMENTOS DO CDB", styles['SectionTitle'])) 
    
    # Conteúdo de fundamentos com negrito ajustado
    fundamentos_texto = (
        "O <b>CDB</b> é um título de renda fixa emitido por bancos. É uma escolha segura por contar com a "
        "garantia do <b>FGC</b> (Fundo Garantidor de Créditos), que cobre até R$ 250.000 por CPF/instituição. "
        "A <b>Rentabilidade</b> pode ser Pré-fixada ou Pós-fixada (atrelada ao CDI). "
        "A <b>Liquidez</b> pode ser diária (reserva de emergência) ou no vencimento (maior retorno). "
        "O <b>IR</b> é regressivo (menor imposto em prazos maiores), e o <b>IOF</b> é isento após 30 dias."
    )
    
    story.append(Paragraph(fundamentos_texto, styles['FundamentosStyle']))
    
    # Espaçamento antes do gráfico
    story.append(Spacer(1, 10*mm)) 
    
    # 10. PROJEÇÃO DA RENTABILIDADE (Gráfico)
    story.append(Paragraph("PROJEÇÃO DA RENTABILIDADE", styles['SectionTitle']))
    
    img = Image(grafico_png(), width=180*mm, height=90*mm)
    img.hAlign = 'CENTER'
    story.append(img)
    story.append(Paragraph("Projeção baseada em taxas atuais, podendo variar conforme mercado", 
                           ParagraphStyle(name='GraphNote', fontSize=9, alignment=1, textColor=colors.HexColor('#666666'), spaceAfter=20*mm)))

    # 11. Rodapé 
    story.append(Paragraph(f"Simulação elaborada por <b>{nome_assessor}</b> em {data_simulacao.strftime('%d/%m/%Y')}", styles['Footer']))


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
    f"<p style='text-align:center; color:#666; margin-top:40px;'>Simulação elaborada por <b>{nome_assessor}</b> em {data_simulacao.strftime('%d/%m/%Y')}</p>",
    unsafe_allow_html=True
)
