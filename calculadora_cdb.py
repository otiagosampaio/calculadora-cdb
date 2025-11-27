import streamlit as st
import datetime
import pandas as pd
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta

# ===================== CONFIGURAÇÃO DA PÁGINA =====================
st.set_page_config(page_title="Traders Corretora - Calculadora CDB", layout="centered")

# ===================== 1) LOGO CENTRALIZADO =====================
st.markdown(
    """
    <div style="text-align: center; margin: 30px 0;">
        <img src="https://ik.imagekit.io/aufhkvnry/logo-traders__bg-white.png" width="480">
    </div>
    """,
    unsafe_allow_html=True
)

# ===================== 2) TÍTULOS NA ORDEM CERTA =====================
st.markdown("<h2 style='text-align: center; color: #222; margin-bottom: 8px;'>Calculadora de CDB Pré e Pós-fixado</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 17px; margin-bottom: 30px;'>Simulação personalizada de renda fixa com imposto de renda regressivo e IOF</p>", unsafe_allow_html=True)

st.markdown("---")

# ===================== DADOS DO CLIENTE =====================
st.subheader("Dados da Simulação")
col1, col2 = st.columns(2)
with col1:
    nome_cliente = st.text_input("Nome do Cliente", value="João Silva")
    nome_assessor = st.text_input("Nome do Assessor", value="Seu Nome")
with col2:
    data_simulacao = st.date_input("Data da Simulação", value=datetime.date.today(), format="DD/MM/YYYY")

st.markdown("---")

# ===================== PARÂMETROS DO INVESTIMENTO =====================
with st.expander("Parâmetros do Investimento", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        investimento = st.number_input("Valor investido (R$)", min_value=100.0, value=500000.0, step=1000.0, format="%.2f")
        st.markdown(f"<h3 style='color: #2E8B57; margin-top: 10px;'>R$ {investimento:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        data_aplicacao = st.date_input("Data da aplicação", value=datetime.date.today(), format="DD/MM/YYYY")
    with col_b:
        data_vencimento = st.date_input("Data do resgate/vencimento", value=data_aplicacao + relativedelta(months=+12), format="DD/MM/YYYY")
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

# ===================== CÁLCULO DO PRAZO E MONTANTE =====================
prazo_meses = (data_vencimento.year - data_aplicacao.year) * 12 + (data_vencimento.month - data_aplicacao.month)
if data_vencimento.day < data_aplicacao.day:
    prazo_meses -= 1
prazo_dias = prazo_meses * 30

if prazo_dias <= 0:
    st.error("A data de resgate deve ser posterior à data da aplicação.")
    st.stop()

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

# IR
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

# ===================== GRÁFICO DE EVOLUÇÃO =====================
st.markdown("### Evolução do Investimento")

# Cria série mensal
meses = list(range(0, prazo_meses + 1))
valores_bruto = []
valores_liquido = []
datas_grafico = []

data_atual = data_aplicacao
for m in meses:
    dias_passados = m * 30
    montante_temp = investimento * (1 + taxa_diaria) ** dias_passados
    rend_temp = montante_temp - investimento
    
    # IR estimado por período (simulação conservadora)
    if dias_passados <= 180:
        ir_temp = rend_temp * 0.225
    elif dias_passados <= 360:
        ir_temp = rend_temp * 0.20
    elif dias_passados <= 720:
        ir_temp = rend_temp * 0.175
    else:
        ir_temp = rend_temp * 0.15
    
    liquido_temp = investimento + rend_temp - ir_temp
    
    valores_bruto.append(round(montante_temp, 2))
    valores_liquido.append(round(liquido_temp, 2))
    datas_grafico.append(data_atual.strftime("%b/%Y"))
    data_atual += relativedelta(months=1)

df = pd.DataFrame({
    "Mês": datas_grafico,
    "Montante Bruto": valores_bruto,
    "Montante Líquido": valores_liquido
})

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Mês"], y=df["Montante Bruto"], name="Bruto", line=dict(color="#6B48FF", width=4)))
fig.add_trace(go.Scatter(x=df["Mês"], y=df["Montante Líquido"], name="Líquido (após IR)", line=dict(color="#2E8B57", width=4, dash="dot")))
fig.update_layout(
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=60, b=20),
    height=400
)
st.plotly_chart(fig, use_container_width=True)

# ===================== RESULTADO FINAL =====================
st.markdown("---")
st.markdown("<h2 style='text-align: center; color: #6B48FF;'>Resultado Final</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
bruto_str = f"R$ {montante_bruto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
liquido_str = f"R$ {montante_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
rendimento_liq_str = f"R$ {rendimento_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

col1.metric("Montante Bruto", bruto_str)
col2.metric("Rendimento Bruto", f"R$ {rendimento_bruto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Montante Líquido", liquido_str, delta=f"+{rendimento_liq_str}")

st.markdown("---")
st.subheader("Detalhamento")
c1, c2 = st.columns(2)
with c1:
    st.write(f"**Cliente:** {nome_cliente}")
    st.write(f"**Assessor:** {nome_assessor}")
    st.write(f"**Data da simulação:** {data_simulacao.strftime('%d/%m/%Y')}")
    st.write(f"**Aplicação:** {data_aplicacao.strftime('%d/%m/%Y')} → **Vencimento:** {data_vencimento.strftime('%d/%m/%Y')}")
    st.write(f"**Prazo:** {prazo_dias} dias ({prazo_dias/360:.2f} anos)")
    st.write(f"**Taxa:** {taxa_anual:.2f}% a.a.")
with c2:
    st.write(f"**Alíquota IR:** {aliquota_ir}%")
    st.write(f"**Imposto de Renda:** R$ {valor_ir:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.write(f"**Rendimento líquido:** {rendimento_liq_str}")

# ===================== RODAPÉ =====================
st.markdown(
    f"""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #f5f0ff, #ede9ff); border-radius: 20px; margin: 40px 0;">
        <p style="margin: 10px; font-size: 18px;"><strong>Simulação elaborada por {nome_assessor}</strong></p>
        <p style="margin: 10px; color: #555;">em <strong>{data_simulacao.strftime('%d/%m/%Y')}</strong> para <strong>{nome_cliente}</strong></p>
        <p style="margin: 25px 0 0 0; color: #6B48FF; font-size: 22px; font-weight: bold;">Traders Corretora • Assessoria de Investimentos</p>
    </div>
    """,
    unsafe_allow_html=True
)

if st.button("Nova simulação", type="primary", use_container_width=True):
    st.experimental_rerun()
