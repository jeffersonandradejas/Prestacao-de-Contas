import streamlit as st
from fpdf import FPDF
from PIL import Image
import re

# ============================================
# CONFIGURAÇÕES DO TEMA PDF
# ============================================
COR_AZUL = (0, 70, 140)
COR_AZUL_CLARO = (220, 235, 250)
COR_ZEBRA = (245, 245, 245)
COR_CINZA = (180, 180, 180)

# ============================================
# CLASSE PDF
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
            self.set_font("Arial", "B", 10)
            self.set_text_color(*COR_AZUL)
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

    def colocar_marca_dagua(self):
        try:
            img = Image.open(self.marca_dagua_path).convert("RGBA")
            alpha = img.split()[3].point(lambda p: int(p * 0.35))
            img.putalpha(alpha)
            temp = "_marca_temp.png"
            img.save(temp)

            info = self.get_image_info(temp)
            w = self.w * 0.6
            h = w * (info["h"] / info["w"])
            self.image(temp, x=(self.w - w) / 2, y=(self.h - h) / 2, w=w)
        except:
            pass

# ============================================
# STREAMLIT APP
# ============================================
st.set_page_config(page_title="Prestação de Contas", layout="centered")

st.title("📊 Prestação de Contas")

# ============================================
# IDENTIFICAÇÃO
# ============================================
quadra = st.text_input("Quadra", "C")
bloco = st.text_input("Bloco", "11A")
mes_ano = st.text_input("Mês/Ano", "nov./25")

saldo_anterior = st.number_input("Saldo anterior", min_value=0.0, value=0.0)
assinante = st.text_input("Responsável pela assinatura")

# ============================================
# RECEITAS - APARTAMENTOS
# ============================================
st.divider()
st.subheader("🏠 Receitas - Apartamentos")

apartamentos = ["101", "102", "201", "202", "301", "302"]
ocupados = {}

for apto in apartamentos:
    ocupados[apto] = st.checkbox(f"Apto {apto} ocupado?", value=True)

# ============================================
# RECEITAS EXTRAS (VISÍVEL GARANTIDO)
# ============================================
st.divider()
st.subheader("💰 Receitas Extras")

receita_extra_texto = st.text_area(
    "Informe receitas extras (ex.: Multa R$ 50,00; Aluguel salão R$ 150,00)",
    height=120
)

valores_receita_extra = re.findall(r"\d+[.,]\d{2}", receita_extra_texto)
receita_extra_total = (
    sum(float(v.replace(",", ".")) for v in valores_receita_extra)
    if valores_receita_extra else 0.0
)

st.success(f"Total de Receitas Extras: R$ {receita_extra_total:.2f}")

# ============================================
# DESPESAS FIXAS
# ============================================
st.divider()
st.subheader("📉 Despesas Fixas")

despesas_data = []
total_despesas = 0.0

for nome in ["CELPE", "COMPESA"]:
    valor = st.number_input(nome, min_value=0.0, value=0.0)
    despesas_data.append({"Despesa": nome, "Valor": valor})
    total_despesas += valor

# ============================================
# DESPESAS EXTRAS
# ============================================
st.divider()
st.subheader("🧾 Despesas Extras")

despesas_extras_texto = st.text_area(
    "Informe despesas extras (ex.: Lâmpada R$ 20,00; Válvula R$ 75,60)",
    height=120
)

valores_despesas_extras = re.findall(r"\d+[.,]\d{2}", despesas_extras_texto)
despesas_extras_total = (
    sum(float(v.replace(",", ".")) for v in valores_despesas_extras)
    if valores_despesas_extras else 0.0
)

st.error(f"Total de Despesas Extras: R$ {despesas_extras_total:.2f}")

# ============================================
# RATEIO
# ============================================
st.divider()
st.subheader("📐 Rateio")

subtotal_taxa = subtotal_rateio = subtotal_caixa = 0.0
ocupados_count = sum(1 for v in ocupados.values() if v)
rateio_unit = total_despesas / ocupados_count if ocupados_count else 0

receitas_data = []

for apto in apartamentos:
    if ocupados[apto]:
        taxa = st.number_input(f"Taxa Apto {apto}", min_value=0.0, value=0.0)
        rateio = rateio_unit
        caixa = taxa - rateio
    else:
        taxa = rateio = caixa = 0.0

    receitas_data.append({
        "Apartamento": apto,
        "Ocupado": ocupados[apto],
        "Rateio": rateio,
        "Taxa": taxa,
        "Caixa": caixa
    })

    subtotal_taxa += taxa
    subtotal_rateio += rateio
    subtotal_caixa += caixa

# ============================================
# SALDO FINAL
# ============================================
saldo_atual = (
    saldo_anterior
    + subtotal_taxa
    + receita_extra_total
    - total_despesas
    - despesas_extras_total
)

# ============================================
# RESUMO NO APP
# ============================================
st.divider()
st.subheader("📌 Resumo Final")

st.write(f"Subtotal Taxas: R$ {subtotal_taxa:.2f}")
st.write(f"Receitas Extras: R$ {receita_extra_total:.2f}")
st.write(f"Total Despesas: R$ {total_despesas:.2f}")
st.write(f"Despesas Extras: R$ {despesas_extras_total:.2f}")
st.markdown(f"### 💵 Saldo Atual: **R$ {saldo_atual:.2f}**")

# ============================================
# GERAR PDF
# ============================================
if st.button("📄 Gerar PDF"):
    pdf = PDF(quadra, bloco, mes_ano, "fab.png")
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=20)

    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 10, "PRESTAÇÃO DE CONTAS DO BLOCO", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(0)

    pdf.cell(0, 8, f"Saldo Anterior: R$ {saldo_anterior:.2f}", ln=True)
    pdf.cell(0, 8, f"Subtotal Taxas: R$ {subtotal_taxa:.2f}", ln=True)
    pdf.cell(0, 8, f"Receitas Extras: R$ {receita_extra_total:.2f}", ln=True)
    pdf.cell(0, 8, f"Total Despesas: R$ {total_despesas:.2f}", ln=True)
    pdf.cell(0, 8, f"Despesas Extras: R$ {despesas_extras_total:.2f}", ln=True)

    if saldo_atual < 0:
        pdf.set_text_color(200, 0, 0)

    pdf.cell(0, 10, f"Saldo Atual: R$ {saldo_atual:.2f}", ln=True)
    pdf.set_text_color(0)

    pdf.ln(15)
    pdf.cell(0, 8, "Receitas Extras (detalhamento):", ln=True)

    if receita_extra_texto.strip():
        pdf.multi_cell(0, 8, receita_extra_texto)
    else:
        pdf.cell(0, 8, "Não houve receitas extras.", ln=True)

    pdf.ln(20)
    pdf.cell(0, 8, f"Assinatura do responsável: {assinante}", ln=True)

    pdf_bytes = bytes(pdf.output(dest="S"))

    st.success("PDF gerado com sucesso!")

    st.download_button(
        "⬇️ Baixar PDF",
        data=pdf_bytes,
        file_name=f"Prestacao_Contas_{bloco}.pdf",
        mime="application/pdf"
    )
