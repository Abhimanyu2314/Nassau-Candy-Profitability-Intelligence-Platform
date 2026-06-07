from datetime import datetime
from io import BytesIO

from fpdf import FPDF


def _safe_text(value):
    """Keep PDF text compatible with core fonts."""
    text = str(value)
    replacements = {
        "–": "-", "—": "-", "“": '"', "”": '"', "’": "'", "•": "-"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


class ExecutivePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(15, 23, 42)
        self.cell(0, 8, _safe_text("Nassau Candy Profitability Intelligence Report"), ln=True)
        self.set_draw_color(15, 118, 110)
        self.line(10, 20, 200, 20)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _section(pdf, title):
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 118, 110)
    pdf.cell(0, 8, _safe_text(title), ln=True)
    pdf.set_text_color(15, 23, 42)


def _para(pdf, text):
    """Render paragraph safely without FPDF horizontal-space errors."""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(pdf.l_margin)
    safe = _safe_text(text)

    # FPDF can fail when a very long token has no safe break point.
    # Insert soft spaces into long tokens and always use a fixed usable width.
    fixed_words = []
    for word in safe.split(" "):
        if len(word) > 45:
            word = " ".join(word[i:i+35] for i in range(0, len(word), 35))
        fixed_words.append(word)
    safe = " ".join(fixed_words)

    usable_width = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.multi_cell(usable_width, 6, safe)
    pdf.set_x(pdf.l_margin)


def _mini_table(pdf, rows, col_widths=(58, 42, 42, 32)):
    """Small PDF table with safe text truncation."""
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(15, 118, 110)
    pdf.set_text_color(255, 255, 255)
    headers = rows[0]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, _safe_text(h)[:22], border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(15, 23, 42)
    for row in rows[1:]:
        pdf.set_x(pdf.l_margin)
        for i, cell in enumerate(row):
            txt = _safe_text(cell).replace("\n", " ")[:28]
            pdf.cell(col_widths[i], 7, txt, border=1)
        pdf.ln()
    pdf.set_x(pdf.l_margin)


def build_executive_pdf(products, divisions, factories, monthly, total_sales, total_profit, avg_margin, risk_count, margin_threshold):
    """Return a PDF report as bytes for Streamlit download_button."""
    pdf = ExecutivePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 10, _safe_text("Product Line Profitability & Margin Performance Analysis"))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 7, _safe_text(f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}"), ln=True)

    _section(pdf, "Executive Summary")
    _para(pdf, (
        "This report evaluates product-line profitability for Nassau Candy Distributor by analyzing sales, cost, "
        "gross profit, margin percentage, division performance, factory contribution, and product-level margin risk. "
        "The objective is to identify products that truly drive profit, detect high-sales but weak-margin products, "
        "and support pricing, sourcing, promotion, and portfolio rationalization decisions."
    ))

    _section(pdf, "Key Performance Indicators")
    rows = [
        ["Metric", "Value", "Interpretation", "Status"],
        ["Total Sales", f"${total_sales:,.2f}", "Filtered revenue", "Tracked"],
        ["Gross Profit", f"${total_profit:,.2f}", "Sales minus cost", "Tracked"],
        ["Average Margin", f"{avg_margin:,.2f}%", "Portfolio efficiency", "Tracked"],
        ["Risk Products", str(risk_count), f"Below {margin_threshold}% margin", "Review"],
    ]
    _mini_table(pdf, rows)

    _section(pdf, "Top Profit Products")
    top = products.sort_values("Gross Profit", ascending=False).head(8)
    rows = [["Product", "Division", "Gross Profit", "Margin %"]]
    for _, r in top.iterrows():
        rows.append([r["Product Name"], r["Division"], f"${r['Gross Profit']:,.2f}", f"{r['Gross Margin %']:.2f}%"])
    _mini_table(pdf, rows)

    _section(pdf, "Division Performance")
    rows = [["Division", "Sales", "Gross Profit", "Margin %"]]
    for _, r in divisions.sort_values("Gross Profit", ascending=False).iterrows():
        rows.append([r["Division"], f"${r['Sales']:,.2f}", f"${r['Gross Profit']:,.2f}", f"{r['Gross Margin %']:.2f}%"])
    _mini_table(pdf, rows)

    _section(pdf, "Factory Intelligence")
    rows = [["Factory", "Sales", "Gross Profit", "Margin %"]]
    for _, r in factories.sort_values("Gross Profit", ascending=False).iterrows():
        rows.append([r["Factory"], f"${r['Sales']:,.2f}", f"${r['Gross Profit']:,.2f}", f"{r['Gross Margin %']:.2f}%"])
    _mini_table(pdf, rows)

    _section(pdf, "Management Recommendations")
    recommendations = []
    if risk_count > 0:
        recommendations.append(f"Review {risk_count} products below the selected {margin_threshold}% margin threshold.")
    best = products.sort_values("Gross Profit", ascending=False).iloc[0]
    recommendations.append(f"Prioritize promotion and stocking for top profit driver: {best['Product Name']}.")
    low_margin = products.sort_values("Gross Margin %", ascending=True).head(3)
    recommendations.append("Investigate pricing or cost renegotiation for the lowest-margin products: " + ", ".join(low_margin["Product Name"].astype(str).tolist()) + ".")
    recommendations.append("Use the Pareto view to monitor over-dependency on a small number of high-profit products.")
    recommendations.append("Compare factory-level margins before expanding production or supplier contracts.")
    for rec in recommendations:
        _para(pdf, "- " + rec)

    result = pdf.output(dest="S")
    if isinstance(result, str):
        return result.encode("latin-1")
    return bytes(result)
