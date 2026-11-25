#!/usr/bin/env python3
"""Build the combined process-book PDF.

Takes the existing process book PDF (every milestone through Milestone 11,
exported from the team Google Doc) and appends pages rendered from one or more
Markdown files in this folder, so updating the process book is: edit the .md,
run this script.

    python process-book/build_process_book.py
        -> process-book/CS1710_Process_Book_Final.pdf  (base export + FINAL.md)
    python process-book/build_process_book.py --base "new export.pdf"
    python process-book/build_process_book.py --no-base --out final_pages_only.pdf

Markdown subset supported: #/##/### headings, paragraphs, "- " bullets,
"1. " numbered lists, **bold**, *italic*, `code`, pipe tables, and images
(![caption](path), .jpg/.png/.svg). Everything else is passed through as text.

Needs: pypdf, reportlab, svglib  (pip install pypdf reportlab svglib)
"""
import argparse, os, re, sys

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))

INK, INK2, RULE = colors.HexColor('#1b2233'), colors.HexColor('#555b6b'), colors.HexColor('#d9d9d4')
ss = getSampleStyleSheet()
H1 = ParagraphStyle('h1', parent=ss['Title'], fontName='Helvetica-Bold', fontSize=22, leading=26,
                    textColor=INK, alignment=TA_LEFT, spaceAfter=10, spaceBefore=6)
H2 = ParagraphStyle('h2', parent=ss['Heading2'], fontName='Helvetica-Bold', fontSize=15, leading=19,
                    textColor=INK, spaceBefore=14, spaceAfter=6)
H3 = ParagraphStyle('h3', parent=ss['Heading3'], fontName='Helvetica-Bold', fontSize=12, leading=15,
                    textColor=INK, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle('body', parent=ss['Normal'], fontName='Helvetica', fontSize=10, leading=14,
                      textColor=INK, spaceAfter=6)
CAP = ParagraphStyle('cap', parent=BODY, fontSize=8.5, leading=11, textColor=INK2, spaceAfter=10)
CELL = ParagraphStyle('cell', parent=BODY, fontSize=8.5, leading=11, spaceAfter=0)
MAXW = letter[0] - 2 * inch
MAXH = letter[1] - 2.6 * inch   # tallest an image may be and still share a page with its caption


def inline(md):
    """Markdown inline -> reportlab paragraph XML."""
    t = (md.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    t = re.sub(r'`([^`]+)`', r'<font face="Courier" size="8.5">\1</font>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])', r'<i>\1</i>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<link href="\2" color="#2a78d6">\1</link>', t)
    return t


def image_flowable(path, caption):
    full = os.path.join(HERE, path)
    if not os.path.exists(full):
        return [Paragraph(f'[missing image: {path}]', CAP)]
    if full.lower().endswith('.svg'):
        from svglib.svglib import svg2rlg
        d = svg2rlg(full)
        scale = min(MAXW / d.width, MAXH / d.height, 1.0)
        d.width, d.height = d.width * scale, d.height * scale
        d.scale(scale, scale)
        fl = d
    else:
        img = Image(full)
        scale = min(MAXW / img.imageWidth, MAXH / img.imageHeight, 1.0)
        img.drawWidth, img.drawHeight = img.imageWidth * scale, img.imageHeight * scale
        fl = img
    return [KeepTogether([fl, Spacer(1, 3), Paragraph(inline(caption), CAP)])]


def md_to_story(text):
    story, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1; continue
        if ln.startswith('# '):
            story.append(Paragraph(inline(ln[2:]), H1))
        elif ln.startswith('## '):
            story.append(Paragraph(inline(ln[3:]), H2))
        elif ln.startswith('### '):
            story.append(Paragraph(inline(ln[4:]), H3))
        elif ln.startswith('!['):
            m = re.match(r'!\[(.*?)\]\((.*?)\)', ln)
            story += image_flowable(m.group(2), m.group(1))
        elif ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append([Paragraph(inline(c), CELL) for c in cells])
                i += 1
            ncol = max(len(r) for r in rows)
            t = Table(rows, colWidths=[MAXW / ncol] * ncol, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0ec')),
                ('LINEBELOW', (0, 0), (-1, -1), 0.4, RULE),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            story += [t, Spacer(1, 8)]
            continue
        elif re.match(r'^(- |\d+\. )', ln):
            numbered = bool(re.match(r'^\d+\. ', ln))
            items = []
            while i < len(lines) and re.match(r'^(- |\d+\. )', lines[i]):
                body = re.sub(r'^(- |\d+\. )', '', lines[i]).strip()
                i += 1
                while i < len(lines) and lines[i].startswith('  ') and lines[i].strip():
                    body += ' ' + lines[i].strip(); i += 1
                items.append(ListItem(Paragraph(inline(body), BODY), leftIndent=12))
            story.append(ListFlowable(items, bulletType='1' if numbered else 'bullet',
                                      start='1' if numbered else None, leftIndent=14,
                                      bulletFontSize=8))
            story.append(Spacer(1, 4))
            continue
        else:
            para = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r'^(#|!\[|\||- |\d+\. )', lines[i]):
                para.append(lines[i].strip()); i += 1
            story.append(Paragraph(inline(' '.join(para)), BODY))
            continue
        i += 1
    return story


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=os.path.join(HERE, 'base', 'GoogleDoc_export_through_Milestone11.pdf'),
                    help='existing process book PDF to append to (omit with --no-base)')
    ap.add_argument('--no-base', action='store_true', help='build only the new pages')
    ap.add_argument('--md', nargs='+', default=[os.path.join(HERE, 'FINAL.md')],
                    help='markdown files to render, in order')
    ap.add_argument('--out', default=os.path.join(HERE, 'CS1710_Process_Book_Final.pdf'))
    a = ap.parse_args()

    new_pages = os.path.join(HERE, '_new_pages.pdf')
    story = []
    for k, md in enumerate(a.md):
        if k: story.append(PageBreak())
        story += md_to_story(open(md, encoding='utf-8').read())
    doc = SimpleDocTemplate(new_pages, pagesize=letter, leftMargin=inch, rightMargin=inch,
                            topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                            title='CS 1710 process book', author='Atul Julka, Lily Xu, Liam Clower')

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont('Helvetica', 8); canvas.setFillColor(INK2)
        canvas.drawRightString(letter[0] - inch, 0.55 * inch, f'CS 1710 process book, final section  |  {d.page}')
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    w = PdfWriter()
    n_base = 0
    if not a.no_base and os.path.exists(a.base):
        for p in PdfReader(a.base).pages:
            w.add_page(p); n_base += 1
    elif not a.no_base:
        print(f'warning: base PDF not found at {a.base}; writing new pages only', file=sys.stderr)
    r = PdfReader(new_pages)
    for p in r.pages:
        w.add_page(p)
    w.add_metadata({'/Title': 'CS 1710 Process Book - Final'})
    with open(a.out, 'wb') as f:
        w.write(f)
    os.remove(new_pages)
    print(f'wrote {a.out}: {n_base} existing pages + {len(r.pages)} new pages = {n_base + len(r.pages)}')


if __name__ == '__main__':
    main()
