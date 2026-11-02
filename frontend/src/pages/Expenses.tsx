import Accountability, { ExpenseVerification } from '../components/Accountability';
import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../api/client';
import ExpenseDocuments from '../components/ExpenseDocuments';
interface Expense { id: number; category: string; amount_cents: number; currency: string; vendor: string; description: string; expense_date: string; publication_status: 'draft' | 'published'; evidence_status: string }
const message = (e: unknown) => e instanceof Error ? e.message : 'Expense request failed';

function ExpenseForm({ projectId, expense, done }: { projectId: number; expense?: Expense; done: () => void }) {
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form); const amount = Number(data.get('amount'));
    if (!Number.isSafeInteger(amount) || amount <= 0) { setError('Use positive integer cents.'); return; }
    setBusy(true); setError('');
    try { await api(expense ? `/api/expenses/${expense.id}` : `/api/projects/${projectId}/expenses`, expense ? 'PATCH' : 'POST', { category: data.get('category'), amount_cents: amount, currency: 'USD', vendor: data.get('vendor'), description: data.get('description'), expense_date: data.get('date') }); if (!expense) form.reset(); done(); } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <form onSubmit={event => void submit(event)}><h4>{expense ? 'Edit expense draft' : 'Record an expense draft'}</h4><label>Category<input name="category" required maxLength={100} defaultValue={expense?.category} /></label><label>Amount (USD cents)<input name="amount" type="number" min="1" step="1" required defaultValue={expense?.amount_cents} /></label><label>Vendor<input name="vendor" required maxLength={200} defaultValue={expense?.vendor} /></label><label>Description<textarea name="description" required maxLength={10000} defaultValue={expense?.description} /></label><label>Expense date<input name="date" type="date" required defaultValue={expense?.expense_date} /></label>{error && <p role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Saving…' : 'Save expense draft'}</button></form>;
}

export default function Expenses({ projectId, canManage }: { projectId: number; canManage: boolean }) {
  const [items, setItems] = useState<Expense[]>([]); const [version, setVersion] = useState(0); const [page, setPage] = useState(0); const [error, setError] = useState(''); const [loading, setLoading] = useState(true); const [busy, setBusy] = useState(false);
  useEffect(() => { let live = true; api<Expense[]>(`/api/projects/${projectId}/expenses?include_drafts=${canManage}&offset=${page * 20}`).then(data => { if (live) { setItems(data); setError(''); } }).catch(e => { if (live) setError(message(e)); }).finally(() => { if (live) setLoading(false); }); return () => { live = false; }; }, [projectId, canManage, version, page]);
  const refresh = () => setVersion(v => v + 1);
  async function publish(id: number) { setBusy(true); try { await api(`/api/expenses/${id}/publish`, 'POST'); refresh(); } catch (e) { setError(message(e)); } finally { setBusy(false); } }
  return <section><Accountability projectId={projectId} refreshToken={version} /><h3>Reported project expenses</h3><p>Published expense claims and evidence do not independently verify spending or payment.</p>{canManage && <details><summary>Create expense</summary><ExpenseForm projectId={projectId} done={refresh} /></details>}{loading && <p role="status">Loading expenses…</p>}{error && <p role="alert">{error}</p>}{!loading && !items.length && <p>No expense records to show.</p>}{items.map(expense => <article key={expense.id}><h4>{expense.category} · {(expense.amount_cents / 100).toFixed(2)} {expense.currency}</h4><p>{expense.vendor} · {expense.expense_date} · {expense.publication_status} · {expense.evidence_status}</p><p>{expense.description}</p>{canManage && expense.publication_status === 'draft' && <><details><summary>Edit draft</summary><ExpenseForm projectId={projectId} expense={expense} done={refresh} /></details><button disabled={busy} onClick={() => void publish(expense.id)}>Publish expense claim (immutable)</button></>}<ExpenseVerification expenseId={expense.id} canManage={canManage} refreshToken={version} onReview={refresh} /><ExpenseDocuments expenseId={expense.id} canManage={canManage} expensePublished={expense.publication_status === 'published'} /></article>)}<div className="actions"><button disabled={!page} onClick={() => { setLoading(true); setPage(page - 1); }}>Previous expenses</button><button disabled={items.length < 20} onClick={() => { setLoading(true); setPage(page + 1); }}>Next expenses</button></div></section>;
}
