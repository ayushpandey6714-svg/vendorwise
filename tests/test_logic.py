from decimal import Decimal

import pytest
from pydantic import ValidationError

from vendorwise.logic import audit_quote, compare, money, what_if
from vendorwise.schemas import Adjustment, Fact, WhatIfRequest


def missing(fact):
    return type(fact)(value=None, status="missing", evidence=[])


def test_expected_demo_and_whatif(quote_factory, requirements):
    quotes = [quote_factory(f"vendor_{v}") for v in "abc"]
    before = compare(quotes, requirements)
    assert [o.vendor for o in before.offers if o.eligible] == ["Vendor C"]
    assert [audit_quote(q).calculated_total for q in quotes] == [Decimal("1080000"), Decimal("1160000"), Decimal("1190000")]
    result = what_if(quotes, requirements, WhatIfRequest(budget="1200000", min_warranty_months=36, max_delivery_days=14))
    assert result.updated.recommendation_ids == [quotes[1].document_id]
    assert result.savings == Decimal("30000.00")
    assert any("delivery FAIL -> PASS" in c for c in result.changes)
    assert result.updated.requirements.quantity == 20
    assert compare(quotes, requirements) == before


@pytest.mark.parametrize("raw,expected", [("1.005", "1.01"), ("1.004", "1.00"), ("2.675", "2.68"), ("0.1", "0.10")])
def test_decimal_rounding(raw, expected):
    assert money(Decimal(raw)) == Decimal(expected)


def test_missing_is_not_zero(quote_factory):
    q = quote_factory()
    assert audit_quote(q).comparable
    assert q.other_charges.value.amount == 0
    q.other_charges = missing(q.other_charges)
    result = audit_quote(q)
    assert not result.complete and result.calculated_total is None
    assert "other_charges" in " ".join(result.issues)


def test_no_tax_or_shipping_double_count(quote_factory):
    q = quote_factory()
    q.unit_price.value = Decimal("59500")
    q.unit_price_basis.value = "tax_included"
    q.tax.value.treatment = "included"
    q.shipping.value.treatment = "included"
    result = audit_quote(q)
    assert result.calculated_total == Decimal("1190000") and result.comparable


def test_conflicting_inclusion_cannot_be_verified(quote_factory):
    q = quote_factory()
    q.tax.value.treatment = "included"
    result = audit_quote(q)
    assert not result.complete and "conflicts" in " ".join(result.issues)


def test_explicit_percentage_discount_and_tax_base(quote_factory):
    q = quote_factory()
    q.discount.value = Adjustment(amount=None, rate_percent="10", basis="subtotal", treatment="add")
    q.stated_total.value = Decimal("1072000")
    result = audit_quote(q)
    assert result.calculated_total == Decimal("1072000") and result.comparable


def test_tax_on_shipping_explicit_base(quote_factory):
    q = quote_factory()
    q.tax.value.basis = "discounted_plus_charges"
    q.stated_total.value = Decimal("1191800")
    assert audit_quote(q).comparable


def test_circular_charge_base_is_rejected(quote_factory):
    q = quote_factory()
    q.shipping.value = Adjustment(amount=None, rate_percent="1", basis="discounted_plus_charges", treatment="add")
    assert not audit_quote(q).complete


@pytest.mark.parametrize("sample", ["ambiguous_tax", "incorrect_total"])
def test_unresolved_price_ineligible(quote_factory, requirements, sample):
    q = quote_factory(sample)
    result = compare([q], requirements)
    assert not result.recommendation_ids and not result.offers[0].eligible
    assert result.provisional


def test_discrepancy_tolerance(quote_factory):
    q = quote_factory()
    q.stated_total.value += Decimal("0.01")
    assert audit_quote(q).comparable
    q.stated_total.value += Decimal("0.01")
    assert not audit_quote(q).comparable


def test_missing_total_allows_calculation_but_not_verification(quote_factory):
    q = quote_factory()
    q.stated_total = missing(q.stated_total)
    audit = audit_quote(q)
    assert audit.complete and not audit.comparable and audit.stated_total is None


def test_missing_warranty_unknown(quote_factory, requirements):
    offer = compare([quote_factory("missing_warranty")], requirements).offers[0]
    assert offer.requirements_status == "UNKNOWN"
    assert next(c for c in offer.checks if c.requirement == "warranty").status == "UNKNOWN"


def test_business_days_never_silently_converted(quote_factory, requirements):
    q = quote_factory()
    q.delivery.value.day_type = "business"
    offer = compare([q], requirements).offers[0]
    assert next(c for c in offer.checks if c.requirement == "delivery").status == "UNKNOWN"


def test_quantity_mismatch_and_no_qualifying(quote_factory, requirements):
    for name in ("quantity_mismatch", "no_qualifying"):
        result = compare([quote_factory(name)], requirements)
        assert result.offers[0].requirements_status == "FAIL"
        assert not result.recommendation_ids


def test_incomplete_offer_makes_winner_provisional(quote_factory, requirements):
    result = compare([quote_factory(), quote_factory("missing_warranty")], requirements)
    assert result.recommendation_ids and result.provisional


def test_equal_cost_tie(quote_factory, requirements):
    first, second = quote_factory(), quote_factory()
    result = compare([first, second], requirements)
    assert result.recommendation_ids == [first.document_id, second.document_id]


def test_negative_nonfinite_and_fact_status_validation():
    with pytest.raises(ValidationError):
        Adjustment(amount="NaN", rate_percent=None, basis="fixed", treatment="add")
    with pytest.raises(ValidationError):
        Adjustment(amount="-1", rate_percent=None, basis="fixed", treatment="add")
    with pytest.raises(ValidationError):
        Fact[int](value=0, status="missing", evidence=[])
    with pytest.raises(ValidationError):
        Fact[int](value=3, status="explicit", evidence=[])


def test_no_quantity_changes_in_whatif():
    with pytest.raises(ValidationError):
        WhatIfRequest(budget="1200000", min_warranty_months=36, max_delivery_days=14, quantity=10)
