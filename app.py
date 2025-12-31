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
            alpha = img.split()[3].point(lambda p: int(p * 0.40))
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
# STREAMLIT UI
# ============================================
st.set_page_config(page_title="Prestação de Contas", layout="centered")

st.markdown("<h1 style='text-align: center;'>Prestação de Contas</h1>", unsafe_allow_html=True)

quadra = st.text_input("Quadra", "C")
bloco = st.text_input("Bloco", "11A")
mes_ano = st.text_input("Mês/Ano", "nov./25")

saldo_anterior = st.number_input("Saldo anterior", min_value=0.0, value=0.0)
assinante = st.text_input("Nome para assinatura do responsável:")

# ============================================
# RECEITAS EXTRAS (MESMO PADRÃO DAS DESPESAS)
# ============================================
st.subheader("Receitas Extras")
receitas_extras_texto = st.text_area(
    "Descreva as receitas extras com valores (Ex.: Multa R$ 50,00; Aluguel R$ 150,00)"
)

valores_receitas = re.findall(r"[\d]+[\.,]\d{2}", receitas_extras_texto)
receitas_extras_total = sum(
    float(v.replace(",", ".")) for v in valores_receitas
) if valores_receitas else 0.0

st.write(f"**Total Receitas Extras:** R$ {receitas_extras_total:.2f}")

# ============================================
# DESPESAS FIXAS
# ============================================
st.subheader("Despesas - Preencha os valores")
despesas_data = []
total_despesas = 0.0
for nome in ["CELPE", "COMPESA"]:
    valor = st.number_input(nome, min_value=0.0, value=0.0)
    despesas_data.append({"Despesa": nome, "Valor": valor})
    total_despesas += valor

# ============================================
# DESPESAS EXTRAS
# ============================================
st.subheader("Despesas Extras")
despesas_extras_texto = st.text_area(
    "Descreva as despesas extras com valores (Ex.: Lâmpada R$ 20,00; Válvula R$ 75,60)"
)

valores_despesas = re.findall(r"[\d]+[\.,]\d{2}", despesas_extras_texto)
despesas_extras_total = sum(
    float(v.replace(",", ".")) for v in valores_despesas
) if valores_despesas else 0.0

st.write(f"**Total Despesas Extras:** R$ {despesas_extras_total:.2f}")

# ============================================
# SALDO
# ============================================
saldo_atual = (
    saldo_anterior
    + receitas_extras_total
    - total_despesas
    - despesas_extras_total
)

st.subheader("Resumo Final")
st.write(f"**Saldo Atual:** R$ {saldo_atual:.2f}")

# ============================================
# PDF
# ============================================
if st.button("Gerar PDF"):
    pdf = PDF(quadra, bloco, mes_ano, "fab.png")
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=20)

    # ===== RECEITAS EXTRAS (CLONE DAS DESPESAS) =====
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 10, "Receitas Extras", ln=True)
    pdf.ln(8)

    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(0)
    if receitas_extras_texto.strip():
        pdf.multi_cell(0, 8, receitas_extras_texto)
    else:
        pdf.cell(0, 8, "Não houve receitas extras.", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(200, 220, 255)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(
        0, 10,
        f"Total Receitas Extras: R$ {receitas_extras_total:.2f}",
        ln=True, align="R", fill=True
    )
    pdf.set_text_color(0)
    pdf.ln(18)

    pdf.cell(0, 8, f"Saldo Atual: R$ {saldo_atual:.2f}", ln=True)
    pdf.ln(20)
    pdf.cell(0, 8, f"Assinatura do responsável: {assinante}", ln=True)

    st.download_button(
        "Baixar PDF",
        data=bytes(pdf.output(dest="S")),
        file_name=f"Prestacao_Contas_{bloco}.pdf",
        mime="application/pdf"
    )
