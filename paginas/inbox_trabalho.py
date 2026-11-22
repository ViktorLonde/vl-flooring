# -*- coding: utf-8 -*-
"""
Lançar trabalho pelo celular, por e-mail (para a conta de Settings → Email):

• Work Day Inbox — assunto `dia JB-0032` (ou `dia JB-0032 JB-0035`).
  Texto opcional: `meio dia, Juan e Pedro`, `ontem`, `19/11`, `JB-0032 1/3`.
  Sem texto = dia inteiro, mesma equipe do último dia. Data = data do
  e-mail. Na revisão cada dia aparece com ✅ ou ⚠️ (código que não existe,
  dia já lançado nessa data, nome de helper desconhecido) e só é criado
  depois de confirmar — igual ao "Log today".
• Material Inbox — assunto `material JB-0032`, uma linha por material
  (`6 Bostik SL-100`, `2 ProFlex primer`, `12 caixas Bone`). Cada linha é
  reconhecida no cadastro de Products (nome, marca, código); produto não
  encontrado pode ser cadastrado na hora. Foto da nota anexada fica
  guardada em receipts_received/ e nos documentos do job.

Os e-mails só são marcados como lidos depois de lançados ou ignorados.

Métodos da MainWindow (mixin) — veja main_.py.
"""

import re
from datetime import date, timedelta

from PySide6.QtWidgets import QInputDialog

from app_common import *  # noqa: F401,F403
from paginas import correio
from paginas.correio import normalize
from paginas.fracao import DAY_PORTIONS, make_portion_combo, portion_label
from paginas.moderno import show_toast
from paginas.visual import tabler_icon

DAY_KEYWORDS = ("dia", "day")
MATERIAL_KEYWORDS = ("material", "materiais", "materials")

_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")
_TABLE_QSS = ("QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; } "
              "QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; "
              "font-weight: 600; }")

_CODE_RE = re.compile(r"\bJB[\s\-_]?(\d{1,5})\b", re.IGNORECASE)
# frações de dia (antes da data, para "1/2" não virar 1º de fevereiro)
_PORTION_WORDS = [
    (r"dia\s+inteiro|full\s*day|o\s+dia\s+todo|dia\s+todo", 1.0),
    (r"meio[\s\-]*dia|meio\s+periodo|half(?:\s*day)?|½|(?<![\d/])1/2(?![\d/])", 0.5),
    (r"dois\s+tercos|2\s*tercos|⅔|(?<![\d/])2/3(?![\d/])", 0.667),
    (r"um\s+terco|1\s*terco|terco|⅓|(?<![\d/])1/3(?![\d/])", 0.333),
    (r"tres\s+quartos|¾|(?<![\d/])3/4(?![\d/])", 0.75),
    (r"um\s+quarto|¼|(?<![\d/])1/4(?![\d/])", 0.25),
]
_DATE_RE = re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?![\d/])")
_FILLER = {"dia", "day", "e", "and", "com", "with", "equipe", "crew", "helpers", "helper", "o", "a", "os", "as",
           "no", "na", "em", "de", "do", "da", "trabalho", "trabalhei", "worked", "hoje", "today", "ontem",
           "yesterday", "anteontem", "eu", "me", "mais", "tambem", "too", "so", "only", "periodo"}
_ALONE = ("sozinho", "sozinha", "alone", "so eu", "ninguem", "sem helper", "sem ajudante", "no helper")


def _snap_portion(x):
    return min((v for v, _l in DAY_PORTIONS), key=lambda v: abs(v - x))


def _find_portion(text):
    norm = normalize(text)
    for pattern, value in _PORTION_WORDS:
        if re.search(pattern, norm):
            return value
    return None


def _strip_portions(norm):
    for pattern, _v in _PORTION_WORDS:
        norm = re.sub(pattern, " ", norm)
    return norm


def parse_day_email(subject, body, email_date, helpers=()):
    """Lê um e-mail de dia de trabalho. helpers: [(id, nome)].
    Devolve {'date', 'entries': [(code, fraction)], 'crew': [ids] ou None,
    'unknown_names': [...], 'notes': [...]}."""
    body = correio.strip_signature(body)
    text =f"{subject or ''}\n{body or ''}"
    norm_all = normalize(text)
    base = email_date.date() if hasattr(email_date, "date") else (email_date or date.today())

    # Job Codes, na ordem, sem repetir
    matches = list(_CODE_RE.finditer(text))
    codes = []
    for m in matches:
        code = f"JB-{int(m.group(1)):04d}"
        if code not in codes:
            codes.append(code)

    # parte do dia: logo depois de cada código ("JB-0032 1/3, JB-0035 2/3")
    per_code = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = text[m.end():end].split("\n")[0]
        p = _find_portion(segment)
        code = f"JB-{int(m.group(1)):04d}"
        if p is not None and code not in per_code:
            per_code[code] = p
    general = _find_portion(text)
    entries = []
    if codes:
        if len(codes) == 1:
            fr = per_code.get(codes[0], general if general is not None else 1.0)
            entries = [(codes[0], _snap_portion(fr))]
        else:
            assigned = sum(per_code.values())
            missing = [c for c in codes if c not in per_code]
            share = (1.0 - assigned) / len(missing) if missing and assigned < 1 else 1.0 / len(codes)
            if not per_code and general is not None:
                share = general  # "dia JB-1 JB-2 / meio dia" → meio dia em cada
            for c in codes:
                entries.append((c, _snap_portion(per_code.get(c, share))))

    # data
    notes = []
    work_date = base
    norm_dates = _strip_portions(norm_all)
    if re.search(r"\banteontem\b", norm_dates):
        work_date = base - timedelta(days=2)
    elif re.search(r"\b(ontem|yesterday)\b", norm_dates):
        work_date = base - timedelta(days=1)
    else:
        m = _DATE_RE.search(norm_dates)
        if m:
            a, b, y = int(m.group(1)), int(m.group(2)), m.group(3)
            # dd/mm (como no Brasil); se o 2º número > 12 só pode ser mm/dd
            day_n, month_n = (a, b) if b <= 12 else (b, a)
            year = int(y) + (2000 if y and len(y) == 2 else 0) if y else base.year
            try:
                d = date(year, month_n, day_n)
                if not y and d > base + timedelta(days=1):
                    d = date(year - 1, month_n, day_n)
                work_date = d
            except ValueError:
                notes.append(f"date '{m.group(0)}' not understood — using the e-mail date")

    # equipe (só se falou de alguém)
    crew, unknown = None, []
    body_norm = normalize(body or "")
    if any(w in body_norm for w in _ALONE):
        crew = []
    else:
        cleaned = _CODE_RE.sub(" ", body or "")
        cleaned = _DATE_RE.sub(" ", _strip_portions(normalize(cleaned)))
        words = [w for w in re.split(r"[^a-z0-9]+", cleaned) if w and w not in _FILLER and not w.isdigit()]
        if words:
            crew = []
            hnorm = [(hid, normalize(name), normalize(name).split()) for hid, name in helpers]
            used = set()
            i = 0
            while i < len(words):
                w = words[i]
                two = f"{w} {words[i + 1]}" if i + 1 < len(words) else None
                hit = None
                if two:
                    hit = next((hid for hid, full, _p in hnorm if full == two or full.startswith(two + " ")), None)
                    if hit:
                        i += 1
                if hit is None:
                    hit = next((hid for hid, full, parts in hnorm if parts and parts[0] == w), None)
                if hit is None and len(w) >= 3:
                    hit = next((hid for hid, full, parts in hnorm if w in parts), None)
                if hit is None:
                    unknown.append(w)
                elif hit not in used:
                    used.add(hit)
                    crew.append(hit)
                i += 1
            if not crew and unknown:
                crew = None  # ninguém reconhecido: mantém a equipe do último dia (com aviso)
    return {"date": work_date, "entries": entries, "crew": crew, "unknown_names": unknown, "notes": notes}


# ── materiais ────────────────────────────────────────────────────────
_UNIT_WORDS = {
    "caixa": "BOX", "caixas": "BOX", "cx": "BOX", "cxs": "BOX", "box": "BOX", "boxes": "BOX", "bx": "BOX",
    "balde": "BUCKET", "baldes": "BUCKET", "bucket": "BUCKET", "buckets": "BUCKET", "pail": "BUCKET",
    "saco": "BAG", "sacos": "BAG", "bag": "BAG", "bags": "BAG",
    "galao": "GAL", "galoes": "GAL", "gal": "GAL", "gallon": "GAL", "gallons": "GAL",
    "rolo": "ROLL", "rolos": "ROLL", "roll": "ROLL", "rolls": "ROLL",
    "tubo": "TUBE", "tubos": "TUBE", "tube": "TUBE", "tubes": "TUBE",
    "un": "EA", "unid": "EA", "unidade": "EA", "unidades": "EA", "ea": "EA", "pc": "EA", "pcs": "EA",
    "peca": "EA", "pecas": "EA", "each": "EA",
    "sf": "SF", "sqft": "SF", "pes": "SF",
}
_STOP = {"de", "do", "da", "of", "the", "x", "e", "and", "para", "pra", "for", "com", "with"}
_QTY_FIRST = re.compile(r"^\s*[-•*]?\s*(\d+(?:[.,]\d+)?)\s*(?:x\s+)?(.+)$", re.IGNORECASE)
_QTY_LAST = re.compile(r"^\s*[-•*]?\s*(.+?)\s*(?:[x×:=\-]\s*)?(\d+(?:[.,]\d+)?)\s*$", re.IGNORECASE)


def parse_material_lines(body):
    """'6 Bostik SL-100' → [(6.0, 'Bostik SL-100', unit_hint)] — linhas sem
    número são ignoradas (vão para 'skipped')."""
    items, skipped = [], []
    for raw in (body or "").replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = _QTY_FIRST.match(line)
        if m:
            qty, rest = m.group(1), m.group(2)
        else:
            m = _QTY_LAST.match(line)
            if not m or not re.search(r"[A-Za-z]", m.group(1)):
                skipped.append(line)
                continue
            rest, qty = m.group(1), m.group(2)
        words = rest.split()
        unit = None
        while words and normalize(words[0]).strip(".,") in set(_UNIT_WORDS) | {"de", "of"}:
            w = normalize(words.pop(0)).strip(".,")
            unit = _UNIT_WORDS.get(w, unit)
        text = " ".join(words).strip(" -:,.")
        if not text:
            skipped.append(line)
            continue
        items.append((float(qty.replace(",", ".")), text, unit))
    return items, skipped


def _tokens(text):
    norm = normalize(text)
    toks = set(t for t in re.split(r"[^a-z0-9\-]+", norm) if t)
    for t in list(toks):
        if "-" in t:
            toks.add(t.replace("-", ""))
            toks.update(p for p in t.split("-") if p)
    return toks


def match_product(text, unit_hint, products):
    """products: [(id, type, name, brand, spec, unit)]. Devolve
    (product_id ou None, certo: bool, pontos)."""
    words = [w for w in _tokens(text) if w not in _STOP and len(w) >= 2]
    if not words:
        return None, False, 0
    scored = []
    for pid, ptype, name, brand, spec, unit in products:
        name_t, brand_t = _tokens(name), _tokens(brand)
        spec_t, type_t = _tokens(spec), _tokens(ptype)
        hay = normalize(" ".join(x or "" for x in (name, brand, spec)))
        score = 0.0
        for w in words:
            if w in name_t or w in brand_t:
                score += 3
            elif w in spec_t:
                score += 2.5 if any(ch.isdigit() for ch in w) else 1.5
            elif w in type_t:
                score += 1
            elif len(w) >= 4 and w in hay.replace("-", ""):
                score += 1
        if unit_hint and unit and unit_hint == (unit or "").upper():
            score += 0.5
        if score:
            scored.append((score, pid))
    if not scored:
        return None, False, 0
    scored.sort(reverse=True)
    best, pid = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0
    sure = best >= 3 and best - second >= 1.5
    return pid, sure, best


class WorkInboxMixin:
    def _setup_work_inboxes(self):
        for attr, handler in (("btn_tool_work_day_inbox", self.open_work_day_inbox_dialog),
                              ("btn_tool_material_inbox", self.open_material_inbox_dialog)):
            btn = QPushButton()
            btn.setObjectName(attr)
            btn.clicked.connect(lambda _c=False, h=handler: h())
            setattr(self.ui, attr, btn)

    def _inbox_ready(self, parent):
        if correio.smtp_ready():
            return True
        QMessageBox.warning(parent, "Email Not Configured",
                            "Set up the e-mail account in Settings → Email first (same one used to send invoices).")
        return False

    def _project_lookup(self, codes):
        """{code: (project_id, quem, último dia ID ou None)}"""
        if not codes:
            return {}
        conn = self._get_connection()
        cur = conn.cursor()
        marks = ",".join(["%s"] * len(codes))
        cur.execute(f"""
            SELECT jp.CODE, jp.ID,
                   COALESCE(NULLIF(cl.FULL_NAME, ''), NULLIF(co.COMPANY_NAME, ''), NULLIF(ct.COMPANY_NAME, ''),
                            ct.FULL_NAME, ''),
                   (SELECT w.ID FROM work_days w WHERE w.JOB_PROJECT_ID = jp.ID AND COALESCE(w.STATUS, '') <> 'CANCELLED'
                    ORDER BY w.WORK_DATE DESC, w.ID DESC LIMIT 1)
            FROM job_projects jp
            LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
            LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
            LEFT JOIN contractors ct ON ct.ID = jp.CONTRACTOR_ID
            WHERE UPPER(jp.CODE) IN ({marks})""", tuple(codes))
        out = {code.upper(): (pid, who, last) for code, pid, who, last in cur.fetchall()}
        cur.close()
        conn.close()
        return out

    def _helpers_list(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ID, COALESCE(NULLIF(FULL_NAME, ''), COMPANY_NAME) FROM helpers ORDER BY FULL_NAME")
        rows = [(hid, name or "") for hid, name in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    def _set_day_crew(self, work_day_id, helper_ids, fraction):
        """Troca a equipe de um dia (pagamento pela diária × parte do dia)."""
        rates = self._helper_daily_rates() if hasattr(self, "_helper_daily_rates") else {}
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM work_day_helpers WHERE WORK_DAY_ID=%s", (work_day_id,))
            pays = []
            for hid in helper_ids:
                pay = round(rates.get(hid, 0) * fraction, 2)
                pays.append(pay)
                cur.execute("INSERT INTO work_day_helpers (WORK_DAY_ID, HELPER_ID, PAY, DAY_FRACTION) "
                            "VALUES (%s,%s,%s,%s)", (work_day_id, hid, pay, fraction))
            cur.execute("UPDATE work_days SET HELPER_ID=%s, HELPER_PAY=%s WHERE ID=%s",
                        (helper_ids[0] if helper_ids else None, round(sum(pays), 2) if pays else None, work_day_id))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    # ═════════════════════════ WORK DAY INBOX ═════════════════════════
    def open_work_day_inbox_dialog(self):
        if self._role_rule("read_only"):
            QMessageBox.information(self, "Read-only", "Your user has read-only access.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Work Day Inbox — log days by e-mail")
        dialog.resize(1000, 600)
        dialog.setStyleSheet(_TABLE_QSS)
        layout = QVBoxLayout(dialog)
        intro = QLabel(
            f"From your phone, send an e-mail to <b>{correio.esc(company_settings.EMAIL_SMTP_USER)}</b> with the "
            f"subject <b>dia JB-0032</b> (two jobs: <b>dia JB-0032 JB-0035</b>). In the text you can add "
            f"<i>meio dia</i>, <i>ontem</i>, <i>19/11</i>, the helpers' names (<i>Juan e Pedro</i>) or "
            f"<i>sozinho</i>. Nothing in the text = full day, same crew as the last day. Nothing is created "
            f"until you click <b>Create checked days</b>.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        top = QHBoxLayout()
        btn_check = QPushButton("  Check inbox")
        btn_check.setIcon(tabler_icon("refresh", "#FFFFFF", 16))
        btn_check.setStyleSheet(_PRIMARY_BTN)
        top.addWidget(btn_check)
        status = QLabel("")
        status.setStyleSheet("color:#6B7C93;")
        top.addWidget(status, 1)
        layout.addLayout(top)
        table = QTableWidget(0, 6)
        table.setObjectName("table_work_day_inbox")
        table.setHorizontalHeaderLabels(["", "Day", "Job Code", "Part of the day", "Crew", "Check"])
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for col, width in ((0, 40), (1, 130), (3, 140), (4, 200)):
            table.setColumnWidth(col, width)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(table, 1)
        bottom = QHBoxLayout()
        btn_ignore = QPushButton("Ignore selected e-mail")
        btn_close = QPushButton("Close")
        btn_create = QPushButton("  Create checked days")
        btn_create.setObjectName("btn_create_inbox_days")
        btn_create.setIcon(tabler_icon("check", "#FFFFFF", 16))
        btn_create.setStyleSheet(_PRIMARY_BTN)
        bottom.addWidget(btn_ignore)
        bottom.addStretch(1)
        bottom.addWidget(btn_close)
        bottom.addWidget(btn_create)
        layout.addLayout(bottom)
        state = {"rows": [], "emails": {}}

        def add_row(mail, code, fraction, parsed, lookup, helpers_by_id, existing):
            r = table.rowCount()
            table.insertRow(r)
            info = lookup.get(code)
            problems = []
            if not info:
                problems.append("Job Code not found")
            elif not info[2]:
                problems.append("this code has no day yet to copy from — use Log today / New job")
            if info and (info[0], parsed["date"]) in existing:
                problems.append(f"already has a day on {parsed['date']:%m/%d}")
            if parsed["unknown_names"]:
                problems.append("unknown name(s): " + ", ".join(parsed["unknown_names"]))
            problems += parsed["notes"]
            chk = QCheckBox()
            can_create = bool(info and info[2])
            chk.setChecked(can_create and not (info and (info[0], parsed["date"]) in existing))
            chk.setEnabled(can_create)
            box = QWidget()
            bl = QHBoxLayout(box)
            bl.setContentsMargins(0, 0, 0, 0)
            bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bl.addWidget(chk)
            table.setCellWidget(r, 0, box)
            d = parsed["date"]
            when = QDateEdit(QDate(d.year, d.month, d.day))
            when.setCalendarPopup(True)
            when.setDisplayFormat("MM/dd/yyyy")
            table.setCellWidget(r, 1, when)
            who = f"  ·  {info[1]}" if info and info[1] else ""
            item = QTableWidgetItem(f"{code}{who}")
            item.setToolTip(f"E-mail: {mail['subject']}\n{mail['body']}")
            table.setItem(r, 2, item)
            portion = make_portion_combo(fraction)
            table.setCellWidget(r, 3, portion)
            if parsed["crew"] is None:
                crew_text = "same as last day"
            elif not parsed["crew"]:
                crew_text = "nobody (alone)"
            else:
                crew_text = ", ".join(helpers_by_id.get(h, "?") for h in parsed["crew"])
            table.setItem(r, 4, QTableWidgetItem(crew_text))
            check = QTableWidgetItem(("⚠️ " + "; ".join(problems)) if problems else "✅ ready")
            check.setForeground(QColor("#B26A00" if problems else "#15803D"))
            table.setItem(r, 5, check)
            state["rows"].append({"uid": mail["uid"], "code": code, "info": info, "chk": chk, "when": when,
                                  "portion": portion, "crew": parsed["crew"], "done": False})

        def check_inbox():
            if not self._inbox_ready(dialog):
                return
            status.setText("Connecting…")
            QApplication.processEvents()
            try:
                mails = correio.fetch_unseen(DAY_KEYWORDS)
                helpers = self._helpers_list()
            except Exception as e:
                status.setText("")
                QMessageBox.critical(dialog, "Connection Error",
                                     f"Could not check the inbox:\n{e}\n\nMake sure IMAP is enabled on the Gmail "
                                     f"account and the App Password in Settings is correct.")
                return
            # assunto tem que ser "dia ..." de verdade (não "diario", "daycare"…)
            mails = [m for m in mails if re.match(r"^(dia|day)\b", normalize(m["subject"]))]
            helpers_by_id = dict(helpers)
            parsed_all = [(m, parse_day_email(m["subject"], m["body"], m["date"], helpers)) for m in mails]
            codes = sorted({c for _m, p in parsed_all for c, _f in p["entries"]})
            try:
                lookup = self._project_lookup(codes)
                existing = set()
                pids = [v[0] for v in lookup.values()]
                if pids:
                    conn = self._get_connection()
                    cur = conn.cursor()
                    cur.execute(f"SELECT JOB_PROJECT_ID, WORK_DATE FROM work_days WHERE COALESCE(STATUS,'') <> 'CANCELLED' "
                                f"AND JOB_PROJECT_ID IN ({','.join(['%s'] * len(pids))})", tuple(pids))
                    existing = set(cur.fetchall())
                    cur.close()
                    conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return
            table.setRowCount(0)
            state["rows"].clear()
            state["emails"] = {m["uid"]: m for m in mails}
            no_code = []
            for m, p in parsed_all:
                if not p["entries"]:
                    no_code.append(m["subject"])
                for code, fr in p["entries"]:
                    add_row(m, code, fr, p, lookup, helpers_by_id, existing)
            msg = f"{len(mails)} e-mail(s), {table.rowCount()} day(s) to review."
            if no_code:
                msg += f"  {len(no_code)} e-mail(s) without a Job Code: " + "; ".join(no_code[:3])
            status.setText(msg if mails else "No new 'dia …' e-mails (they must be unread).")
            dialog._rows = state["rows"]  # usado nos testes

        def finish_emails():
            """Marca como lido o e-mail cujos dias já foram todos tratados."""
            done_uids = []
            for uid in list(state["emails"]):
                rows = [r for r in state["rows"] if r["uid"] == uid]
                if rows and all(r["done"] for r in rows):
                    done_uids.append(uid)
                    state["emails"].pop(uid)
            correio.mark_seen(done_uids)

        def create():
            chosen = [r for r in state["rows"] if not r["done"] and r["chk"].isChecked() and r["info"]]
            if not chosen:
                QMessageBox.information(dialog, "Work Day Inbox", "Tick at least one day that is ready.")
                return
            created = []
            try:
                for r in chosen:
                    fr = float(r["portion"].currentData())
                    day = r["when"].date().toPython()
                    ids = self.log_work_days(day, [(r["info"][0], fr)])
                    if ids and r["crew"] is not None:
                        self._set_day_crew(ids[0], r["crew"], fr)
                    if ids:
                        created.append((r, ids[0], day, fr))
                    r["done"] = True
                    r["chk"].setChecked(False)
                    r["chk"].setEnabled(False)
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not create the day:\n{e}")
            for i, r in enumerate(state["rows"]):
                if r["done"]:
                    table.item(i, 5).setText("✔ created")
                    table.item(i, 5).setForeground(QColor("#1565C0"))
            finish_emails()
            if created:
                parts = ", ".join(f"{r['code']} {d:%m/%d} ({portion_label(fr)})" for r, _i, d, fr in created)
                show_toast(f"Created: {parts}. Open each day to review services and Value.", "success", self)
                if hasattr(self, "refresh_today_card"):
                    self.refresh_today_card()
                try:
                    self.load_work_days()
                except Exception:
                    pass

        def ignore():
            row = table.currentRow()
            if row < 0 or row >= len(state["rows"]):
                QMessageBox.information(dialog, "Ignore", "Click a line of the e-mail you want to ignore.")
                return
            uid = state["rows"][row]["uid"]
            for i, r in enumerate(state["rows"]):
                if r["uid"] == uid and not r["done"]:
                    r["done"] = True
                    r["chk"].setChecked(False)
                    r["chk"].setEnabled(False)
                    table.item(i, 5).setText("ignored")
            finish_emails()

        btn_check.clicked.connect(check_inbox)
        btn_create.clicked.connect(create)
        btn_ignore.clicked.connect(ignore)
        btn_close.clicked.connect(dialog.accept)
        dialog._check, dialog._create, dialog._ignore = check_inbox, create, ignore  # testes
        if correio.smtp_ready():
            QTimer.singleShot(0, check_inbox)
        dialog.exec()

    # ═════════════════════════ MATERIAL INBOX ═════════════════════════
    def _product_rows(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ID, TYPE, NAME, BRAND, SPECIFICATION, UNIT, PRICE FROM products ORDER BY TYPE, NAME")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def _quick_product_dialog(self, parent, guess=""):
        """Cadastro rápido de produto. Devolve o ID novo ou None."""
        d = QDialog(parent)
        d.setWindowTitle("Register product")
        g = QGridLayout(d)
        cmb_type = QComboBox()
        cmb_type.setEditable(True)
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT TYPE FROM products WHERE TYPE IS NOT NULL ORDER BY TYPE")
            cmb_type.addItems([t for (t,) in cur.fetchall()])
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            cmb_type.addItems(["Flooring", "Adhesive", "Preparation", "Underlayment", "Molding", "Others"])
        txt_name, txt_brand, txt_spec = QLineEdit(guess), QLineEdit(), QLineEdit()
        cmb_unit = QComboBox()
        cmb_unit.setEditable(True)
        cmb_unit.addItems(["BOX", "BAG", "BUCKET", "GAL", "ROLL", "TUBE", "EA", "SF", "BUNDLE"])
        price = QDoubleSpinBox()
        price.setRange(0, 1_000_000)
        price.setPrefix("$ ")
        price.setDecimals(2)
        for r, (label, w) in enumerate((("Type", cmb_type), ("Name", txt_name), ("Brand", txt_brand),
                                        ("Specification", txt_spec), ("Unit", cmb_unit), ("Price", price))):
            g.addWidget(QLabel(label), r, 0)
            g.addWidget(w, r, 1)
        row = QHBoxLayout()
        ok, cancel = QPushButton("Save product"), QPushButton("Cancel")
        ok.setStyleSheet(_PRIMARY_BTN)
        row.addStretch(1)
        row.addWidget(cancel)
        row.addWidget(ok)
        g.addLayout(row, 6, 0, 1, 2)
        result = {"id": None}

        def save():
            name = txt_name.text().strip()
            if not name:
                QMessageBox.information(d, "Product", "Enter the product name.")
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO products (TYPE, NAME, BRAND, SPECIFICATION, PRICE, UNIT) "
                            "VALUES (%s,%s,%s,%s,%s,%s)",
                            (cmb_type.currentText().strip() or None, name, txt_brand.text().strip(),
                             txt_spec.text().strip(), price.value(), cmb_unit.currentText().strip().upper() or None))
                result["id"] = cur.lastrowid
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(d, "Database Error", f"Could not save the product:\n{e}")
                return
            d.accept()

        ok.clicked.connect(save)
        cancel.clicked.connect(d.reject)
        d._fields = (cmb_type, txt_name, txt_brand, txt_spec, cmb_unit, price, save)  # testes
        d.exec()
        return result["id"]

    def launch_materials(self, project_id, lines, attachments=(), code=""):
        """lines: [(product_id, qty)]. Soma na linha que já existe do mesmo
        produto no job (como 'Add to it'); senão cria. Preço = preço do
        cadastro (ou $0). Guarda as fotos da nota. Devolve nº de linhas."""
        conn = self._get_connection()
        cur = conn.cursor()
        n = 0
        try:
            for pid, qty in lines:
                if not pid or qty <= 0:
                    continue
                cur.execute("SELECT COALESCE(PRICE, 0) FROM products WHERE ID=%s", (pid,))
                row = cur.fetchone()
                price = float(row[0]) if row else 0.0
                cur.execute("SELECT ID FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s ORDER BY ID LIMIT 1",
                            (project_id, pid))
                existing = cur.fetchone()
                if existing:
                    cur.execute("UPDATE job_materials SET QUANTITY = QUANTITY + %s WHERE ID=%s", (qty, existing[0]))
                else:
                    cur.execute("INSERT INTO job_materials (JOB_PROJECT_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE) "
                                "VALUES (%s,%s,%s,%s)", (project_id, pid, qty, price))
                n += 1
            folder = os.path.join(PROJECT_DIR, "receipts_received")
            for name, data, _ctype in attachments or ():
                os.makedirs(folder, exist_ok=True)
                safe = "".join(ch for ch in name if ch.isalnum() or ch in "._-") or "receipt.jpg"
                path = os.path.join(folder, f"{datetime.now():%Y%m%d_%H%M%S}_{code}_{safe}")
                with open(path, "wb") as f:
                    f.write(data)
                cur.execute("INSERT INTO documents (CATEGORY, ENTITY_TYPE, ENTITY_ID, NAME, FILE_PATH, NOTES) "
                            "VALUES ('Material Receipt', 'JOB_PROJECT', %s, %s, %s, %s)",
                            (project_id, name, os.path.relpath(path, PROJECT_DIR), "Received by e-mail"))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
        return n

    def open_material_inbox_dialog(self):
        if self._role_rule("read_only"):
            QMessageBox.information(self, "Read-only", "Your user has read-only access.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Material Inbox — materials used, by e-mail")
        dialog.resize(1040, 660)
        dialog.setStyleSheet(_TABLE_QSS)
        layout = QVBoxLayout(dialog)
        intro = QLabel(
            f"Send an e-mail to <b>{correio.esc(company_settings.EMAIL_SMTP_USER)}</b> with the subject "
            f"<b>material JB-0032</b> and one material per line: <i>6 Bostik SL-100</i>, <i>2 ProFlex primer</i>, "
            f"<i>12 caixas Bone</i>. A photo of the receipt can go attached. Check each line (✅ = sure, "
            f"⚠️ = choose the product) and click <b>Launch to job</b>.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        top = QHBoxLayout()
        btn_check = QPushButton("  Check inbox")
        btn_check.setIcon(tabler_icon("refresh", "#FFFFFF", 16))
        btn_check.setStyleSheet(_PRIMARY_BTN)
        top.addWidget(btn_check)
        top.addWidget(QLabel("E-mail:"))
        cmb_mail = QComboBox()
        cmb_mail.setMinimumWidth(380)
        top.addWidget(cmb_mail, 1)
        layout.addLayout(top)
        lbl_job = QLabel("")
        lbl_job.setStyleSheet("font-weight:600; color:#334155;")
        layout.addWidget(lbl_job)
        table = QTableWidget(0, 4)
        table.setObjectName("table_material_inbox")
        table.setHorizontalHeaderLabels(["Qty", "Line in the e-mail", "Product", "Check"])
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for col, width in ((0, 110), (1, 240), (3, 120)):
            table.setColumnWidth(col, width)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(table, 1)
        lbl_extra = QLabel("")
        lbl_extra.setWordWrap(True)
        lbl_extra.setStyleSheet("color:#6B7C93;")
        layout.addWidget(lbl_extra)
        bottom = QHBoxLayout()
        btn_new = QPushButton("  Register product for this line")
        btn_new.setIcon(tabler_icon("plus", "#37474F", 16))
        btn_ignore = QPushButton("Ignore this e-mail")
        btn_close = QPushButton("Close")
        btn_launch = QPushButton("  Launch to job")
        btn_launch.setObjectName("btn_launch_inbox_materials")
        btn_launch.setIcon(tabler_icon("check", "#FFFFFF", 16))
        btn_launch.setStyleSheet(_PRIMARY_BTN)
        for b in (btn_new, btn_ignore):
            bottom.addWidget(b)
        bottom.addStretch(1)
        bottom.addWidget(btn_close)
        bottom.addWidget(btn_launch)
        layout.addLayout(bottom)
        state = {"mails": [], "products": [], "lookup": {}, "rows": []}

        def product_label(p):
            pid, ptype, name, brand, spec, unit, price = p
            extra = f" ({brand})" if brand else ""
            pr = f" · ${float(price):,.2f}" if price else " · no price"
            return f"{name}{extra} — {unit or ''}{pr}"

        def fill_combo(combo, selected):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("— choose the product —", None)
            for p in state["products"]:
                combo.addItem(product_label(p), p[0])
            idx = combo.findData(selected) if selected else 0
            combo.setCurrentIndex(max(idx, 0))
            combo.blockSignals(False)

        def set_check(r, sure):
            pid = table.cellWidget(r, 2).currentData()
            item = QTableWidgetItem("✅" if pid and sure else ("⚠️ choose" if not pid else "⚠️ confirm"))
            item.setForeground(QColor("#15803D" if pid and sure else "#B26A00"))
            table.setItem(r, 3, item)

        def show_mail(*_a):
            table.setRowCount(0)
            state["rows"] = []
            i = cmb_mail.currentIndex()
            if i < 0 or i >= len(state["mails"]):
                lbl_job.setText("")
                lbl_extra.setText("")
                return
            m = state["mails"][i]
            codes = [f"JB-{int(x):04d}" for x in _CODE_RE.findall(m["subject"] + " " + m["body"])]
            code = codes[0] if codes else None
            info = state["lookup"].get(code) if code else None
            m["code"], m["project"] = code, info[0] if info else None
            if not code:
                lbl_job.setText("⚠️ No Job Code in the subject — write e.g. 'material JB-0032'.")
            elif not info:
                lbl_job.setText(f"⚠️ {code} was not found.")
            else:
                lbl_job.setText(f"Job {code}" + (f"  ·  {info[1]}" if info[1] else "") +
                                f"  ·  e-mail of {m['date']:%m/%d/%Y %H:%M}")
            items, skipped = parse_material_lines(m["body"])
            catalog = [p[:6] for p in state["products"]]
            for qty, text, unit in items:
                r = table.rowCount()
                table.insertRow(r)
                s = QDoubleSpinBox()
                s.setRange(0, 100_000)
                s.setDecimals(2)
                s.setValue(qty)
                table.setCellWidget(r, 0, s)
                table.setItem(r, 1, QTableWidgetItem(text))
                pid, sure, _score = match_product(text, unit, catalog)
                combo = QComboBox()
                fill_combo(combo, pid)
                combo.currentIndexChanged.connect(lambda _i, row=r: set_check(row, True))
                table.setCellWidget(r, 2, combo)
                set_check(r, sure)
                state["rows"].append({"text": text, "qty": s, "combo": combo})
            extra = []
            if skipped:
                extra.append("Lines without a quantity (not used): " + "; ".join(skipped[:5]))
            pics = [a for a in m["attachments"] if a[2].startswith("image/") or a[2] == "application/pdf"]
            if pics:
                extra.append(f"📎 {len(pics)} attachment(s) will be saved in the job's documents.")
            lbl_extra.setText("   ".join(extra))
            dialog._rows = state["rows"]  # testes

        def check_inbox():
            if not self._inbox_ready(dialog):
                return
            try:
                mails = correio.fetch_unseen(MATERIAL_KEYWORDS)
                state["products"] = self._product_rows()
                codes = sorted({f"JB-{int(x):04d}" for m in mails for x in _CODE_RE.findall(m["subject"] + " " + m["body"])})
                state["lookup"] = self._project_lookup(codes)
            except Exception as e:
                QMessageBox.critical(dialog, "Connection Error", f"Could not check the inbox:\n{e}")
                return
            load_mails(mails)

        def load_mails(mails):
            state["mails"] = list(mails)
            cmb_mail.blockSignals(True)
            cmb_mail.clear()
            for m in state["mails"]:
                cmb_mail.addItem(f"{m['date']:%m/%d %H:%M} — {m['subject']}")
            cmb_mail.blockSignals(False)
            if not state["mails"]:
                lbl_job.setText("No new 'material …' e-mails (they must be unread).")
            show_mail()

        def drop_current():
            i = cmb_mail.currentIndex()
            if 0 <= i < len(state["mails"]):
                state["mails"].pop(i)
                cmb_mail.removeItem(i)
            show_mail()

        def register_new():
            r = table.currentRow()
            if r < 0 or r >= len(state["rows"]):
                QMessageBox.information(dialog, "Register product", "Click the line that has no product first.")
                return
            new_id = self._quick_product_dialog(dialog, state["rows"][r]["text"])
            if not new_id:
                return
            try:
                state["products"] = self._product_rows()
            except (MySQLError, RuntimeError):
                return
            for row in state["rows"]:
                fill_combo(row["combo"], row["combo"].currentData())
            fill_combo(state["rows"][r]["combo"], new_id)
            set_check(r, True)

        def launch():
            i = cmb_mail.currentIndex()
            if i < 0 or i >= len(state["mails"]):
                return
            m = state["mails"][i]
            if not m.get("project"):
                QMessageBox.information(dialog, "Job Code", "This e-mail has no valid Job Code.")
                return
            lines = [(row["combo"].currentData(), row["qty"].value()) for row in state["rows"]]
            missing = [row["text"] for row in state["rows"] if not row["combo"].currentData()]
            if missing:
                QMessageBox.information(dialog, "Choose the products",
                                        "Choose (or register) the product for: " + "; ".join(missing))
                return
            if not lines:
                QMessageBox.information(dialog, "Nothing to launch", "This e-mail has no material lines.")
                return
            try:
                pics = [a for a in m["attachments"] if a[2].startswith("image/") or a[2] == "application/pdf"]
                n = self.launch_materials(m["project"], lines, pics, m["code"])
            except (MySQLError, RuntimeError, OSError) as e:
                QMessageBox.critical(dialog, "Error", f"Could not launch the materials:\n{e}")
                return
            correio.mark_seen([m["uid"]])
            show_toast(f"{n} material line(s) launched in {m['code']}.", "success", self)
            code_open = self.ui.cmb_job_code.currentText().strip().upper() if hasattr(self.ui, "cmb_job_code") else ""
            if code_open == m["code"] and hasattr(self, "_load_job_materials"):
                self._load_job_materials()
            drop_current()

        def ignore():
            i = cmb_mail.currentIndex()
            if 0 <= i < len(state["mails"]):
                correio.mark_seen([state["mails"][i]["uid"]])
                drop_current()

        btn_check.clicked.connect(check_inbox)
        cmb_mail.currentIndexChanged.connect(show_mail)
        btn_new.clicked.connect(register_new)
        btn_launch.clicked.connect(launch)
        btn_ignore.clicked.connect(ignore)
        btn_close.clicked.connect(dialog.accept)
        dialog._check, dialog._launch, dialog._load = check_inbox, launch, load_mails  # testes
        if correio.smtp_ready():
            QTimer.singleShot(0, check_inbox)
        dialog.exec()
