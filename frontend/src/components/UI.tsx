import type { ReactNode } from 'react';

export function PageHeading({ title, description, action }: { eyebrow: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="page-heading page-heading-row"><div><h1>{title}</h1>{description && <p className="muted">{description}</p>}</div>{action && <div className="heading-action">{action}</div>}</div>;
}

export function SectionHeading({ title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="section-heading"><div><h3>{title}</h3>{description && <p>{description}</p>}</div>{action}</div>;
}

export function MetricCard({ label, value, note, emphasis = false }: { label: string; value: ReactNode; note?: string; emphasis?: boolean }) {
  return <article className={`metric-card${emphasis ? ' metric-emphasis' : ''}`}><h4>{label}</h4><p className="metric-value">{value}</p>{note && <p className="metric-note">{note}</p>}</article>;
}

export function StatusBadge({ status, children }: { status: string; children?: ReactNode }) {
  const tone = ['active', 'completed', 'fulfilled', 'granted', 'answered', 'delivered'].includes(status) ? 'success' : ['pending', 'created', 'in_progress', 'submitted_for_review'].includes(status) ? 'warning' : ['failed', 'denied', 'provider_unavailable', 'reversed'].includes(status) ? 'error' : 'neutral';
  return <span className={`badge status-badge status-${tone}`}><span aria-hidden="true" className="status-dot" />{children ?? status.replaceAll('_', ' ')}</span>;
}

export function FormSection({ number, title, description, children }: { number: string; title: string; description?: string; children: ReactNode }) {
  return <fieldset className="form-section" data-section={number}><legend>{title}</legend>{description && <p className="form-section-description">{description}</p>}<div className="form-fields">{children}</div></fieldset>;
}

export function EmptyState({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return <div className="empty-state"><h4>{title}</h4><p>{description}</p>{children}</div>;
}
