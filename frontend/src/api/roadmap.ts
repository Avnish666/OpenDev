/** Flat, dated commitments usable by a future Gantt adapter; no completion percentages. */
export type RoadmapStatus = 'planned' | 'in_progress' | 'submitted_for_review' | 'delivered' | 'cancelled';
export interface RoadmapEvidence { id: string; evidence_type: string; canonical_id: string | null; url: string | null; state: string | null; merged: boolean | null; stale: boolean; snapshot_available: boolean; last_observed_at: string | null }
export interface RoadmapMilestone {
  id: number; project_id: number; title: string; description: string; deliverable_description: string;
  planned_start_date: string; planned_end_date: string; actual_completion_date: string | null;
  status: RoadmapStatus; display_order: number; version: number; created_by: number;
  created_at: string; updated_at: string; evidence: RoadmapEvidence[];
  development_signals: Record<string, number>; notice: string;
}
export interface RoadmapPage { items: RoadmapMilestone[]; total: number; limit: number; offset: number }
export interface RoadmapHistory { id: string; version: number; previous_status: RoadmapStatus | null; new_status: RoadmapStatus; actor_id: number; action: string; reason: string; before: Record<string, unknown>; after: Record<string, unknown>; created_at: string }
