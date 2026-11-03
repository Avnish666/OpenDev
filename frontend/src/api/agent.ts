import { APIError } from './client';
export type AgentMode = 'deterministic' | 'llm' | 'auto';
export type AnswerStatus = 'answered' | 'insufficient_evidence' | 'unsupported_question' | 'unavailable_source' | 'provider_unavailable';
export type Freshness = 'current_database_snapshot' | 'stale' | 'unknown';
export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };
export interface Citation {
  source_id: string; reference: string; api_path: string; method: 'GET' | 'POST';
  request_body: Record<string, JsonValue> | null; projection_sha256: string; retrieved_at: string;
}
export interface AgentEvidence {
  source_type: string; source_id: string; project_id: number | null; claim: string; value: JsonValue;
  observed_at: string; last_updated_at: string | null; visibility: 'public_active_projects';
  freshness: Freshness; citation: Citation; limitations: string[];
}
export interface AgentAnswer {
  answer: string; citations: Citation[]; evidence_used: AgentEvidence[]; limitations: string[];
  confidence: 'deterministic_records' | 'limited_evidence' | 'not_applicable'; answer_status: AnswerStatus;
  execution_mode: 'deterministic' | 'llm'; source_freshness: Record<string, string>; diagnostics: Record<string, JsonValue>;
}
const API_URL = import.meta.env.VITE_API_URL ?? '';
const statuses = ['answered', 'insufficient_evidence', 'unsupported_question', 'unavailable_source', 'provider_unavailable'];
const object = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every(x => typeof x === 'string');
function citation(v: unknown): boolean {
  return object(v) && ['source_id', 'reference', 'api_path', 'projection_sha256', 'retrieved_at'].every(k => typeof v[k] === 'string') &&
    ['GET', 'POST'].includes(String(v.method)) && (v.request_body === null || object(v.request_body));
}
export function parseAgentAnswer(v: unknown): AgentAnswer {
  if (!object(v) || typeof v.answer !== 'string' || !statuses.includes(String(v.answer_status)) ||
      !['deterministic', 'llm'].includes(String(v.execution_mode)) || !strings(v.limitations) ||
      !['deterministic_records', 'limited_evidence', 'not_applicable'].includes(String(v.confidence)) ||
      !Array.isArray(v.citations) || !v.citations.every(citation) || !Array.isArray(v.evidence_used) ||
      !v.evidence_used.every(e => object(e) && ['source_type', 'source_id', 'claim', 'observed_at'].every(k => typeof e[k] === 'string') &&
        (e.project_id === null || Number.isSafeInteger(e.project_id)) && e.visibility === 'public_active_projects' &&
        ['current_database_snapshot', 'stale', 'unknown'].includes(String(e.freshness)) && strings(e.limitations) &&
        (e.last_updated_at === null || typeof e.last_updated_at === 'string') && 'value' in e && citation(e.citation)) ||
      !object(v.source_freshness) || !Object.values(v.source_freshness).every(x => typeof x === 'string') || !object(v.diagnostics)) {
    throw new Error('The agent returned an invalid response. No answer was displayed.');
  }
  return v as unknown as AgentAnswer;
}
export class AgentRequestError extends APIError {
  retryAfter: number;
  retryAt?: number;
  constructor(status: number, message: string, retryAfter = 0) { super(status, message); this.retryAfter = retryAfter; this.retryAt = retryAfter ? Date.now() + retryAfter * 1000 : undefined; }
}
export function errorForStatus(status: number): string {
  if ([400, 422].includes(status)) return 'Check your question: use 3–1,000 characters and a valid project.';
  if ([401, 403].includes(status)) return 'This public project query is not authorized. Refresh the project before retrying.';
  if (status === 404) return 'This project is no longer publicly available.';
  if (status === 429) return 'Too many queries. Please wait before retrying.';
  if ([408, 504].includes(status)) return 'The agent request timed out. You can retry or use Deterministic mode.';
  if (status === 503) return 'The agent service is unavailable. Try again later or use Deterministic mode.';
  return 'The agent could not answer this request. Please retry later.';
}
export async function queryAgent(projectId: number, question: string, mode: AgentMode, signal: AbortSignal): Promise<AgentAnswer> {
  const trimmed = question.trim();
  if (!Number.isSafeInteger(projectId) || projectId <= 0 || Array.from(trimmed).length < 3 || Array.from(trimmed).length > 1000) throw new AgentRequestError(422, errorForStatus(422));
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/projects/${projectId}/agent/query`, { method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ project_id: projectId, question: trimmed, mode }), signal, cache: 'no-store' });
  } catch (e) { if (signal.aborted) throw e; throw new Error('Network connection failed. Check your connection and retry.'); }
  if (!response.ok) {
    const retry = response.headers.get('Retry-After') ?? '';
    const seconds = /^\d+$/.test(retry) ? Number(retry) : Math.ceil((Date.parse(retry) - Date.now()) / 1000);
    throw new AgentRequestError(response.status, errorForStatus(response.status), Number.isFinite(seconds) ? Math.max(0, Math.min(seconds, 3600)) : 0);
  }
  let data: unknown;
  try { data = await response.json(); } catch { throw new Error('The agent returned an invalid response. No answer was displayed.'); }
  return parseAgentAnswer(data);
}

export interface SourcePresentation { title: string; category: string; explanation: string; href?: string; verifiedReference?: string }
export function citationPresentation(c: Citation, e: AgentEvidence | undefined, projectId: number, ownerId?: number): SourcePresentation {
  const unknown: SourcePresentation = { title: 'Unrecognized source', category: 'Unavailable', explanation: 'No supported public destination. Source identifiers are withheld.' };
  if (!e || e.citation.reference !== c.reference || e.source_id !== c.source_id || e.citation.projection_sha256 !== c.projection_sha256 ||
      !/^[a-f0-9]{64}$/.test(c.projection_sha256) || c.reference !== `${c.source_id}@sha256:${c.projection_sha256}`) return unknown;
  const id = projectId;
  const suffix = e.claim;
  let title = '', category = '', explanation = '', path = '';
  if (e.project_id === id && e.source_id === `opendev:project:${id}:${suffix}`) {
    if (suffix === 'finances') { title = 'Funding and reported spending'; category = 'Recorded financial facts'; explanation = 'Deterministic public accounting. Reported expenses and calculated differences are not verified cash balances.'; path = `/api/projects/${id}/transparency`; }
    if (/^expenses:offset:\d+$/.test(suffix)) { title = 'Published expense ledger'; category = 'Maintainer reports'; explanation = 'Published expense reports and approved-redaction metadata only. A document does not prove payment.'; path = `/api/projects/${id}/ledger?limit=50&offset=${suffix.split(':').at(-1)}`; }
    if (/^roadmap:offset:\d+$/.test(suffix)) { title = 'Commitments and public history'; category = 'Maintainer assertions'; explanation = 'Delivery is self-reported. Counts may be page-scoped; original deadlines and history are not independent certification.'; path = `/api/projects/${id}/roadmap?limit=50&offset=${suffix.split(':').at(-1)}`; }
    if (suffix === 'overview') { title = 'Public project overview'; category = 'Project report'; explanation = 'Current public project identity and recorded goal.'; path = `/api/projects/${id}`; }
    if (suffix === 'reward_fulfillment') { title = 'Project reward fulfillment'; category = 'Maintainer assertions'; explanation = 'Public aggregates of eligible Sandbox rewards. The source requires a read-only POST query; no automatic navigation or POST is performed.'; }
  } else if (e.project_id === id && e.source_type === 'github_repository' && /^activity:offset:\d+$/.test(suffix) && new RegExp(`^opendev:github_repository:[0-9]+:${suffix}$`).test(e.source_id)) {
    title = 'Synchronized GitHub activity'; category = 'GitHub observations'; explanation = 'Retained snapshots and sampled commits, not complete repository history or proof of delivery.';
    path = `/api/projects/${id}/github/activity?limit=50&offset=${suffix.split(':').at(-1)}`;
  } else if (e.project_id === null && ownerId && e.source_id === `opendev:maintainer:${ownerId}:history`) {
    title = 'Public maintainer track record'; category = 'Owner outcomes and participation'; explanation = 'Currently owned active public projects only. No trust score or independent delivery verification.'; path = `/api/maintainers/${ownerId}/credibility`;
  }
  if (!title) return unknown;
  // Reconstruct only known API routes, and require the backend path to match exactly.
  // Never turn source text, receipt paths, signed URLs or model-provided external URLs into links.
  let href: string | undefined;
  if (path && c.method === 'GET' && c.api_path === path && e.citation.api_path === path) {
    try {
      const url = new URL(`${API_URL}${path}`, 'http://local.invalid');
      if (['https:', 'http:'].includes(url.protocol) && !url.username && !url.password) href = `${API_URL}${path}`;
    } catch { /* Show metadata without a link. */ }
  }
  return { title, category, explanation, href, verifiedReference: c.reference };
}
