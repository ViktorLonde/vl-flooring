# -*- coding: utf-8 -*-
"""
Padrão de escrita de nomes e endereços: Primeira Letra Maiúscula (Title Case),
com exceções:

• Siglas e códigos ficam em MAIÚSCULAS: LLC, USA, LVT, SPC, SF, JB-0033,
  SGH104, 771-STEP (qualquer palavra com letra e número junto).
• Palavras pequenas no meio ficam minúsculas: by, of, and, the, de, da, do…
• Ordinais: 1st, 2nd, 3rd, 4th.
• Palavras escritas de propósito com maiúsculas no meio (TruBalance,
  DurAlive, McDonald) não são mexidas.
• E-mails e sites não são mexidos.

smart_title("3331 FOUNDERS CLUB DR")      → "3331 Founders Club Dr"
smart_title("flooring options by carpet one") → "Flooring Options by Carpet One"
smart_title("vertex londe flooring llc")  → "Vertex Londe Flooring LLC"
"""

import re

ACRONYMS = {
    "LLC", "INC", "LLP", "PLLC", "CO.", "USA", "US", "LVT", "LVP", "SPC", "WPC", "VCT", "PVC", "MDF", "HVAC",
    "SF", "SQFT", "LF", "YF", "EA", "PCS", "HOA", "DBA", "FL", "GA", "NY", "NJ", "TX", "CA", "NC", "SC",
    "NE", "NW", "SE", "SW", "N", "S", "E", "W", "II", "III", "IV", "UV", "PO", "ID", "QC", "DIY", "CEO",
}
SMALL_WORDS = {"a", "an", "and", "at", "by", "for", "in", "of", "on", "or", "the", "to", "de", "da", "do",
               "das", "dos", "e", "la", "van", "von", "x"}
_ORDINAL = re.compile(r"^(\d+)(st|nd|rd|th)$", re.IGNORECASE)
_DIMENSION = re.compile(r"^\d+(\.\d+)?[xX]\d+(\.\d+)?$")
_HAS_LETTER_AND_DIGIT = re.compile(r"(?=.*[A-Za-z])(?=.*\d)")
_TOKEN = re.compile(r"(\s+|[/(),&\"]+)")


def _is_mixed_case(word):
    letters = [c for c in word if c.isalpha()]
    return (any(c.isupper() for c in letters) and any(c.islower() for c in letters)
            and not (letters and letters[0].isupper() and all(c.islower() for c in letters[1:])))


def _fix_word(word, first, keep_caps=False):
    if not word or not any(c.isalpha() for c in word):
        return word
    # texto digitado com maiúsculas/minúsculas misturadas: palavra curta toda em
    # MAIÚSCULAS é sigla de propósito (PL Premium, OSB, ABC Supply)
    if keep_caps and word.isupper() and len(word.strip(".'")) <= 4:
        return word
    if "-" in word.strip("-"):
        pieces = word.split("-")
        if any(any(ch.isdigit() for ch in p) for p in pieces):
            return word.upper()  # código com hífen: 771-STEP, JB-0033
        return "-".join(_fix_word(p, first and i == 0, keep_caps) if p else p for i, p in enumerate(pieces))
    if _DIMENSION.match(word):
        return word.lower()  # medidas: 36x42, 7.5x72
    m = _ORDINAL.match(word)
    if m:
        return m.group(1) + m.group(2).lower()
    if _HAS_LETTER_AND_DIGIT.match(word):
        return word.upper()  # códigos: SGH104, 4TH? (ordinal já tratado), 2X4
    if _is_mixed_case(word):
        return word  # TruBalance, DurAlive, McDonald, iPhone
    core = word.strip(".'")
    if core.upper() in ACRONYMS or word.upper() in ACRONYMS:
        return word.upper()
    lower = word.lower()
    if not first and lower in SMALL_WORDS:
        return lower
    # O'Neil, D'Angelo
    if "'" in lower and len(lower) > 2 and lower[1] == "'":
        return lower[0].upper() + "'" + lower[2:3].upper() + lower[3:]
    return lower[0].upper() + lower[1:]


def smart_title(text):
    """Aplica o padrão; devolve o texto sem mexer se for e-mail/site ou vazio."""
    if text is None:
        return text
    original = str(text)
    stripped = " ".join(original.split())
    if not stripped or "@" in stripped or "www." in stripped.lower() or "://" in stripped:
        return stripped
    parts = _TOKEN.split(stripped)
    letters = [c for c in stripped if c.isalpha()]
    keep_caps = any(c.islower() for c in letters) and any(c.isupper() for c in letters)
    out, first = [], True
    for part in parts:
        if not part or _TOKEN.fullmatch(part):
            out.append(part)
            continue
        out.append(_fix_word(part, first, keep_caps))
        first = False
    return "".join(out)
