# -*- coding: utf-8 -*-
"""
E-mail compartilhado pelas telas novas:

• send_mail()       — envia (texto + HTML opcional + anexos) pela conta de
                      Settings → Email. Levanta exceção se falhar.
• fetch_unseen()    — lê os e-mails NÃO LIDOS da caixa de entrada cujo
                      assunto começa com uma das palavras dadas.
• mark_seen()       — marca como lido (o e-mail não volta a aparecer).
• brand_header()    — cabeçalho com logo + nome da empresa para os PDFs.
• partner_sources   — de onde vêm nome/e-mail de cada tipo de invoice.

Nada aqui manda e-mail sozinho: quem chama sempre pergunta antes.
"""

import os
import smtplib
import unicodedata
from email.message import EmailMessage
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime

import company_settings

# (tipo em payments.INVOICE_TYPE, tabela, FK, tabela do parceiro, SQL do nome, SQL do e-mail)
PARTNER_SOURCES = [
    ("Contractor", "contractor_invoices", "CONTRACTOR_ID", "contractors",
     "COALESCE(NULLIF(p.COMPANY_NAME, ''), p.FULL_NAME)", "COALESCE(NULLIF(p.COMPANY_EMAIL, ''), p.EMAIL)"),
    ("Company", "company_invoices", "COMPANY_ID", "companies", "p.COMPANY_NAME", "p.EMAIL"),
    ("Client", "client_invoices", "CLIENT_ID", "clients", "p.FULL_NAME", "p.EMAIL"),
]


def normalize(text):
    """minúsculo, sem acento — para comparar palavras."""
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()


def smtp_ready():
    user = (company_settings.EMAIL_SMTP_USER or "").strip()
    pw = (company_settings.EMAIL_SMTP_PASSWORD or "").strip()
    return bool(user) and "your-email" not in user and bool(pw) and pw != "your-app-password"


def build_message(to, subject, text, html=None, attachments=(), cc=None):
    m = EmailMessage()
    m["Subject"] = subject
    m["From"] = f"{company_settings.EMAIL_FROM_NAME} <{company_settings.EMAIL_SMTP_USER}>"
    m["To"] = to
    if cc:
        m["Cc"] = cc
    m.set_content(text)
    if html:
        m.add_alternative(f"<html><body style='font-family:Segoe UI,Arial,sans-serif'>{html}</body></html>",
                          subtype="html")
    for path in attachments or ():
        if not path or not os.path.exists(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        maintype, subtype = {".pdf": ("application", "pdf"), ".jpg": ("image", "jpeg"), ".jpeg": ("image", "jpeg"),
                             ".png": ("image", "png")}.get(ext, ("application", "octet-stream"))
        with open(path, "rb") as f:
            m.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(path))
    return m


def send_messages(messages):
    """Envia várias mensagens numa conexão só. Devolve [(mensagem, erro ou None)]."""
    results = []
    with smtplib.SMTP(company_settings.EMAIL_SMTP_HOST, company_settings.EMAIL_SMTP_PORT, timeout=25) as server:
        server.starttls()
        server.login(company_settings.EMAIL_SMTP_USER, company_settings.EMAIL_SMTP_PASSWORD)
        for m in messages:
            try:
                server.send_message(m)
                results.append((m, None))
            except Exception as e:  # um e-mail com problema não para os outros
                results.append((m, e))
    return results


def send_mail(to, subject, text, html=None, attachments=(), cc=None):
    m = build_message(to, subject, text, html, attachments, cc)
    (_m, err), = send_messages([m])
    if err:
        raise err


def _decode(value):
    parts = decode_header(value or "")
    return "".join((p.decode(enc or "utf-8", errors="ignore") if isinstance(p, bytes) else p) for p, enc in parts)


def _imap():
    import imaplib
    imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    imap.login(company_settings.EMAIL_SMTP_USER, company_settings.EMAIL_SMTP_PASSWORD)
    imap.select("INBOX")
    return imap


def fetch_unseen(keywords):
    """E-mails não lidos cujo assunto (sem acento, minúsculo) COMEÇA com uma
    das palavras. Não marca nada como lido. Devolve lista de dicts:
    uid, subject, from, date (datetime), body, attachments [(nome, bytes, tipo)]."""
    import email as email_module
    keys = tuple(normalize(k) for k in keywords)
    imap = _imap()
    out = []
    try:
        status, data = imap.uid("search", None, "UNSEEN")
        if status != "OK":
            raise RuntimeError("IMAP search failed")
        for uid in data[0].split():
            # primeiro só o cabeçalho (rápido); o resto só se o assunto bate
            status, head = imap.uid("fetch", uid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT)])")
            if status != "OK" or not head or not head[0]:
                continue
            subject = _decode(email_module.message_from_bytes(head[0][1]).get("Subject", ""))
            if not normalize(subject).startswith(keys):
                continue
            status, msg_data = imap.uid("fetch", uid, "(BODY.PEEK[])")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email_module.message_from_bytes(msg_data[0][1])
            try:
                when = parsedate_to_datetime(msg.get("Date", ""))
                if when.tzinfo:
                    when = when.astimezone().replace(tzinfo=None)
            except Exception:
                when = datetime.now()
            body, attachments = "", []
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                filename = part.get_filename()
                if filename:
                    payload = part.get_payload(decode=True)
                    if payload:
                        attachments.append((_decode(filename), payload, part.get_content_type()))
                elif part.get_content_type() == "text/plain" and not body:
                    try:
                        body = (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8",
                                                                             errors="ignore")
                    except Exception:
                        body = ""
            out.append({"uid": uid, "subject": subject, "from": _decode(msg.get("From", "")), "date": when,
                        "body": strip_signature(body), "attachments": attachments})
    finally:
        try:
            imap.logout()
        except Exception:
            pass
    return out


def strip_signature(body):
    """Corta o texto citado de respostas e assinaturas comuns de celular."""
    lines = []
    for line in (body or "").replace("\r", "").split("\n"):
        s = line.strip()
        low = normalize(s)
        quoted_reply = low.startswith(("on ", "em ")) and low.endswith(("wrote:", "escreveu:"))
        signature = low.startswith(("sent from my", "enviado do meu", "enviado de meu", "get outlook for"))
        if s == "--" or s.startswith(">") or quoted_reply or signature:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def mark_seen(uids):
    if not uids:
        return
    try:
        imap = _imap()
        for uid in uids:
            imap.uid("store", uid, "+FLAGS", "\\Seen")
        imap.logout()
    except Exception:
        pass  # não crítico — o e-mail só reaparece na próxima checagem


def esc(text):
    return (str(text or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def brand_header(title, lines_right):
    """Cabeçalho de PDF igual ao do Estimate: logo + empresa à esquerda,
    título laranja + linhas à direita. Devolve lista de flowables."""
    from app_common import (Table, TableStyle, Paragraph, Spacer, Image, HRFlowable, ParagraphStyle,
                            getSampleStyleSheet, colors, inch, TA_RIGHT, PROJECT_DIR, BRAND_NAVY, BRAND_ORANGE)
    styles = getSampleStyleSheet()
    small = ParagraphStyle("hsmall", parent=styles["Normal"], fontSize=9, leading=12)
    right = ParagraphStyle("hright", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=10)
    name_style = ParagraphStyle("hcompany", parent=styles["Normal"], fontSize=15, leading=18,
                                textColor=colors.HexColor(BRAND_NAVY))
    name = Paragraph(f"<b>{esc(company_settings.COMPANY_NAME)}</b>", name_style)
    logo = os.path.join(PROJECT_DIR, "icons_", "logo_icon_only_256.png")
    if os.path.exists(logo):
        brand = Table([[Image(logo, width=0.62 * inch, height=0.62 * inch), name]], colWidths=[0.75 * inch, 3.0 * inch])
        brand.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        left = [brand]
    else:
        left = [name]
    left += [Spacer(1, 6), Paragraph(f"{esc(company_settings.COMPANY_PHONE)}<br/>{esc(company_settings.COMPANY_EMAIL)}"
                                     f"<br/>{esc(company_settings.COMPANY_WEBSITE)}", small)]
    head_right = Paragraph(f"<font size=20 color='{BRAND_ORANGE}'><b>{esc(title)}</b></font><br/><br/>"
                           + "<br/>".join(lines_right), right)
    header = Table([[left, head_right]], colWidths=[3.8 * inch, 3.2 * inch])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return [header, Spacer(1, 14), HRFlowable(width="100%", color=colors.HexColor(BRAND_ORANGE), thickness=2),
            Spacer(1, 10)]


def table_style(extra=()):
    from app_common import TableStyle, colors, BRAND_NAVY
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        *extra,
    ])
