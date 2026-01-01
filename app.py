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
        self.colocar_marca_dagua()
        if self.page_no() > 1:
            self.set_text_color(*COR_AZUL)
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, f"Quadra {self.quadra} | Bloco {self.bloco} | Mês/Ano {self.mes_ano}", ln=True, align="C")
            self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 9)
        self.set_text_color(100)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

    def colocar_marca_dagua(self):
        try:
            img = Image.open(self.marca_dagua_path).convert("RGBA")
            alpha = img.split()[3].point(lambda p: int(p * 0.4))
            img.putalpha(alpha)
            temp_path = "_marca_temp.png"
            img.save(temp_path)
            info = self.get_image_info(temp_path)
            w = self.w * 0.6
            h = w * (info['h'] / info['w'])
            self.image(temp_path, x=(self.w - w) / 2, y=(self.h - h) / 2, w=w)
        except:
            pass

# ============================================
# STREAMLIT UI
# ============================================
st.set_page_config(page_title="Prestação de Contas", layout="centered")

st.markdown("<h1 style='text-align: center;'>Prestação de Contas</h1>", unsafe_allow_html=True)

# IDENTIFICAÇÃO
col1, col2, col3 = st.columns(3)
quadra = col1.text_input("Quadra", "C")
bloco = col2.text_input("Bloco", "11A")
mes_ano = col3.text_input("Mês/Ano", "nov./25")

saldo_anterior = st.number_input("Saldo anterior", min_value=0.0, value=0.0)
assinante = st.text_input("Nome para assinatura do responsável:")

# RECEITAS
apartamentos = ["101", "102", "201", "202", "301", "302"]
st.subheader("Receitas - Preencha os valores")
receitas_data = []
ocupados = {}

for apto in apartamentos:
    ocupados[apto] = st.checkbox(f"Apto {apto} ocupado?", True)

# DESPESAS FIXAS
st.subheader("Despesas - Preencha os valores")
despesas_data = []
total_despesas = 0.0
for nome in ["CELPE", "COMPESA"]:
    v = st.number_input(nome, min_value=0.0, value=0.0)
    despesas_data.append({"Despesa": nome, "Valor": v})
    total_despesas += v

# DESPESAS EXTRAS
st.subheader("Despesas Extras")
despesas_extras_texto = st.text_area("Descreva as despesas extras com valores")
valores = re.findall(r"[\d]+[\.,]\d{2}", despesas_extras_texto)
despesas_extras_total = sum(float(v.replace(",", ".")) for v in valores) if valores else 0.0
st.write(f"**Total Despesas Extras:** R$ {despesas_extras_total:.2f}")

# RECEITAS EXTRAS (ÚNICA ADIÇÃO)
st.subheader("Receitas Extras")
receitas_extras_texto = st.text_area("Descreva as receitas extras com valores")
valores_r = re.findall(r"[\d]+[\.,]\d{2}", receitas_extras_texto)
receitas_extras_total = sum(float(v.replace(",", ".")) for v in valores_r) if valores_r else 0.0
st.write(f"**Total Receitas Extras:** R$ {receitas_extras_total:.2f}")

# RATEIO
subtotal_rateio = subtotal_taxa = subtotal_caixa = 0.0
ocupados_qtd = sum(ocupados.values())
rateio = total_despesas / ocupados_qtd if ocupados_qtd else 0

for apto in apartamentos:
    if ocupados[apto]:
        taxa = st.number_input(f"Taxa Apto {apto}", min_value=0.0, value=0.0)
        caixa = taxa - rateio
    else:
        taxa = caixa = rateio = 0

    receitas_data.append({"Apartamento": apto, "Ocupado": ocupados[apto], "Rateio": rateio, "Taxa": taxa, "Caixa": caixa})
    subtotal_rateio += rateio
    subtotal_taxa += taxa
    subtotal_caixa += caixa

saldo_atual = saldo_anterior + subtotal_taxa + receitas_extras_total - total_despesas - despesas_extras_total

# SUBTOTAIS
st.subheader("Subtotais das Receitas")
st.write(f"Subtotal Rateio: R$ {subtotal_rateio:.2f}")
st.write(f"Subtotal Taxa: R$ {subtotal_taxa:.2f}")
st.write(f"Subtotal Caixa: R$ {subtotal_caixa:.2f}")

# RESUMO
st.subheader("Resumo Final")
st.write(f"Total Despesas: R$ {total_despesas:.2f}")
st.write(f"Total Despesas Extras: R$ {despesas_extras_total:.2f}")
st.write(f"Total Receitas Extras: R$ {receitas_extras_total:.2f}")
st.write(f"Saldo Atual: R$ {saldo_atual:.2f}")

# GERAR PDF
if st.button("Gerar PDF"):
    pdf = PDF(quadra, bloco, mes_ano, "fab.png")
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial", "", 11)

    pdf.cell(0, 8, f"Receitas Extras:", ln=True)
    pdf.multi_cell(0, 8, receitas_extras_texto or "Não houve receitas extras.")
    pdf.cell(0, 8, f"Total Receitas Extras: R$ {receitas_extras_total:.2f}", ln=True)

    pdf_bytes = bytes(pdf.output(dest="S"))
    st.download_button("Baixar PDF", pdf_bytes, f"Prestacao_Contas_{bloco}.pdf", "application/pdf")
