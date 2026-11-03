import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../api/client';
import { displayMoney as money, transparencyAPI, type PublicTransparency, type PublicFinding, type LedgerPage, type LedgerEntry } from '../api/transparency';
import './Transparency.css';

const message = (error: unknown) => error instanceof Error ? error.message : 'Unable to load public financial records.';

function Findings({ items }: { items: PublicFinding[] }) {
  return <ul>{items.map(item => <li key={item.category}><strong>{item.category} · {item.severity} · unresolved</strong><p>{item.explanation}</p><p>Applies to the category total, not an assertion about an individual payment.</p></li>)}</ul>;
}

function ExpenseDetail({ projectId, expenseId }: { projectId: number; expenseId: number }) {
  const [entry, setEntry] = useState<LedgerEntry>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let live = true;
    transparencyAPI.detail(projectId, expenseId).then(data => { if (live) setEntry(data); }).catch(e => { if (live) setError(message(e)); });
    return () => { live = false; };
  }, [projectId, expenseId]);
  async function download(id: string) {
    setBusy(true); setError('');
    try {
      const result = await api<{ url: string; expires_in: number }>(`/api/documents/${encodeURIComponent(id)}/download`);
      // Never persist or prefetch signed URLs. Authorization is rechecked on every click.
      const url = new URL(result.url);
      if (url.protocol !== 'https:') throw new Error('Secure evidence download is unavailable.');
      window.location.assign(url.href);
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <article aria-label="Public expense detail" aria-live="polite">
    <h4>Expense details</h4>{error && <p role="alert">{error}</p>}
    {!entry && !error && <p role="status">Loading expense…</p>}
    {entry && <><h5>{entry.vendor} · {money(entry.amount_cents, entry.currency)}</h5><p className="description">{entry.description}</p>
      <p>{entry.category} · {entry.expense_date}</p><p>Evidence: {entry.evidence.length ? 'Approved redacted supporting documents' : 'Self-reported; no approved public evidence'}</p>
      <p>Vendor payment has not been independently verified.</p>
      <ul>{entry.evidence.map((doc, index) => <li key={doc.id}><button disabled={busy} onClick={() => void download(doc.id)}>Download approved redacted evidence {index + 1} ({doc.detected_mime_type})</button></li>)}</ul>
      <Findings items={entry.findings} /><p>Expense record updated: {new Date(entry.updated_at).toLocaleString()}</p></>}
  </article>;
}

function Ledger({ projectId, categories, refresh }: { projectId: number; categories: string[]; refresh: number }) {
  const [filters, setFilters] = useState({ q: '', category: '', evidence: 'all', sort: 'date_desc' });
  const [page, setPage] = useState(0);
  const [result, setResult] = useState<LedgerPage>();
  const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<number>();
  useEffect(() => {
    let live = true;
    transparencyAPI.ledger(projectId, new URLSearchParams({ ...filters, limit: '10', offset: String(page * 10) }))
      .then(data => { if (live) setResult(data); }).catch(e => { if (live) setError(message(e)); }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [projectId, filters, page, refresh]);
  function resetLedger() { setLoading(true); setResult(undefined); setError(''); setSelected(undefined); }
  function filter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    resetLedger(); setPage(0); setFilters({ q: String(form.get('q')).trim(), category: String(form.get('category')), evidence: String(form.get('evidence')), sort: String(form.get('sort')) });
  }
  return <section><h4>Published expense ledger</h4><form className="ledger-filters" onSubmit={filter}>
    <label>Search vendor, description or category<input name="q" maxLength={200} type="search" /></label>
    <label>Category<select name="category"><option value="">All categories</option>{categories.map(c => <option key={c}>{c}</option>)}</select></label>
    <label>Public evidence<select name="evidence"><option value="all">All expenses</option><option value="supported">With approved evidence</option><option value="unsupported">Without approved evidence</option></select></label>
    <label>Order<select name="sort"><option value="date_desc">Newest expense date first</option><option value="date_asc">Oldest expense date first</option></select></label><button>Apply filters</button>
  </form>
    {loading && <p role="status">Loading ledger…</p>}{error && <p role="alert">{error}</p>}
    {result && <><p aria-live="polite">{result.total} published expense(s) match.</p>
      {!result.items.length ? <p>No published expenses match these filters.</p> : <div className="ledger-table"><table><caption>Maintainer-reported expenses; supporting documents do not prove payment.</caption><thead><tr><th scope="col">Date</th><th scope="col">Vendor / category</th><th scope="col">Reported amount</th><th scope="col">Public evidence</th><th scope="col">Details</th></tr></thead><tbody>{result.items.map(item => <tr key={item.id}><td>{item.expense_date}</td><td>{item.vendor}<br />{item.category}</td><td>{money(item.amount_cents, item.currency)}</td><td>{item.evidence.length ? 'Approved redaction attached' : 'Self-reported'}</td><td><button aria-expanded={selected === item.id} onClick={() => setSelected(selected === item.id ? undefined : item.id)}>Inspect expense {item.id}</button></td></tr>)}</tbody></table></div>}
      <div className="actions"><button disabled={page === 0} onClick={() => { resetLedger(); setPage(p => p - 1); }}>Previous expenses</button><span>Page {page + 1}</span><button disabled={(page + 1) * 10 >= result.total} onClick={() => { resetLedger(); setPage(p => p + 1); }}>Next expenses</button></div>
      <p>Ledger calculated: {new Date(result.calculated_at).toLocaleString()}</p>
    </>}
    {selected !== undefined && <ExpenseDetail key={`${selected}-${refresh}`} projectId={projectId} expenseId={selected} />}
  </section>;
}

export default function Transparency({ projectId }: { projectId: number }) {
  const [data, setData] = useState<PublicTransparency>();
  const [error, setError] = useState(''); const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let live = true;
    transparencyAPI.overview(projectId).then(value => { if (live) setData(value); }).catch(e => { if (live) setError(message(e)); });
    return () => { live = false; };
  }, [projectId, refresh]);
  const s = data?.financial_summary;
  return <section className="transparency" aria-labelledby="transparency-title"><h3 id="transparency-title">Financial Transparency</h3><p><a href={`#/projects/${projectId}/analytics`}>Open project analytics</a></p>
    <p>Public records · PayPal Sandbox · amounts reported in USD minor units by the API.</p><button onClick={() => { setData(undefined); setError(''); setRefresh(v => v + 1); }}>Refresh public ledger</button>
    {error && <p role="alert">{error}</p>}{!data && !error && <p role="status">Loading financial transparency…</p>}
    {data && s && <><div className="grid">
      <article><h4>Net recorded funding</h4><p className="financial-value">{money(s.net_recorded_funding_cents, s.currency)}</p><p>Gross completed captures: {money(s.gross_completed_funding_cents, s.currency)}</p><p>Refund exclusions: {money(s.refund_excluded_cents, s.currency)}</p><p>Reversal exclusions: {money(s.reversal_excluded_cents, s.currency)}</p></article>
      <article><h4>Published reported spending</h4><p className="financial-value">{money(s.published_reported_spending_cents, s.currency)}</p><p>{s.published_expense_count} published expense(s)</p><p>Funding minus reported spending: {money(s.funding_minus_reported_expenditure_cents, s.currency)}</p><p>This calculated difference is not available cash or a verified bank balance.</p></article>
      <article><h4>Public document support</h4><p>{s.expenses_with_documents_count} expense(s) · {money(s.expenses_with_documents_cents, s.currency)} with approved redacted evidence</p><p>{s.expenses_without_documents_count} expense(s) · {money(s.expenses_without_documents_cents, s.currency)} without public evidence</p><p>Independently verified vendor payments: none.</p></article>
    </div>
      <h4>Budget allocation versus reported spending</h4><p>Bars share a scale within each category. Text values provide the exact amounts.</p>
      <div className="grid">{s.budget_variance.map(item => {
        const max = Math.max(item.allocated_cents, item.reported_spending_cents, 1);
        const safe = Number.isSafeInteger(max);
        return <article key={item.category}><h5>{item.category}</h5><p>Allocated: {money(item.allocated_cents, s.currency)}</p>{safe && <div className="budget-track" aria-hidden="true"><span className="allocation-bar" style={{ width: `${item.allocated_cents / max * 100}%` }} /></div>}<p>Reported: {money(item.reported_spending_cents, s.currency)}</p>{safe && <div className="budget-track" aria-hidden="true"><span className="spending-bar" style={{ width: `${item.reported_spending_cents / max * 100}%` }} /></div>}<p>Remaining allocation: {money(item.remaining_cents, s.currency)}</p><p>Reported overspend: {money(item.overspend_cents, s.currency)}</p></article>;
      })}</div>{!s.budget_variance.length && <p>No budget allocations or published expenses yet.</p>}
      <h4>Expense category breakdown</h4><ul>{s.budget_variance.map(item => <li key={item.category}>{item.category}: {money(item.reported_spending_cents, s.currency)}</li>)}</ul>
      <h4>Unresolved public findings: {data.public_unresolved_discrepancy_count}</h4><p>{data.finding_policy}</p><Findings items={data.public_findings} />
      <Ledger key={refresh} projectId={projectId} categories={s.budget_variance.map(item => item.category)} refresh={refresh} />
      <aside><h4>How to interpret these records</h4><ul>{s.notes.map(note => <li key={note}>{note}</li>)}</ul><p>No public finding is a fraud determination or payment certification.</p><p>Last refreshed: {new Date(data.last_updated_at).toLocaleString()}. {data.timestamp_basis}</p></aside>
    </>}
  </section>;
}

// A shareable route reuses the existing authorized public ledger detail component.
export function PublicExpensePage({projectId,expenseId}:{projectId:number;expenseId:number}) {
  return <section><h2>Public expense</h2><a href={`#/projects/${projectId}`}>Return to project</a><ExpenseDetail key={`${projectId}-${expenseId}`} projectId={projectId} expenseId={expenseId}/></section>;
}
