import type { DeliveryRow } from './credibility';
import type { RoadmapHistory } from './roadmap';
export interface Counts { total: number; planned: number; in_progress: number; submitted_for_review: number; delivered: number; cancelled: number; overdue_unfinished: number; reopened: number; on_time: number; late: number; unknown_delivery_timing: number }
interface GitHubItem { github_id: number; number: number; title: string; state: string; updated_at: string; merged_at?: string | null }
export interface ProgressSummary {
  project_id: number; github_repository_id: number; calculated_at: string; roadmap_updated_at: string | null; counts: Counts;
  linked_issues: number | null; linked_merged_pull_requests: number | null; github_available: boolean; linked_evidence_stale: boolean | null;
  sync: { latest: { status: string; started_at: string; completed_at: string | null; error_code: string | null } | null; last_successful_sync_at: string | null; stale: boolean };
  snapshot_age_seconds: number | null;
  activity: { repository: { full_name: string }; counts: Record<string, number>; issues: GitHubItem[]; pull_requests: GitHubItem[]; recent_commits: { sha: string; committed_at: string }[] } | null;
  github_milestones: { github_id: number; number: number; title: string; state: string; open_issues: number; closed_issues: number; last_synced_at: string }[];
  delivery_history_preview: DeliveryRow[];
  recent_changes: (RoadmapHistory & { milestone_id: number; title: string })[];
  owner: { identity: { user_id: number; username: string }; public_projects: number; delivery: Counts; profile_href: string; scope: string };
  financial: { currency: string; gross_completed_funding_cents: number; refund_excluded_cents: number; reversal_excluded_cents: number; net_recorded_funding_cents: number; published_reported_spending_cents: number; funding_minus_reported_expenditure_cents: number; expenses_with_documents_count: number; expenses_with_documents_cents: number; published_expense_count: number; public_unresolved_discrepancy_count: number; notes: string[] };
  links: Record<string, string>; limitations: string[];
}
export function githubSource(name: string, kind: 'issues' | 'pull' | 'milestone' | 'commit', id: number | string): string {
  if (!/^[A-Za-z0-9-]{1,39}\/[A-Za-z0-9_.-]{1,100}$/.test(name) || name.split('/').some(p => p === '.' || p === '..')) throw new Error('Invalid repository name');
  if (kind === 'commit' ? !/^[0-9a-f]{40}$/.test(String(id)) : !Number.isSafeInteger(id) || Number(id) <= 0) throw new Error('Invalid GitHub identifier');
  return `https://github.com/${name}/${kind}/${id}`;
}
export function onTimeLabel(counts: Counts): string {
  const known = counts.on_time + counts.late;
  return known ? `${counts.on_time} / ${known} dated delivery assertions were on time` : 'Insufficient history for delivery timing';
}
