import os
import math
from datetime import datetime
from typing import List, Dict, Any, Optional
from fpdf import FPDF


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Multi-Agent Data Assistant Report", ln=1)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, f"Generated: {datetime.utcnow().isoformat()} UTC", ln=1)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def create_pdf_summary(question: str, rows: List[Dict[str, Any]], file_path: Optional[str] = None, chart_path: Optional[str] = None) -> str:
    os.makedirs("artifacts", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out_path = file_path or os.path.join("artifacts", f"report-{ts}.pdf")

    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 20, 15)
    pdf.add_page()
    epw = pdf.w - pdf.l_margin - pdf.r_margin

    # Question summary
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(epw, 7, f"Question: {question}")
    pdf.ln(2)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, f"Rows: {len(rows)}", ln=1)

    # Optional chart image
    if chart_path and os.path.exists(chart_path):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Chart", ln=1)
        try:
            pdf.image(chart_path, w=epw * 0.9)
        except Exception:
            # ignore image errors and continue
            pass
        pdf.ln(2)

    # Table rendering
    if rows:
        # Columns from first row (preserve order)
        first = rows[0]
        cols = list(first.keys())

        # Estimate column widths from header + sample of rows
        padding = 6
        max_widths = []
        sample = rows[:50]
        for c in cols:
            texts = [str(c)] + [str(r.get(c, "")) for r in sample]
            w = max(pdf.get_string_width(t) for t in texts) + padding
            max_widths.append(w)
        total = sum(max_widths)
        if total <= 0:
            total = 1
        scale = epw / total
        col_widths = [w * scale for w in max_widths]

        # Header row
        pdf.set_draw_color(200, 200, 200)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", "B", 10)
        for c, w in zip(cols, col_widths):
            pdf.cell(w, 8, str(c).upper(), border=1, align="C", fill=True)
        pdf.ln(8)

        # Body rows (zebra)
        pdf.set_font("Helvetica", size=10)
        for i, r in enumerate(sample):
            is_alt = (i % 2 == 1)
            if is_alt:
                pdf.set_fill_color(250, 250, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            for c, w in zip(cols, col_widths):
                text = str(r.get(c, ""))
                # Truncate text to fit cell width
                if pdf.get_string_width(text) > (w - 2):
                    ellipsis = "…"
                    while text and pdf.get_string_width(text + ellipsis) > (w - 2):
                        text = text[:-1]
                    text = text + ellipsis if text else ""
                pdf.cell(w, 7, text, border=1, align="L", fill=True)
            pdf.ln(7)

        # Simple numeric summary
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Summary", ln=1)
        pdf.set_font("Helvetica", size=10)
        # Detect numeric columns
        numeric_cols: List[str] = []
        for c in cols:
            ok = True
            for r in sample:
                v = r.get(c, None)
                if v is None or v == "":
                    continue
                try:
                    float(v)
                except Exception:
                    ok = False
                    break
            if ok:
                numeric_cols.append(c)
        if numeric_cols:
            for c in numeric_cols:
                vals = [float(r.get(c, 0) or 0) for r in sample]
                total_val = sum(vals)
                avg_val = (total_val / len(vals)) if vals else 0
                pdf.cell(0, 6, f"{c}: total={total_val:.2f}, avg={avg_val:.2f}", ln=1)
        else:
            pdf.cell(0, 6, "No numeric columns detected.", ln=1)
    else:
        pdf.ln(4)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(epw, 6, "No data rows to display.")

    pdf.output(out_path)
    return out_path
