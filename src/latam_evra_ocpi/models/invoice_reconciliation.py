"""Módulo Invoice Reconciliation (mod_invoicereconciliations), implementado
server-side en el Hub.

Field shapes mirror lib/ocpi/invoiceReconciliation.ts
(toPublicInvoiceReconciliation / invoiceReconciliationInputSchema). Solo
PUT (upsert) — sin POST, a diferencia de CDRs que es POST-only.

Lógica FX (server-side, el SDK solo tipa el resultado): si el body del PUT
incluye discrepancy_amount, el Hub resuelve la moneda del CDR
referenciado, convierte a USD vía Frankfurter, y agrega
discrepancy_currency/discrepancy_amount_usd/exchange_rate_used. Si no,
esos 3 campos vienen ausentes — son opcionales, no asumir que siempre
están presentes.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

__all__ = [
    "InvoiceReconciliationStatus",
    "DiscrepancyAmount",
    "InvoiceReconciliationInput",
    "InvoiceReconciliation",
    "InvoiceReconciliationsPage",
]


class InvoiceReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    DISPUTED = "DISPUTED"
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"


class DiscrepancyAmount(BaseModel):
    excl_vat: float
    incl_vat: float | None = None


class InvoiceReconciliationInput(BaseModel):
    id: str
    cdr_id: str
    invoice_reference_id: str | None = None
    status: InvoiceReconciliationStatus
    discrepancy_description: str | None = None
    discrepancy_amount: DiscrepancyAmount | None = None


class InvoiceReconciliation(InvoiceReconciliationInput):
    country_code: str
    party_id: str
    discrepancy_currency: str | None = None
    discrepancy_amount_usd: DiscrepancyAmount | None = None
    exchange_rate_used: float | None = None
    last_updated: str


class InvoiceReconciliationsPage(BaseModel):
    reconciliations: list[InvoiceReconciliation]
    total: int
