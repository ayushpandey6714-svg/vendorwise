"""Generate clearly synthetic two-page PDFs, exact-hash fixtures, and two layouts."""
import hashlib
import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]


def generate(output: Path = ROOT / "samples"):
    output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    specs = [
        ("vendor_a", "Vendor A", 45000, 18000, 12, 7, "normal"),
        ("vendor_b", "Vendor B", 49000, 3600, 36, 12, "normal"),
        ("vendor_c", "Vendor C", 50000, 10000, 36, 8, "normal"),
        ("incorrect_total", "Vendor C", 50000, 10000, 36, 8, "incorrect_total"),
        ("missing_warranty", "Vendor C", 50000, 10000, None, 8, "missing_warranty"),
        ("ambiguous_tax", "Vendor C", 50000, 10000, 36, 8, "ambiguous_tax"),
        ("missing_battery", "Vendor B", 49000, 3600, 36, 12, "missing_battery"),
        ("no_qualifying", "Vendor A", 45000, 18000, 6, 30, "no_qualifying"),
        ("quantity_mismatch", "Vendor C", 50000, 10000, 36, 8, "quantity_mismatch"),
    ]
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#174F48")
    styles["BodyText"].leading = 16

    for idx, (slug, vendor, unit, shipping, warranty, days, case) in enumerate(specs):
        qty = 19 if case == "quantity_mismatch" else 20
        subtotal = Decimal(unit * qty)
        tax = subtotal * Decimal("0.18")
        total = subtotal + tax + shipping
        stated = total + (500 if case == "incorrect_total" else 0)
        quote: dict[str, Any] = {"document_id": "", "filename": f"{slug}.pdf"}
        lines = {1: [], 2: []}

        def add(name, value, text, page=1, status="explicit", note=""):
            quote[name] = {"value": value, "status": status,
                           "evidence": [{"page": page, "text": text}] if text else [], "note": note}
            if text:
                lines[page].append(text)

        def adjustment(amount=None, rate=None, basis="fixed", treatment="add"):
            return {"amount": str(amount) if amount is not None else None,
                    "rate_percent": str(rate) if rate is not None else None,
                    "basis": basis, "treatment": treatment}

        add("vendor", vendor, f"Supplier: {vendor}")
        add("manufacturer", "Example Computing", "Manufacturer: Example Computing (synthetic brand)")
        add("model", "StudyBook 14", "Product: StudyBook 14 laptop; one offered configuration only")
        add("currency", "INR", "Currency: INR. All amounts below are Indian rupees.")
        add("quantity", qty, f"Offered quantity: {qty} laptops")
        add("ram_gb", 16, "Memory: 16 GB RAM")
        add("storage_gb", 512, "Storage: 512 GB SSD")
        add("unit_price", str(unit), f"Unit price: INR {unit:.2f}")
        if case == "ambiguous_tax":
            add("unit_price_basis", None, "Tax inclusion in unit price is to be confirmed.", status="ambiguous")
            add("tax", None, "Tax: 18%; whether already included is to be confirmed.", status="ambiguous")
        else:
            add("unit_price_basis", "before_tax", "Unit prices exclude tax and shipping.")
            add("tax", adjustment(rate=18, basis="discounted_subtotal"),
                "Tax: 18% of merchandise subtotal after discount, added separately.")
        add("discount", adjustment(amount=0), "Discount: INR 0.00; no discount applies.")
        add("shipping", adjustment(amount=shipping),
            f"Shipping: INR {shipping:.2f}, added separately; no further tax on shipping.")
        add("other_charges", adjustment(amount=0), "Other charges: INR 0.00.")
        add("all_charges_disclosed", True, "All applicable charges are listed above. No additional charges apply.")
        add("stated_total", str(stated), f"FINAL PAYABLE TOTAL: INR {stated:.2f}")
        add("warranty_months", warranty,
            f"Warranty duration: {warranty} months from delivery." if warranty else "", page=2,
            status="explicit" if warranty else "missing", note="Warranty duration not stated." if not warranty else "")
        terms = "Warranty service: onsite. Exclusions: accidental damage, liquid damage and misuse."
        if case != "missing_battery" and vendor == "Vendor B":
            terms += " Battery replacement is covered for manufacturing defects for 12 months."
        elif vendor == "Vendor A":
            terms += " Battery replacement is not covered."
        add("warranty_terms", terms, terms, page=2)
        add("delivery", {"days": days, "day_type": "calendar", "trigger": "receipt of purchase order and full payment"},
            f"Delivery: within {days} calendar days after receipt of purchase order and full payment.", page=2)
        delivery_terms = "Delivery address must be within the supplier's city. Site access must be available."
        add("delivery_terms", delivery_terms, delivery_terms, page=2)
        lines[2] += ["This document is synthetic training data. It is not a commercial offer or tax advice."]
        story = []
        for page in (1, 2):
            story += [Paragraph("VENDORWISE / SYNTHETIC DEMO", styles["Title"]),
                      Paragraph(f"{vendor} | {'Commercial quotation' if page == 1 else 'Warranty and delivery terms'}", styles["Heading2"]),
                      Paragraph(f"Sample reference: {slug}. No real customer or supplier data.", styles["BodyText"]),
                      Spacer(1, 18)]
            if idx % 2 == 0 and page == 1:
                table = Table([[Paragraph(line, styles["BodyText"])] for line in lines[page]], colWidths=[465])
                table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F5F3")),
                                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                           ("TOPPADDING", (0, 0), (-1, -1), 6),
                                           ("LINEBELOW", (0, 0), (-1, -1), .25, colors.white)]))
                story.append(table)
            else:
                for line in lines[page]:
                    story += [Paragraph(line, styles["BodyText"]), Spacer(1, 7)]
            if page == 1:
                story.append(PageBreak())

        def footer(canvas, doc):
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(colors.HexColor("#53645F"))
            canvas.drawString(54, 30, "SYNTHETIC / FOR PORTFOLIO DEMONSTRATION ONLY")
            canvas.drawRightString(A4[0] - 54, 30, f"Page {doc.page}")

        target = output / f"{slug}.pdf"
        doc = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=54, leftMargin=54,
                                topMargin=40, bottomMargin=48, invariant=1)
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest[digest] = {"sample": slug, "quote": deepcopy(quote)}
    (output / "fixture_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(specs)} synthetic PDFs and an exact-SHA256 fixture manifest in {output}")


if __name__ == "__main__":
    generate()
