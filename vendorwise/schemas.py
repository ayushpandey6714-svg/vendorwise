"""Shared contracts. Unknown facts are None, never an invented zero."""
from decimal import Decimal
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


Money = Annotated[Decimal, Field(ge=0, le=Decimal("1000000000000"))]
PositiveInt = Annotated[int, Field(gt=0, le=1000000)]
Status = Literal["explicit", "missing", "ambiguous"]
Verdict = Literal["PASS", "FAIL", "UNKNOWN"]


class Evidence(StrictModel):
    page: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=4000)
    document_id: str = ""
    filename: str = ""


T = TypeVar("T")


class Fact(StrictModel, Generic[T]):
    value: T | None
    status: Status
    evidence: list[Evidence]
    note: str = ""

    @model_validator(mode="after")
    def consistent(self):
        if self.status == "explicit" and (self.value is None or not self.evidence):
            raise ValueError("Explicit facts need a value and source evidence")
        if self.status != "explicit" and self.value is not None:
            raise ValueError("Missing/ambiguous facts must not supply a normalized value")
        return self


class Adjustment(StrictModel):
    """Exactly one amount OR percentage; included components are not added again."""
    amount: Money | None
    rate_percent: Annotated[Decimal, Field(ge=0, le=100)] | None
    basis: Literal["fixed", "subtotal", "discounted_subtotal", "discounted_plus_charges"]
    treatment: Literal["add", "included"]

    @model_validator(mode="after")
    def consistent(self):
        if (self.amount is None) == (self.rate_percent is None):
            raise ValueError("Specify exactly one amount or rate")
        if (self.amount is not None) != (self.basis == "fixed"):
            raise ValueError("Amounts use fixed basis; rates need an explicit percentage base")
        return self


class Delivery(StrictModel):
    days: PositiveInt
    day_type: Literal["calendar", "business", "unspecified"]
    trigger: str = Field(min_length=1)


class Quote(StrictModel):
    document_id: str
    filename: str
    vendor: Fact[str]
    manufacturer: Fact[str]
    model: Fact[str]
    currency: Fact[Literal["INR"]]
    quantity: Fact[PositiveInt]
    ram_gb: Fact[PositiveInt]
    storage_gb: Fact[PositiveInt]
    unit_price: Fact[Money]
    unit_price_basis: Fact[Literal["before_tax", "tax_included"]]
    discount: Fact[Adjustment]
    tax: Fact[Adjustment]
    shipping: Fact[Adjustment]
    other_charges: Fact[Adjustment]
    all_charges_disclosed: Fact[bool]
    stated_total: Fact[Money]
    warranty_months: Fact[PositiveInt]
    warranty_terms: Fact[str]
    delivery: Fact[Delivery]
    delivery_terms: Fact[str]


class Extraction(StrictModel):
    supported: bool
    reason: str
    quote: Quote | None


class Requirements(StrictModel):
    quantity: int = Field(ge=1, le=10000)
    budget: Money
    min_ram_gb: int = Field(ge=1, le=1024)
    min_storage_gb: int = Field(ge=1, le=100000)
    min_warranty_months: int = Field(ge=0, le=120)
    max_delivery_days: int = Field(ge=1, le=730)


class WhatIfRequest(StrictModel):
    budget: Money
    min_warranty_months: int = Field(ge=0, le=120)
    max_delivery_days: int = Field(ge=1, le=730)


class Audit(StrictModel):
    document_id: str
    stated_total: Decimal | None
    calculated_total: Decimal | None
    complete: bool
    comparable: bool
    discrepancy: Decimal | None
    issues: list[str]
    steps: list[str]
    source_inputs: list[Evidence]
    tolerance: Decimal = Decimal("0.01")


class Check(StrictModel):
    requirement: str
    status: Verdict
    reason: str
    evidence: list[Evidence]


class OfferResult(StrictModel):
    document_id: str
    vendor: str
    checks: list[Check]
    requirements_status: Verdict
    eligible: bool
    audit: Audit


class Comparison(StrictModel):
    requirements: Requirements
    offers: list[OfferResult]
    eligible_document_ids: list[str]
    recommendation_ids: list[str]
    provisional: bool
    explanation: str


class WhatIfResult(StrictModel):
    previous: Comparison
    updated: Comparison
    changes: list[str]
    savings: Decimal | None


class Document(StrictModel):
    document_id: str
    filename: str
    sha256: str
    pages: list[str]


class Analysis(StrictModel):
    analysis_id: UUID
    requirements: Requirements
    documents: list[Document] = Field(default_factory=list)
    quotes: list[Quote] = Field(default_factory=list)
    mode: Literal["fixture", "live"]
    embedding_backend: Literal["fastembed", "tfidf"]


class AnalysisSummary(StrictModel):
    analysis_id: UUID
    requirements: Requirements
    mode: str
    embedding_backend: str
    documents: list[Document]


class Chunk(StrictModel):
    citation_id: str
    document_id: str
    filename: str
    page: int
    text: str


class SearchArguments(StrictModel):
    query: str = Field(min_length=1, max_length=2000)
    document_ids: list[UUID] | None = None


class CalculateArguments(StrictModel):
    document_id: UUID


class CompareArguments(StrictModel):
    pass


class AskRequest(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    document_ids: list[UUID] | None = None


class AnswerDraft(StrictModel):
    answer: str = Field(min_length=1, max_length=10000)
    citation_ids: list[str]
    evidence_absent: bool
    conflict: bool


class Activity(StrictModel):
    tool: str
    outcome: str


class Answer(StrictModel):
    answer: str
    citations: list[Chunk]
    evidence_absent: bool
    conflict: bool
    activity: list[Activity]
    calculations: list[Audit]
    comparison: Comparison | None = None
    mode: str
    latency_ms: float


class Health(StrictModel):
    status: str
    mode: str
    embedding_backend: str
    provider_configured: bool
    public_demo: bool = False
    ai_requests_per_minute: int = 20
    ai_requests_per_day: int = 100
