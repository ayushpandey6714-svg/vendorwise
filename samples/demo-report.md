# VendorWise quotation audit

Analysis: c24b1461-2581-4f46-be68-29e57886e20e
Mode: **fixture** | Local embeddings: **tfidf**

SYNTHETIC FIXTURE DEMO - not real customer data.

## Buyer requirements

- quantity: 20
- budget: 1200000
- min_ram_gb: 16
- min_storage_gb: 512
- min_warranty_months: 36
- max_delivery_days: 14

## Recommendation

Lowest verified total among offers passing every mandatory requirement: Vendor B.

Rule: lowest verified comparable total among offers passing every mandatory requirement.
Rounding: INR 0.01, ROUND_HALF_UP per monetary line; discrepancy tolerance INR 0.01.

## Vendor A

Requirements: FAIL; eligible: False
Vendor-stated total: 1080000.00
Calculated total: 1080000.00; comparable: True

- **quantity: PASS** - Offered 20 laptops (exact quantity); required 20 laptops (exact quantity).
- **ram: PASS** - Offered 16 GB minimum; required 16 GB minimum.
- **storage: PASS** - Offered 512 GB minimum; required 512 GB minimum.
- **warranty: FAIL** - Offered 12 months minimum; required 36 months minimum.
- **delivery: PASS** - Offered 7 calendar days from receipt of purchase order and full payment; maximum 14.
- **budget: PASS** - INR 1080000.00 vs budget INR 1200000; verified total.

### Pricing audit

- CALCULATION: 20 x INR 45000 = INR 900000.00
- Discount deducted: INR 0.00
- Shipping added: INR 18000.00; other charges added: INR 0.00
- Tax added: INR 162000.00 (add; base: discounted_subtotal)
- Calculated final total: INR 1080000.00. Included charges are not added again.

### Extracted facts and source evidence

- **vendor** (explicit): Vendor A
  - vendor_a.pdf, PDF page 1: Supplier: Vendor A
- **manufacturer** (explicit): Example Computing
  - vendor_a.pdf, PDF page 1: Manufacturer: Example Computing (synthetic brand)
- **model** (explicit): StudyBook 14
  - vendor_a.pdf, PDF page 1: Product: StudyBook 14 laptop; one offered configuration only
- **currency** (explicit): INR
  - vendor_a.pdf, PDF page 1: Currency: INR. All amounts below are Indian rupees.
- **quantity** (explicit): 20
  - vendor_a.pdf, PDF page 1: Offered quantity: 20 laptops
- **ram_gb** (explicit): 16
  - vendor_a.pdf, PDF page 1: Memory: 16 GB RAM
- **storage_gb** (explicit): 512
  - vendor_a.pdf, PDF page 1: Storage: 512 GB SSD
- **unit_price** (explicit): 45000
  - vendor_a.pdf, PDF page 1: Unit price: INR 45000.00
- **unit_price_basis** (explicit): before_tax
  - vendor_a.pdf, PDF page 1: Unit prices exclude tax and shipping.
- **discount** (explicit): amount=Decimal('0') rate_percent=None basis='fixed' treatment='add'
  - vendor_a.pdf, PDF page 1: Discount: INR 0.00; no discount applies.
- **tax** (explicit): amount=None rate_percent=Decimal('18') basis='discounted_subtotal' treatment='add'
  - vendor_a.pdf, PDF page 1: Tax: 18% of merchandise subtotal after discount, added separately.
- **shipping** (explicit): amount=Decimal('18000') rate_percent=None basis='fixed' treatment='add'
  - vendor_a.pdf, PDF page 1: Shipping: INR 18000.00, added separately; no further tax on shipping.
- **other_charges** (explicit): amount=Decimal('0') rate_percent=None basis='fixed' treatment='add'
  - vendor_a.pdf, PDF page 1: Other charges: INR 0.00.
- **all_charges_disclosed** (explicit): True
  - vendor_a.pdf, PDF page 1: All applicable charges are listed above. No additional charges apply.
- **stated_total** (explicit): 1080000.00
  - vendor_a.pdf, PDF page 1: FINAL PAYABLE TOTAL: INR 1080000.00
- **warranty_months** (explicit): 12
  - vendor_a.pdf, PDF page 2: Warranty duration: 12 months from delivery.
- **warranty_terms** (explicit): Warranty service: onsite. Exclusions: accidental damage, liquid damage and misuse. Battery replacement is not covered.
  - vendor_a.pdf, PDF page 2: Warranty service: onsite. Exclusions: accidental damage, liquid damage and misuse. Battery replacement is not covered.
- **delivery** (explicit): days=7 day_type='calendar' trigger='receipt of purchase order and full payment'
  - vendor_a.pdf, PDF page 2: Delivery: within 7 calendar days after receipt of purchase order and full payment.
- **delivery_terms** (explicit): Delivery address must be within the supplier's city. Site access must be available.
  - vendor_a.pdf, PDF page 2: Delivery address must be within the supplier's city. Site access must be available.

## Vendor B

Requirements: PASS; eligible: True
Vendor-stated total: 1160000.00
Calculated total: 1160000.00; comparable: True

- **quantity: PASS** - Offered 20 laptops (exact quantity); required 20 laptops (exact quantity).
- **ram: PASS** - Offered 16 GB minimum; required 16 GB minimum.
- **storage: PASS** - Offered 512 GB minimum; required 512 GB minimum.
- **warranty: PASS** - Offered 36 months minimum; required 36 months minimum.
- **delivery: PASS** - Offered 12 calendar days from receipt of purchase order and full payment; maximum 14.
- **budget: PASS** - INR 1160000.00 vs budget INR 1200000; verified total.

### Pricing audit

- CALCULATION: 20 x INR 49000 = INR 980000.00
- Discount deducted: INR 0.00
- Shipping added: INR 3600.00; other charges added: INR 0.00
- Tax added: INR 176400.00 (add; base: discounted_subtotal)
- Calculated final total: INR 1160000.00. Included charges are not added again.

### Extracted facts and source evidence

- **vendor** (explicit): Vendor B
  - vendor_b.pdf, PDF page 1: Supplier: Vendor B
- **manufacturer** (explicit): Example Computing
  - vendor_b.pdf, PDF page 1: Manufacturer: Example Computing (synthetic brand)
- **model** (explicit): StudyBook 14
  - vendor_b.pdf, PDF page 1: Product: StudyBook 14 laptop; one offered configuration only
- **currency** (explicit): INR
  - vendor_b.pdf, PDF page 1: Currency: INR. All amounts below are Indian rupees.
- **quantity** (explicit): 20
  - vendor_b.pdf, PDF page 1: Offered quantity: 20 laptops
- **ram_gb** (explicit): 16
  - vendor_b.pdf, PDF page 1: Memory: 16 GB RAM
- **storage_gb** (explicit): 512
  - vendor_b.pdf, PDF page 1: Storage: 512 GB SSD
- **unit_price** (explicit): 49000
  - vendor_b.pdf, PDF page 1: Unit price: INR 49000.00
- **unit_price_basis** (explicit): before_tax
  - vendor_b.pdf, PDF page 1: Unit prices exclude tax and shipping.
- **discount** (explicit): amount=Decimal('0') rate_percent=None basis='fixed' treatment='add'
  - vendor_b.pdf, PDF page 1: Discount: INR 0.00; no discount applies.
- **tax** (explicit): amount=None rate_percent=Decimal('18') basis='discounted_subtotal' treatment='add'
  - vendor_b.pdf, PDF page 1: Tax: 18% of merchandise subtotal after discount, added separately.
- **shipping** (explicit): amount=Decimal('3600') rate_percent=None basis='fixed' treatment='add'
  - vendor_b.pdf, PDF page 1: Shipping: INR 3600.00, added separately; no further tax on shipping.
- **other_charges** (explicit): amount=Decimal('0') rate_percent=None basis='fixed' treatment='add'
  - vendor_b.pdf, PDF page 1: Other charges: INR 0.00.
- **all_charges_disclosed** (explicit): True
  - vendor_b.pdf, PDF page 1: All applicable charges are listed above. No additional charges apply.
- **stated_total** (explicit): 1160000.00
  - vendor_b.pdf, PDF page 1: FINAL PAYABLE TOTAL: INR 1160000.00
- **warranty_months** (explicit): 36
  - vendor_b.pdf, PDF page 2: Warranty duration: 36 months from delivery.
- **warranty_terms** (explicit): Warranty service: onsite. Exclusions: accidental damage, liquid damage and misuse. Battery replacement is covered for manufacturing defects for 12 months.
  - vendor_b.pdf, PDF page 2: Warranty service: onsite. Exclusions: accidental damage, liquid damage and misuse. Battery replacement is covered for manufacturing defects for 12 months.
- **delivery** (explicit): days=12 day_type='calendar' trigger='receipt of purchase order and full payment'
  - vendor_b.pdf, PDF page 2: Delivery: within 12 calendar days after receipt of purchase order and full payment.
- **delivery_terms** (explicit): Delivery address must be within the supplier's city. Site access must be available.
  - vendor_b.pdf, PDF page 2: Delivery address must be within the supplier's city. Site access must be available.

## Vendor C

Requirements: PASS; eligible: True
Vendor-stated total: 1190000.00
Calculated total: 1190000.00; comparable: True

- **quantity: PASS** - Offered 20 laptops (exact quantity); required 20 laptops (exact quantity).
- **ram: PASS** - Offered 16 GB minimum; required 16 GB minimum.
- **storage: PASS** - Offered 512 GB minimum; required 512 GB minimum.
- **warranty: PASS** - Offered 36 months minimum; required 36 months minimum.
- **delivery: PASS** - Offered 8 calendar days from receipt of purchase order and full payment; maximum 14.
- **budget: PASS** - INR 1190000.00 vs budget INR 1200000; verified total.

### Pricing audit

- CALCULATION: 20 x INR 50000 = INR 1000000.00
- Discount deducted: INR 0.00
- Shipping added: INR 10000.00; other charges added: INR 0.00
- Tax added: INR 180000.00 (add; base: discounted_subtotal)
- Calculated final total: INR 1190000.00. Included charges are not added again.

### Extracted facts and source evidence

- **vendor** (explicit): Vendor C
  - vendor_c.pdf, PDF page 1: Supplier: Vendor C
- **manufacturer** (explicit): Example Computing
  - vendor_c.pdf, PDF page 1: Manufacturer: Example Computing (synthetic brand)
- **model** (explicit): StudyBook 14
  - vendor_c.pdf, PDF page 1: Product: StudyBook 14 laptop; one offered configuration only
- **currency** (explicit): INR
  - vendor_c.pdf, PDF page 1: Currency: INR. All amounts below are Indian rupees.
- **quantity** (explicit): 20
  - vendor_c.pdf, PDF page 1: Offered quantity: 20 laptops
- **ram_gb** (explicit): 16
  - vendor_c.pdf, PDF page 1: Memory: 16 GB RAM
- **storage_gb** (explicit): 512
  - vendor_c.pdf, PDF page 1: Storage: 512 GB SSD
- **unit_price** (explicit): 50000
  - vendor_c.pdf, PDF page 1: Unit price: INR 50000.00
- **unit_price_basis** (explicit): before_tax
  - vendor_c.pdf, PDF page 1: Unit prices exclude tax and shipping.
- **discount** (explicit): amount=Decimal('0') rate_percent=None basis='fixed' treatment='add'
  - vendor_c.pdf, PDF page 1: Discount: INR 0.00; no discount applies.
- **tax** (explicit): amount=None rate_percent=Decimal('18') basis='discounted_subtotal' treatment='add'
  - vendor_c.pdf, PDF page 1: Tax: 18% of merchandise subtotal after discount, added separately.
- **shipping** (explicit): amount=Decimal('10000') rate_percent=None basis='fixed' treatment='add'
  - vendor_c.pdf, PDF page 1: Shipping: INR 10000.00, added separately; no further tax on shipping.
- **other_charges** (explicit): amount=Decimal('0') rate_percent=None basis='fixed' treatment='add'
  - vendor_c.pdf, PDF page 1: Other charges: INR 0.00.
- **all_charges_disclosed** (explicit): True
  - vendor_c.pdf, PDF page 1: All applicable charges are listed above. No additional charges apply.
- **stated_total** (explicit): 1190000.00
  - vendor_c.pdf, PDF page 1: FINAL PAYABLE TOTAL: INR 1190000.00
- **warranty_months** (explicit): 36
  - vendor_c.pdf, PDF page 2: Warranty duration: 36 months from delivery.
- **warranty_terms** (explicit): Warranty service: onsite. Exclusions: accidental damage, liquid damage and misuse.
  - vendor_c.pdf, PDF page 2: Warranty service: onsite. Exclusions: accidental damage, liquid damage and misuse.
- **delivery** (explicit): days=8 day_type='calendar' trigger='receipt of purchase order and full payment'
  - vendor_c.pdf, PDF page 2: Delivery: within 8 calendar days after receipt of purchase order and full payment.
- **delivery_terms** (explicit): Delivery address must be within the supplier's city. Site access must be available.
  - vendor_c.pdf, PDF page 2: Delivery address must be within the supplier's city. Site access must be available.

Mechanical evidence validation checks page/text existence, not correctness of every interpretation.
Session isolation is not authentication. Review supplier terms before any purchasing decision.
