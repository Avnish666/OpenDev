import type { TaskModelConfig } from '@bryntum/gantt-community';
import { api } from './client';
import type { RoadmapMilestone } from './roadmap';

export interface Dependency { id: number; project_id: number; from_id: number; to_id: number }
export interface DateProposal { milestoneId: number; start: string; end: string }
export type MappedTask = TaskModelConfig & { opendev: { status: string; deliverable: string; displayOrder: number; signals: Record<string, number>; stale: boolean } };

export function calendarDate(value: string): Date {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error('Invalid calendar date');
  const [y, m, d] = value.split('-').map(Number);
  const result = new Date(0); result.setHours(0, 0, 0, 0); result.setFullYear(y, m - 1, d);
  if (formatDate(result) !== value) throw new Error('Invalid calendar date');
  return result;
}
export function formatDate(date: Date): string {
  if (!Number.isFinite(date.getTime())) throw new Error('Invalid calendar date');
  return `${String(date.getFullYear()).padStart(4, '0')}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
export function shiftDate(date: Date, days: number): Date { const result = new Date(date); result.setDate(result.getDate() + days); return result; }
export function proposal(id: number, start: Date, exclusiveEnd: Date): DateProposal {
  return { milestoneId: id, start: formatDate(start), end: formatDate(shiftDate(exclusiveEnd, -1)) };
}
export function validateDependencies(rows: RoadmapMilestone[], edges: Dependency[], projectId: number) {
  const ids = new Set(rows.map(r => r.id)); const graph = new Map<number, number[]>(); const keys = new Set<string>();
  for (const edge of edges) {
    if (edge.project_id !== projectId || !ids.has(edge.from_id) || !ids.has(edge.to_id) || edge.from_id === edge.to_id) throw new Error('Invalid or cross-project dependency');
    const key = `${edge.from_id}:${edge.to_id}`; if (keys.has(key)) throw new Error('Duplicate dependency'); keys.add(key);
    graph.set(edge.from_id, [...(graph.get(edge.from_id) ?? []), edge.to_id]);
  }
  const active = new Set<number>(); const done = new Set<number>();
  function visit(id: number) { if (active.has(id)) throw new Error('Circular dependency'); if (done.has(id)) return; active.add(id); for (const next of graph.get(id) ?? []) visit(next); active.delete(id); done.add(id); }
  for (const id of ids) visit(id);
}
export function mapRoadmap(rows: RoadmapMilestone[], edges: Dependency[], projectId: number, canManage: boolean) {
  if (new Set(rows.map(r => r.id)).size !== rows.length || rows.some(r => !Number.isSafeInteger(r.id) || r.project_id !== projectId)) throw new Error('Invalid or duplicate milestone IDs');
  validateDependencies(rows, edges, projectId);
  const tasks: MappedTask[] = [...rows].sort((a, b) => a.display_order - b.display_order || a.id - b.id).map(row => {
    const start = calendarDate(row.planned_start_date); const end = calendarDate(row.planned_end_date);
    if (start > end) throw new Error('Invalid date interval');
    const editable = canManage && row.status === 'planned';
    return { id: row.id, name: row.title, startDate: start, endDate: shiftDate(end, 1), manuallyScheduled: true,
      draggable: editable, resizable: editable ? 'end' : false, readOnly: !editable,
      opendev: { status: row.status, deliverable: row.deliverable_description, displayOrder: row.display_order, signals: row.development_signals, stale: row.evidence.some(e => e.stale) } };
  });
  return { tasks, dependencies: edges.map(e => ({ id: e.id, fromTask: e.from_id, toTask: e.to_id, type: 2 })) };
}
export async function saveSchedule(row: RoadmapMilestone, dates: DateProposal, reason: string, canManage: boolean, request = api): Promise<RoadmapMilestone> {
  if (!canManage || row.status !== 'planned' || row.id !== dates.milestoneId) throw new Error('Only authorized maintainers may reschedule planned commitments');
  const start = calendarDate(dates.start); const end = calendarDate(dates.end);
  if (start > end) throw new Error('Start date must precede end date');
  if (reason.trim().length < 10 || reason.trim().length > 2000) throw new Error('Explain the change in 10–2000 characters');
  return request<RoadmapMilestone>(`/api/roadmap/${row.id}`, 'PATCH', { expected_version: row.version, reason: reason.trim(), planned_start_date: dates.start, planned_end_date: dates.end });
}
export async function loadTimeline(projectId: number) {
  async function pages<T>(path: string): Promise<T[]> {
    const items: T[] = [];
    for (let offset = 0; offset < 1000; offset += 100) {
      const page = await api<{ items: T[]; total: number }>(`${path}?limit=100&offset=${offset}`);
      if (!Number.isSafeInteger(page.total) || page.total < 0 || page.total > 1000 || !Array.isArray(page.items)) throw new Error('Timeline exceeds 1,000 records or returned an invalid response; use the milestone list');
      items.push(...page.items); if (items.length >= page.total) return items;
      if (!page.items.length) throw new Error('Roadmap changed while loading; refresh');
    }
    throw new Error('Timeline too large; use the milestone list');
  }
  const [rows, edges, sync] = await Promise.all([pages<RoadmapMilestone>(`/api/projects/${projectId}/roadmap`), pages<Dependency>(`/api/projects/${projectId}/roadmap/dependencies`), api<{ last_successful_sync_at: string | null; stale: boolean }>(`/api/projects/${projectId}/github/sync-status`)]);
  return { rows, edges, sync };
}
