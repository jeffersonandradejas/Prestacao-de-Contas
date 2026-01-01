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
st.markdown("""
<div style='text-align:center; line-height:1.6;'>
    <strong>ASSOCIAÇÃO DOS PERMISSIONÁRIOS DO CONJUNTO HABITACIONAL</strong><br>
    <strong>SGT WALDER XAVIER DE LIMA</strong><br>
    Av. Armindo Moura, 581 - Quadra E - Loja 04.<br>
    Boa Viagem - Recife-PE<br>
    Telefone escritório: 3343-5965<br>
    Telefone portaria: 3341-0475<br><br>
    <strong>PRESTAÇÃO DE CONTAS DO BLOCO</strong>
</div>
""", unsafe_allow_html=True)

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
# RECEITAS EXTRAS (NOVO)
# -----------------------------------------------
st.subheader("Receitas Extras")
receitas_extras_texto = st.text_area(
    "Descreva as receitas extras com valores (Ex.: Aluguel R$ 200,00; Multa R$ 50,00)"
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

# -----------------------------
# SALDO ATUAL (considera receitas extras)
# -----------------------------
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
#   BOTÃO — GERAR PDF
# ============================================
if st.button("Gerar PDF"):
    marca_path = "fab.png"  # caminho da sua marca d'água

    pdf = PDF(quadra, bloco, mes_ano, marca_path)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=20)

    # ============================
    #  CABEÇALHO PRINCIPAL
    # ============================
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 8, "ASSOCIAÇÃO DOS PERMISSIONÁRIOS DO CONJUNTO HABITACIONAL", ln=True, align="C")
    pdf.cell(0, 8, "SGT WALDER XAVIER DE LIMA", ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0)
    pdf.cell(0, 5, "Av. Armindo Moura, 581 - Quadra E - Loja 04 | Boa Viagem - Recife-PE", ln=True, align="C")
    pdf.cell(0, 5, "Escritório: 3343-5965 | Portaria: 3341-0475", ln=True, align="C")

    pdf.ln(6)
    pdf.set_draw_color(*COR_AZUL)
    y = pdf.get_y()
    pdf.line(15, y, 195, y)
    pdf.ln(12)

    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 12, "PRESTAÇÃO DE CONTAS DO BLOCO", ln=True, align="C")
    pdf.ln(15)

    # ============================================
    #  IDENTIFICAÇÃO
    # ============================================
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 10, "Identificação", ln=True)
    pdf.ln(6)

    pdf.set_font("Arial", "", 11)
    pdf.set_fill_color(*COR_AZUL_CLARO)
    pdf.set_draw_color(*COR_CINZA)
    pdf.set_text_color(0)

    w1, w2, w3 = 50, 50, 60
    largura_total = w1 + w2 + w3
    x = centralizar_x(largura_total)

    pdf.set_x(x)
    pdf.cell(w1, 10, f"Quadra: {quadra}", 1, 0, "L", True)
    pdf.cell(w2, 10, f"Bloco: {bloco}", 1, 0, "L", True)
    pdf.cell(w3, 10, f"Mês/Ano: {mes_ano}", 1, 1, "L", True)
    pdf.ln(15)

    # ============================================
    #  RECEITAS
    # ============================================
    col_apto = 25
    col_rateio = 35
    col_taxa = 35
    col_caixa = 35
    largura_total = col_apto + col_rateio + col_taxa + col_caixa
    x = centralizar_x(largura_total)

    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(*COR_AZUL_CLARO)
    pdf.set_draw_color(*COR_CINZA)
    pdf.set_x(x)
    pdf.cell(col_apto, 10, "Apto", 1, 0, "C", True)
    pdf.cell(col_rateio, 10, "Rateio", 1, 0, "C", True)
    pdf.cell(col_taxa, 10, "Taxa", 1, 0, "C", True)
    pdf.cell(col_caixa, 10, "Caixa", 1, 1, "C", True)

    pdf.set_font("Arial", "", 11)
    zebra = False

    for r in receitas_data:
        fill = COR_ZEBRA if zebra else (255, 255, 255)
        zebra = not zebra
        pdf.set_fill_color(*fill)
        pdf.set_x(x)
        pdf.cell(col_apto, 9, r["Apartamento"], 1, 0, "C", True)
        if r["Ocupado"]:
            pdf.cell(col_rateio, 9, f"R$ {r['Rateio']:.2f}", 1, 0, "R", True)
            pdf.cell(col_taxa, 9, f"R$ {r['Taxa']:.2f}", 1, 0, "R", True)
            if r["Caixa"] < 0:
                pdf.set_text_color(200, 0, 0)
            pdf.cell(col_caixa, 9, f"R$ {r['Caixa']:.2f}", 1, 1, "R", True)
            pdf.set_text_color(0)
        else:
            pdf.cell(col_rateio + col_taxa + col_caixa, 9, "DESOCUPADO", 1, 1, "C", True)

    # Totais receitas
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(200, 220, 255)
    pdf.set_text_color(*COR_AZUL)
    pdf.set_x(x)
    pdf.cell(col_apto, 10, "Subtotal", 1, 0, "C", True)  # <-- título atualizado
    pdf.cell(col_rateio, 10, f"R$ {subtotal_rateio:.2f}", 1, 0, "R", True)
    pdf.cell(col_taxa, 10, f"R$ {subtotal_taxa:.2f}", 1, 0, "R", True)
    pdf.cell(col_caixa, 10, f"R$ {subtotal_caixa:.2f}", 1, 1, "R", True)
    pdf.set_text_color(0)
    pdf.ln(5)


    # ============================================
    #  DESPESAS
    # ============================================
    col_nome = 90
    col_valor = 40
    largura_total = col_nome + col_valor
    x = centralizar_x(largura_total)

    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(*COR_AZUL_CLARO)
    pdf.set_x(x)
    pdf.cell(col_nome, 10, "Despesa", 1, 0, "C", True)
    pdf.cell(col_valor, 10, "Valor", 1, 1, "C", True)

    pdf.set_font("Arial", "", 11)
    zebra = False
    for d in despesas_data:
        fill = COR_ZEBRA if zebra else (255, 255, 255)
        zebra = not zebra
        pdf.set_fill_color(*fill)
        pdf.set_x(x)
        pdf.cell(col_nome, 9, d["Despesa"], 1, 0, "L", True)
        pdf.cell(col_valor, 9, f"R$ {d['Valor']:.2f}", 1, 1, "R", True)

    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(200, 220, 255)
    pdf.set_text_color(*COR_AZUL)
    pdf.set_x(x)
    pdf.cell(col_nome, 10, "Total Despesas", 1, 0, "L", True)
    pdf.cell(col_valor, 10, f"R$ {total_despesas:.2f}", 1, 1, "R", True)
    pdf.set_text_color(0)
    pdf.ln(18)

    # ============================================
    #  DESPESAS EXTRAS
    # ============================================
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 10, "Despesas Extras", ln=True)
    pdf.ln(8)

    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(0)
    if despesas_extras_texto.strip():
        pdf.multi_cell(0, 8, despesas_extras_texto)
    else:
        pdf.cell(0, 8, "Não houve despesas extras.", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(200, 220, 255)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 10, f"Total Despesas Extras: R$ {despesas_extras_total:.2f}", ln=True, align="R", fill=True)
    pdf.set_text_color(0)
    pdf.ln(18)

    # ============================================
    #  RECEITAS EXTRAS
    # ============================================
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
    pdf.cell(0, 10, f"Total Receitas Extras: R$ {receitas_extras_total:.2f}", ln=True, align="R", fill=True)
    pdf.set_text_color(0)
    pdf.ln(18)

    # ============================================
    #  RESUMO FINAL COMPLETO
    # ============================================
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 10, "Resumo Final", ln=True)
    pdf.ln(6)

    pdf.set_font("Arial", "", 11)
    pdf.set_fill_color(*COR_AZUL_CLARO)
    pdf.set_text_color(0)

    pdf.cell(0, 8, f"Total de Despesas: R$ {total_despesas:.2f}", ln=True)
    pdf.cell(0, 8, f"Total Despesas Extras: R$ {despesas_extras_total:.2f}", ln=True)
    pdf.cell(0, 8, f"Total Receitas Extras: R$ {receitas_extras_total:.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo Anterior: R$ {saldo_anterior:.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo Atual: R$ {saldo_atual:.2f}", ln=True)

    pdf.ln(18)


    # ============================================
    #  ASSINATURA
    # ============================================
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Responsável: {assinante}", ln=True)
    pdf.ln(25)
    pdf.cell(0, 10, "______________________________", ln=True)


    # ============================================
    #  DOWNLOAD
    # ============================================
    pdf_bytes = bytes(pdf.output(dest='S'))  # CORREÇÃO: bytearray -> bytes
    st.success("PDF gerado com sucesso!")

    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name=f"Prestacao_Contas_{bloco}.pdf",
        mime="application/pdf"
    )



