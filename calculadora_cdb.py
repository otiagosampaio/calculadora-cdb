import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta

# Configuração da página
st.set_page_config(page_title="Calculadora CDB Pré e Pós-fixado", layout="centered")
st.title("🧮 Calculadora de CDB Pré e Pós-fixado")
st.markdown("Calcule o rendimento bruto e líquido de CDBs com imposto de renda e IOF (se aplicável).")

# Sidebar com os inputs
with st.sidebar:
    st.header("Parâmetros do Investimento")
    
    investimento = st.number_input("Valor investido (R$)", min_value=100.0, value=10000.0, step=100.0)
    
    data_aplicacao = st.date_input("Data da aplicação", value=datetime.date.today())
    data_vencimento = st.date_input("Data do resgate", value=data_aplicacao + relativedelta(months=+12))
    
    # Ajuste para prazo em dias: usa 30 dias por mês para convenção financeira
    prazo_meses = (data_vencimento.year - data_aplicacao.year) * 12 + (data_vencimento.month - data_aplicacao.month)
    if data_vencimento.day < data_aplicacao.day:
        prazo_meses -= 1  # Ajuste se dia de vencimento for anterior
    prazo_dias = prazo_meses * 30  # Convenção: 30 dias/mês = 360 dias/ano
    
    tipo_cdb = st.radio("Tipo de CDB", ["Pós-fixado (% do CDI)", "Pré-fixado"])
    
    if tipo_cdb == "Pós-fixado (% do CDI)":
        taxa_cdi = st.number_input("Taxa CDI anual (ex: 13.65 para 13,65%)", min_value=0.01, value=13.65)
        perc_cdi = st.number_input("Percentual do CDI (ex: 100% = digite 100)", min_value=1.0, value=110.0, step=1.0)
        taxa_anual = taxa_cdi * (perc_cdi / 100)
        dias_ano = 252  # Dias úteis para pós-fixado
        st.info(f"Taxa efetiva: {taxa_anual:.2f}% a.a.")
    else:
        taxa_anual = st.number_input("Taxa pré-fixada anual (%)", min_value=0.01, value=14.50)
        dias_ano = 360  # Convenção para pré-fixado
    
    considerar_iof = st.checkbox("Considerar IOF (resgate < 30 dias)", value=False)

if prazo_dias <= 0:
    st.error("A data de resgate deve ser posterior à data de aplicação.")
else:
    # Taxa diária corrigida pela convenção
    taxa_diaria = (1 + taxa_anual / 100) ** (1/dias_ano) - 1
    montante_bruto = investimento * (1 + taxa_diaria) ** prazo_dias
    
    rendimento_bruto = montante_bruto - investimento

    # IOF (só nos primeiros 30 dias) - não altera aqui
    iof = 0.0
    if considerar_iof and prazo_dias < 30:
        tabela_iof = [0.96, 0.93, 0.90, 0.86, 0.83, 0.80, 0.76, 0.73, 0.70, 0.66,
                      0.63, 0.60, 0.56, 0.53, 0.50, 0.46, 0.43, 0.40, 0.36, 0.33,
                      0.30, 0.26, 0.23, 0.20, 0.16, 0.13, 0.10, 0.06, 0.03, 0.00]
        iof = tabela_iof[min(prazo_dias - 1, 29)]
        rendimento_bruto_iof = rendimento_bruto * (1 - iof)

    # Imposto de Renda (tabela regressiva)
    if prazo_dias <= 180:
        aliquota_ir = 22.5
    elif prazo_dias <= 360:
        aliquota_ir = 20.0
    elif prazo_dias <= 720:
        aliquota_ir = 17.5
    else:
        aliquota_ir = 15.0

    base_ir = rendimento_bruto if not considerar_iof or prazo_dias >= 30 else rendimento_bruto_iof
    ir = base_ir * (aliquota_ir / 100)
    montante_liquido = investimento + base_ir - ir

    # Resultados
    st.markdown("---")
    st.subheader("📊 Resultado Final")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Montante Bruto", f"R$ {montante_bruto:,.2f}")
    with col2:
        st.metric("Rendimento Bruto", f"R$ {rendimento_bruto:,.2f}")
    with col3:
        st.metric("Montante Líquido", f"R$ {montante_liquido:,.2f}", 
                  delta=f"R$ {montante_liquido - investimento:,.2f}")

    st.markdown("---")
    st.subheader("📋 Detalhamento")

    col_a, col_b = st.columns(2)
    with col_a:
        st.write(f"**Prazo do investimento:** {prazo_dias} dias ({prazo_dias/360:.2f} anos)")
        st.write(f"**Taxa contratada:** {taxa_anual:.2f}% a.a.")
        if tipo_cdb == "Pós-fixado (% do CDI)":
            st.write(f"→ {perc_cdi}% do CDI ({taxa_cdi}% a.a.)")
        st.write(f"**Rendimento bruto:** R$ {rendimento_bruto:,.2f}")
        
    with col_b:
        if considerar_iof and prazo_dias < 30:
            st.write(f"**IOF ({prazo_dias} dias):** {iof*100:.1f}% → R$ {rendimento_bruto - rendimento_bruto_iof:,.2f}")
        st.write(f"**Alíquota IR:** {aliquota_ir}% (prazo de {prazo_dias} dias)")
        st.write(f"**Imposto de Renda:** R$ {ir:,.2f}")
        st.write(f"**Rendimento líquido:** R$ {montante_liquido - investimento:,.2f}")

    st.success(f"Você terá **R$ {montante_liquido:,.2f}** na data {data_vencimento.strftime('%d/%m/%Y')}")

    # Botão para "limpar"
    if st.button("Nova simulação"):
        st.experimental_rerun()
