"""Transforme le texte du CV adapté (format « # SECTION » / « - puce ») en PDF propre."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

BLEU = colors.HexColor("#123B66")
GRIS = colors.HexColor("#44546A")

NOM = ParagraphStyle("nom", fontName="Helvetica-Bold", fontSize=20, textColor=BLEU, leading=24)
CONTACT = ParagraphStyle("contact", fontName="Helvetica", fontSize=9.5, textColor=GRIS, leading=13)
SECTION = ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=11.5, textColor=BLEU, leading=15, spaceBefore=10)
TEXTE = ParagraphStyle("texte", fontName="Helvetica", fontSize=10, leading=13.5, spaceAfter=2)


def cv_vers_pdf(texte: str) -> bytes:
    lignes = [l.rstrip() for l in texte.strip().splitlines()]
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm, title="CV", author="")
    flux, puces = [], []

    def vider_puces():
        nonlocal puces
        if puces:
            flux.append(ListFlowable([ListItem(Paragraph(escape(p), TEXTE), leftIndent=12) for p in puces],
                                     bulletType="bullet", start="•", leftIndent=12))
            puces = []

    entete = 0
    for l in lignes:
        if not l.strip():
            continue
        if l.startswith("#"):
            vider_puces()
            flux.append(Paragraph(escape(l.lstrip("# ").upper()), SECTION))
            flux.append(HRFlowable(width="100%", thickness=0.8, color=BLEU, spaceAfter=4))
            entete = 99
        elif l.lstrip().startswith(("- ", "• ", "* ")):
            puces.append(l.lstrip()[2:].strip())
        else:
            vider_puces()
            if entete == 0:
                flux.append(Paragraph(escape(l), NOM))
            elif entete == 1:
                flux.append(Paragraph(escape(l), CONTACT))
                flux.append(Spacer(1, 4))
            else:
                flux.append(Paragraph(escape(l), TEXTE))
            entete += 1
    vider_puces()
    doc.build(flux)
    return buf.getvalue()
