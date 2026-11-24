"""Pure, deterministic business rules. No network, files, floats or LLM calls."""
from decimal import Decimal, ROUND_HALF_UP

from .schemas import (
    Adjustment, Audit, Check, Comparison, Fact, OfferResult, Quote,
    Requirements, WhatIfRequest, WhatIfResult,
)

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def value(fact: Fact):
    return fact.value if fact.status == "explicit" else None


def audit_quote(q: Quote) -> Audit:
    names = ["currency", "quantity", "unit_price", "unit_price_basis", "discount",
             "tax", "shipping", "other_charges", "all_charges_disclosed"]
    sources = [e for name in names + ["stated_total"] for e in getattr(q, name).evidence]
    issues = [f"Clarify {name}: {getattr(q, name).status}." for name in names
              if value(getattr(q, name)) is None]
    if value(q.all_charges_disclosed) is False:
        issues.append("Confirm that all applicable charges have been disclosed.")
    result = Audit(document_id=q.document_id, stated_total=value(q.stated_total),
                   calculated_total=None, complete=False, comparable=False,
                   discrepancy=None, issues=issues, steps=[], source_inputs=sources)
    issues = result.issues
    if issues:
        return result
    discount, tax, shipping, other = [value(getattr(q, n)) for n in
                                    ["discount", "tax", "shipping", "other_charges"]]
    if discount.treatment != "add" or discount.basis not in ("fixed", "subtotal"):
        issues.append("Discount must be a separate deduction with a fixed or subtotal base.")
    if (q.unit_price_basis.value == "tax_included") != (tax.treatment == "included"):
        issues.append("Unit-price tax basis conflicts with tax inclusion; clarify before calculating.")
    if any(c.basis not in ("fixed", "subtotal", "discounted_subtotal") for c in [shipping, other]):
        issues.append("Shipping/other percentage base is circular or unsupported.")
    if tax.treatment == "included" and discount.amount != Decimal(0):
        issues.append("Tax-inclusive prices with a nonzero/rate discount need a clarified tax treatment.")
    if issues:
        return result

    assert q.unit_price.value is not None and q.quantity.value is not None
    subtotal = money(q.unit_price.value * q.quantity.value)
    included_fixed = sum((c.amount for c in (tax, shipping, other)
                          if c.treatment == "included" and c.amount is not None), Decimal(0))
    if included_fixed > subtotal:
        issues.append("Included fixed charges exceed the unit-price subtotal; clarify their bases.")
        return result
    bases = {"subtotal": subtotal}

    def amount(a: Adjustment) -> Decimal:
        if a.amount is not None:
            return money(a.amount)
        assert a.rate_percent is not None  # Adjustment validates exactly one amount/rate.
        return money(bases[a.basis] * a.rate_percent / Decimal(100))

    deducted = amount(discount)
    if deducted > subtotal:
        issues.append("Discount exceeds merchandise subtotal.")
        return result
    discounted = money(subtotal - deducted)
    bases["discounted_subtotal"] = discounted
    shipping_added = amount(shipping) if shipping.treatment == "add" else Decimal(0)
    other_added = amount(other) if other.treatment == "add" else Decimal(0)
    bases["discounted_plus_charges"] = discounted + shipping_added + other_added
    tax_added = amount(tax) if tax.treatment == "add" else Decimal(0)
    calculated = money(discounted + shipping_added + other_added + tax_added)
    result.steps = [
        f"CALCULATION: {q.quantity.value} x INR {q.unit_price.value} = INR {subtotal}",
        f"Discount deducted: INR {deducted}",
        f"Shipping added: INR {shipping_added}; other charges added: INR {other_added}",
        f"Tax added: INR {tax_added} ({tax.treatment}; base: {tax.basis})",
        f"Calculated final total: INR {calculated}. Included charges are not added again.",
    ]
    result.complete = True
    result.calculated_total = calculated
    if result.stated_total is None:
        issues.append("Vendor-stated total is missing or ambiguous; request confirmation.")
    else:
        result.discrepancy = money(result.stated_total - calculated)
        if abs(result.discrepancy) > result.tolerance:
            issues.append(f"Pricing discrepancy of INR {result.discrepancy}; requires vendor clarification.")
        else:
            result.comparable = True
    return result


def compare(quotes: list[Quote], req: Requirements) -> Comparison:
    offers = []
    for q in quotes:
        audit = audit_quote(q)
        checks = []

        def check(name, fact, threshold, relation, unit):
            actual = value(fact)
            status = "UNKNOWN" if actual is None else ("PASS" if relation(actual, threshold) else "FAIL")
            reason = (f"Clarify {name}: {fact.status}. {fact.note}" if actual is None else
                      f"Offered {actual} {unit}; required {threshold} {unit}.")
            checks.append(Check(requirement=name, status=status, reason=reason, evidence=fact.evidence))

        check("quantity", q.quantity, req.quantity, lambda a, b: a == b, "laptops (exact quantity)")
        check("ram", q.ram_gb, req.min_ram_gb, lambda a, b: a >= b, "GB minimum")
        check("storage", q.storage_gb, req.min_storage_gb, lambda a, b: a >= b, "GB minimum")
        check("warranty", q.warranty_months, req.min_warranty_months, lambda a, b: a >= b, "months minimum")
        delivery = value(q.delivery)
        known = delivery is not None and delivery.day_type == "calendar"
        checks.append(Check(requirement="delivery", status=("UNKNOWN" if not known else
                            "PASS" if delivery.days <= req.max_delivery_days else "FAIL"),
                            reason=(f"Offered {delivery.days} calendar days from {delivery.trigger}; "
                                    f"maximum {req.max_delivery_days}." if known else
                                    "Clarify delivery in calendar days and its starting event; business days are not calendar days."),
                            evidence=q.delivery.evidence + q.delivery_terms.evidence))
        # A stated amount can establish a budget check but never establish verified cost.
        budget_amount = audit.calculated_total if audit.comparable else audit.stated_total
        checks.append(Check(requirement="budget", status=("UNKNOWN" if budget_amount is None else
                            "PASS" if budget_amount <= req.budget else "FAIL"),
                            reason=("Clarify total cost." if budget_amount is None else
                                    f"INR {budget_amount} vs budget INR {req.budget}; "
                                    + ("verified total." if audit.comparable else "vendor-stated, UNVERIFIED total.")),
                            evidence=q.stated_total.evidence))
        statuses = [c.status for c in checks]
        overall = "FAIL" if "FAIL" in statuses else "UNKNOWN" if "UNKNOWN" in statuses else "PASS"
        offers.append(OfferResult(document_id=q.document_id, vendor=value(q.vendor) or q.filename,
                                 checks=checks, requirements_status=overall,
                                 eligible=overall == "PASS" and audit.comparable, audit=audit))
    eligible = [o for o in offers if o.eligible]
    lowest = min((o.audit.calculated_total for o in eligible if o.audit.calculated_total is not None), default=None)
    winners = [o for o in eligible if o.audit.calculated_total == lowest]
    # Any unresolved offer without a definitive non-price failure could alter the outcome.
    # An unverified high stated price is not reliable grounds to rule it out.
    unresolved = [o for o in offers if not o.eligible and
                  not any(c.status == "FAIL" and (c.requirement != "budget" or o.audit.comparable)
                          for c in o.checks)]
    provisional = bool(unresolved)
    explanation = ("Lowest verified total among offers passing every mandatory requirement: "
                   + ", ".join(o.vendor for o in winners) + "." if winners else
                   "No offer qualifies with all requirements passed and a verified comparable total.")
    if len(winners) > 1:
        explanation += " Equal-cost tie; no arbitrary vendor preference."
    if provisional:
        explanation += " Provisional: unresolved information in " + ", ".join(o.vendor for o in unresolved) + " could change the outcome."
    return Comparison(requirements=req, offers=offers, eligible_document_ids=[o.document_id for o in eligible],
                      recommendation_ids=[o.document_id for o in winners], provisional=provisional,
                      explanation=explanation)


def what_if(quotes: list[Quote], previous: Requirements, change: WhatIfRequest) -> WhatIfResult:
    updated = Requirements.model_validate({**previous.model_dump(), **change.model_dump()})
    before, after = compare(quotes, previous), compare(quotes, updated)
    changes = [f"{name}: {getattr(previous, name)} -> {getattr(updated, name)}"
               for name in change.model_fields_set if getattr(previous, name) != getattr(updated, name)]
    for old, new in zip(before.offers, after.offers):
        for a, b in zip(old.checks, new.checks):
            if a.status != b.status:
                changes.append(f"{new.vendor}: {b.requirement} {a.status} -> {b.status}. {b.reason}")
    def winner_total(c):
        return next((o.audit.calculated_total for o in c.offers if o.document_id in c.recommendation_ids), None)
    old_cost, new_cost = winner_total(before), winner_total(after)
    savings = money(old_cost - new_cost) if old_cost is not None and new_cost is not None else None
    return WhatIfResult(previous=before, updated=after, changes=sorted(changes), savings=savings)
