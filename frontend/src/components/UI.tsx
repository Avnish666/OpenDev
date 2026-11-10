import type { ReactNode } from 'react';

export function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="page-heading page-heading-row"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{description && <p className="muted">{description}</p>}</div>{action && <div className="heading-action">{action}</div>}</div>;
}

export function SectionHeading({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="section-heading"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h3>{title}</h3>{description && <p>{description}</p>}</div>{action}</div>;
}

export function MetricCard({ label, value, note, emphasis = false }: { label: string; value: ReactNode; note?: string; emphasis?: boolean }) {
  return <article className={`metric-card${emphasis ? ' metric-emphasis' : ''}`}><h4>{label}</h4><p className="metric-value">{value}</p>{note && <p className="metric-note">{note}</p>}</article>;
}

export function StatusBadge({ status, children }: { status: string; children?: ReactNode }) {
  const tone = ['active', 'completed', 'fulfilled', 'granted', 'answered', 'delivered'].includes(status) ? 'success' : ['pending', 'created', 'in_progress', 'submitted_for_review'].includes(status) ? 'warning' : ['failed', 'denied', 'provider_unavailable', 'reversed'].includes(status) ? 'error' : 'neutral';
  return <span className={`badge status-badge status-${tone}`}><span aria-hidden="true" className="status-dot" />{children ?? status.replaceAll('_', ' ')}</span>;
}

export function FormSection({ number, title, description, children }: { number: string; title: string; description?: string; children: ReactNode }) {
  return <fieldset className="form-section"><legend><span aria-hidden="true">{number}</span>{title}</legend>{description && <p className="form-section-description">{description}</p>}<div className="form-fields">{children}</div></fieldset>;
}

export function EmptyState({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return <div className="empty-state"><span className="empty-state-symbol" aria-hidden="true"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M5 4h10l4 4v12H5zM15 4v5h4M8 13h8M8 16h5" /></svg></span><h4>{title}</h4><p>{description}</p>{children}</div>;
}
