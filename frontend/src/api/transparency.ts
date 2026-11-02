import { api } from './client';

export interface PublicFinding { category: string; finding_code: 'CATEGORY_BUDGET_OVERRUN'; severity: 'warning'; explanation: string; unresolved: true; scope: 'published_category_totals' }
export interface PublicEvidence { id: string; detected_mime_type: string; status: 'approved_redacted' }
export interface LedgerEntry {
  id: number; project_id: number; currency: string; category: string; vendor: string; description: string;
  amount_cents: number; expense_date: string; updated_at: string;
  public_evidence_status: 'self_reported' | 'approved_redacted_document_attached';
  evidence: PublicEvidence[]; findings: PublicFinding[]; independently_payment_matched: false;
}
export interface BudgetVariance { category: string; allocated_cents: number; reported_spending_cents: number; remaining_cents: number; overspend_cents: number }
export interface PublicTransparency {
  financial_summary: {
    currency: string; gross_completed_funding_cents: number; refund_excluded_cents: number; reversal_excluded_cents: number;
    net_recorded_funding_cents: number; published_reported_spending_cents: number; funding_minus_reported_expenditure_cents: number;
    expenses_with_documents_count: number; expenses_with_documents_cents: number; expenses_without_documents_count: number;
    expenses_without_documents_cents: number; published_expense_count: number; budget_variance: BudgetVariance[]; notes: string[];
  };
  public_findings: PublicFinding[]; public_unresolved_discrepancy_count: number; private_discrepancy_count: null;
  finding_policy: string; last_updated_at: string; timestamp_basis: string;
}
export interface LedgerPage { project_id: number; items: LedgerEntry[]; total: number; limit: number; offset: number; sort: 'date_desc' | 'date_asc'; calculated_at: string }

export const transparencyAPI = {
  overview: (projectId: number) => api<PublicTransparency>(`/api/projects/${projectId}/transparency`),
  ledger: (projectId: number, params: URLSearchParams) => api<LedgerPage>(`/api/projects/${projectId}/ledger?${params}`),
  detail: (projectId: number, expenseId: number) => api<LedgerEntry>(`/api/projects/${projectId}/ledger/${expenseId}`),
};

export function displayMoney(value: number, currency: string) {
  if (!Number.isSafeInteger(value)) return 'Amount exceeds safe browser display range; inspect the API integer value.';
  const amount = BigInt(value); const absolute = amount < 0n ? -amount : amount;
  return `${amount < 0n ? '-' : ''}${absolute / 100n}.${String(absolute % 100n).padStart(2, '0')} ${currency}`;
}
