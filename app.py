import streamlit as st
from fpdf import FPDF
from PIL import Image
import re

# ============================================
#    CONFIGURAÇÕES DO TEMA PDF (AZUL PRO)
# ============================================
COR_AZUL = (0, 70, 140)
COR_AZUL_CLARO = (220, 235, 250)
COR_ZEBRA = (245, 245, 245)
COR_CINZA = (180, 180, 180)


# ============================================
#      CLASSE CUSTOMIZADA PARA CABEÇALHO / RODAPÉ
# ============================================
class PDF(FPDF):

    def __init__(self, quadra, bloco, mes_ano, marca_dagua_path):
        super().__init__()
        self.quadra = quadra
        self.bloco = bloco
        self.mes_ano = mes_ano
        self.marca_dagua_path = marca_dagua_path

    def header(self):
        # Marca d'água em TODAS as páginas
        self.colocar_marca_dagua()

        if self.page_no() > 1:
            self.set_text_color(*COR_AZUL)
            self.set_font("Arial", "B", 10)
            self.cell(
                0, 6,
                f"Quadra {self.quadra} | Bloco {self.bloco} | Mês/Ano {self.mes_ano}",
                ln=True, align="C"
            )
            self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 9)
        self.set_text_color(100)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

    # ---------------------------------------------------------
    # FUNÇÃO DA MARCA D'ÁGUA — CENTRALIZADA
    # ---------------------------------------------------------
    def colocar_marca_dagua(self):
        try:
            img = Image.open(self.marca_dagua_path).convert("RGBA")
            alpha_factor = 0.40
            alpha = img.split()[3]
            alpha = alpha.point(lambda p: int(p * alpha_factor))
            img.putalpha(alpha)

            temp_path = "_marca_temp.png"
            img.save(temp_path)

            info = self.get_image_info(temp_path)
            img_w = info['w']
            img_h = info['h']

            page_w = self.w
            page_h = self.h

            escala = 0.60
            nova_largura = page_w * escala
            nova_altura = nova_largura * (img_h / img_w)

            x = (page_w - nova_largura) / 2
            y = (page_h - nova_altura) / 2

            self.image(temp_path, x=x, y=y, w=nova_largura)

        except Exception as e:
            print("Erro ao carregar marca d’água:", e)


# ============================================
#               STREAMLIT UI
# ============================================
st.set_page_config(page_title="Prestação de Contas", layout="centered")

st.markdown("<h1 style='text-align: center;'>Prestação de Contas</h1>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align:center; line-height:1.6;'>
        <strong>ASSOCIAÇÃO DOS PERMISSIONÁRIOS DO CONJUNTO HABITACIONAL</strong><br>
        <strong>SGT WALDER XAVIER DE LIMA</strong><br>
        Av. Armindo Moura, 581 - Quadra E - Loja 04.<br>
        Boa Viagem - Recife-PE<br>
        Telefone escritório: 3343-5965<br>
        Telefone portaria: 3341-0475<br><br>
        <strong>PRESTAÇÃO DE CONTAS DO BLOCO</strong>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------
# IDENTIFICAÇÃO
# -----------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    quadra = st.text_input("Quadra", value="C")
with col2:
    bloco = st.text_input("Bloco", value="11A")
with col3:
    mes_ano = st.text_input("Mês/Ano", value="nov./25")

saldo_anterior = st.number_input("Saldo anterior", min_value=0.0, value=0.0)
assinante = st.text_input("Nome para assinatura do responsável:", value="")

# -----------------------------------------------
# APARTAMENTOS / RECEITAS
# -----------------------------------------------
apartamentos = ["101", "102", "201", "202", "301", "302"]
st.subheader("Receitas - Preencha os valores")
receitas_data = []
ocupados_flags = {}

for apto in apartamentos:
    ocupado = st.checkbox(f"Apto {apto} ocupado?", value=True)
    ocupados_flags[apto] = ocupado

# -----------------------------------------------
# DESPESAS FIXAS
# -----------------------------------------------
st.subheader("Despesas - Preencha os valores")
despesas_data = []
total_despesas = 0.0
for nome in ["CELPE", "COMPESA"]:
    valor = st.number_input(nome, min_value=0.0, value=0.0)
    despesas_data.append({"Despesa": nome, "Valor": valor})
    total_despesas += valor

# -----------------------------------------------
# DESPESAS EXTRAS
# -----------------------------------------------
st.subheader("Despesas Extras")
despesas_extras_texto = st.text_area(
    "Descreva as despesas extras com valores (Ex.: Lâmpada R$ 20,00; Válvula R$ 75,60)"
)
valores_encontrados = re.findall(r"[\d]+[\.,]\d{2}", despesas_extras_texto)
despesas_extras_total = sum(float(v.replace(",", ".")) for v in valores_encontrados) if valores_encontrados else 0.0
st.write(f"**Total Despesas Extras:** R$ {despesas_extras_total:.2f}")

# -----------------------------------------------
# RECEITAS EXTRAS
# -----------------------------------------------
st.subheader("Receitas Extras")
receitas_extras_texto = st.text_area(
    "Descreva as receitas extras com valores (Ex.: Aluguel R$ 500,00; Doação R$ 200,00)"
)
valores_receitas_extras = re.findall(r"[\d]+[\.,]\d{2}", receitas_extras_texto)
receitas_extras_total = sum(float(v.replace(",", ".")) for v in valores_receitas_extras) if valores_receitas_extras else 0.0
st.write(f"**Total Receitas Extras:** R$ {receitas_extras_total:.2f}")

# -----------------------------------------------
# RATEIO E CÁLCULOS
# -----------------------------------------------
subtotal_rateio = subtotal_taxa = subtotal_caixa = 0.0
apartamentos_ocupados = sum(1 for apto in apartamentos if ocupados_flags[apto])
rateio_por_unidade = total_despesas / apartamentos_ocupados if apartamentos_ocupados else 0.0

for apto in apartamentos:
    ocupado = ocupados_flags[apto]
    if ocupado:
        rateio = rateio_por_unidade
        taxa = st.number_input(f"Taxa Apto {apto}", min_value=0.0, value=0.0)
        caixa = taxa - rateio
    else:
        rateio = taxa = caixa = 0.0

    receitas_data.append({
        "Apartamento": apto,
        "Ocupado": ocupado,
        "Rateio": rateio,
        "Taxa": taxa,
        "Caixa": caixa
    })

    subtotal_rateio += rateio
    subtotal_taxa += taxa
    subtotal_caixa += caixa

saldo_atual = saldo_anterior + subtotal_taxa + receitas_extras_total - total_despesas - despesas_extras_total

# -----------------------------------------------
# SUBTOTAIS NO APP
# -----------------------------------------------
st.subheader("Subtotais das Receitas")
st.write(f"**Subtotal Rateio:** R$ {subtotal_rateio:.2f}")
st.write(f"**Subtotal Taxa:** R$ {subtotal_taxa:.2f}")
st.write(f"**Subtotal Caixa:** R$ {subtotal_caixa:.2f}")

# -----------------------------------------------
# SALDOS NO APP
# -----------------------------------------------
st.subheader("Resumo Final")
st.write(f"**Total de Despesas:** R$ {total_despesas:.2f}")
st.write(f"**Total Despesas Extras:** R$ {despesas_extras_total:.2f}")
st.write(f"**Total Receitas Extras:** R$ {receitas_extras_total:.2f}")
st.write(f"**Saldo Anterior:** R$ {saldo_anterior:.2f}")
st.write(f"**Saldo Atual:** R$ {saldo_atual:.2f}")


# ============================================
# FUNÇÃO AUXILIAR — CENTRALIZAR TABELAS
# ============================================
def centralizar_x(largura_total, margem=15):
    largura_util = 210 - 2 * margem
    return margem + (largura_util - largura_total) / 2


   # ============================================
    #  DOWNLOAD BUTTON — CONVERSÃO PARA BYTES
    # ============================================
pdf_bytes = bytes(pdf.output(dest='S'))  # CORREÇÃO: bytearray -> bytes
    st.success("PDF gerado com sucesso!")

    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"Prestacao_Contas_{bloco}.pdf",
        mime="application/pdf")
