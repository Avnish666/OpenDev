export interface Indicator { key: string; label: string; numerator: number | null; denominator: number | null; sample_size: number; state: 'recorded' | 'insufficient_history' | 'unavailable'; formula: string; calculated_at: string; last_updated_at: string | null; limitations: string[]; source_links: string[] }
export interface Profile {
  identity: { user_id: number; github_id: number | null; username: string; avatar_url: string | null; github_profile_url: string | null };
  calculated_at: string; attribution: string; scope: string; participation: Record<string, number>;
  delivery: Indicator[]; rewards: Indicator[];
  financial: { project_id: number; reporting_available: boolean; currency: string; published_reported_spending_cents: number; document_supported_expense_cents: number; last_reporting_activity: string | null; metrics: Indicator[]; notes: string[] }[];
  github: { project_id: number; repository_name: string | null; last_successful_sync_at: string | null; stale: boolean; metrics: Indicator[] }[];
  limitations: string[];
}
export interface PublicProject { id: number; title: string; status: string; role: 'owner' | 'maintainer' | 'collaborator'; project_href: string }
export interface DeliveryRow { milestone_id: number; project_id: number; title: string; status: string; original_deadline: string | null; current_deadline: string; actual_completion_date: string | null; timing: string; ever_asserted_delivered: boolean; reopened_after_delivery: boolean; evidence_links_at_delivery: number | null; independently_reviewed: false; updated_at: string; project_href: string; history_path: string }
export interface Page<T> { items: T[]; total: number; limit: number; offset: number; calculated_at: string }
export function indicatorValue(metric: Indicator): string {
  if (metric.state === 'insufficient_history') return 'Insufficient history';
  if (metric.state === 'unavailable' || metric.numerator === null) return 'Unavailable';
  if (!Number.isSafeInteger(metric.numerator) || (metric.denominator !== null && !Number.isSafeInteger(metric.denominator))) return 'Count exceeds safe browser range';
  return metric.denominator === null ? String(metric.numerator) : `${metric.numerator} / ${metric.denominator}`;
}
export function sourceHref(path: string): string {
  if (!/^\/api\/[a-zA-Z0-9/_-]+$/.test(path)) throw new Error('Invalid source link');
  return `${import.meta.env.VITE_API_URL ?? ''}${path}`;
}
