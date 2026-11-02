import ReceiptExtraction from './ReceiptExtraction';
import { useEffect, useState, type FormEvent } from 'react';
import { api, uploadReceipt } from '../api/client';

export interface ExpenseDocument { id: string; expense_id: number; original_filename: string; detected_mime_type: string; file_size_bytes: number; publication_status: 'private' | 'published'; is_redacted_version: boolean; duplicate_in_project: boolean | null }
const message = (e: unknown) => e instanceof Error ? e.message : 'Document request failed';

export default function ExpenseDocuments({ expenseId, canManage, expensePublished }: { expenseId: number; canManage: boolean; expensePublished: boolean }) {
  const [documents, setDocuments] = useState<ExpenseDocument[]>([]);
  const [file, setFile] = useState<File | null>(null); const [source, setSource] = useState('');
  const [error, setError] = useState(''); const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true); const [busy, setBusy] = useState(false); const [version, setVersion] = useState(0); const [page, setPage] = useState(0);
  useEffect(() => { let live = true; api<ExpenseDocument[]>(`/api/expenses/${expenseId}/documents?offset=${page * 20}`).then(data => { if (live) { setDocuments(data); setError(''); } }).catch(e => { if (live) setError(message(e)); }).finally(() => { if (live) setLoading(false); }); return () => { live = false; }; }, [expenseId, page, version]);
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget;
    if (!file) { setError('Select a receipt or invoice.'); return; }
    if (!file.size || file.size > 5 * 1024 * 1024 || !/\.(pdf|png|jpe?g)$/i.test(file.name)) { setError('Choose a nonempty PDF, PNG or JPEG of at most 5 MiB.'); return; }
    setBusy(true); setError(''); setSuccess('');
    try { const doc = await uploadReceipt(expenseId, file, source || undefined); setSuccess(`Uploaded privately.${doc.duplicate_in_project ? ' Duplicate content already exists in this project.' : ''}`); setFile(null); setSource(''); form.reset(); setVersion(v => v + 1); } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function download(id: string) {
    setBusy(true); setError('');
    try { const result = await api<{ url: string; expires_in: number }>(`/api/documents/${id}/download`); const url = new URL(result.url); if (url.protocol !== 'https:' || !/^[a-z0-9-]+\.supabase\.co$/.test(url.hostname)) throw new Error('Invalid private download URL'); window.location.assign(url.href); } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  async function publication(id: string, publish: boolean) {
    setBusy(true); setError(''); setSuccess('');
    try { await api(`/api/documents/${id}/${publish ? 'publish' : 'unpublish'}`, 'POST', publish ? { redaction_reviewed: true } : undefined); setVersion(v => v + 1); setSuccess(publish ? 'Reviewed redacted evidence is public. This does not verify payment.' : 'Evidence is private. Existing signed links may work for up to 60 seconds.'); } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <section aria-label="Expense receipts and invoices"><h4>Receipts and invoices</h4><p>Evidence is unverified and does not prove payment. Files are untrusted; downloads are attachments, not previews.</p>
    {canManage && <form onSubmit={event => void upload(event)}><p>PDF, PNG or JPEG, up to 5 MiB. Originals always remain private. Prepare redactions locally, including hidden text and metadata, before uploading a separate version.</p>
      <label>Version type<select value={source} onChange={event => setSource(event.target.value)}><option value="">Private original</option>{documents.filter(d => !d.is_redacted_version).map(d => <option key={d.id} value={d.id}>Redacted version of {d.original_filename}</option>)}</select></label>
      <label>File<input type="file" accept="application/pdf,image/png,image/jpeg,.pdf,.png,.jpg,.jpeg" disabled={busy} onChange={event => setFile(event.target.files?.[0] ?? null)} required /></label>
      {file && <p>{file.name} · {(file.size / 1024).toFixed(1)} KiB</p>}<button disabled={busy || !file}>{busy ? 'Uploading / validating…' : 'Upload privately'}</button></form>}
    {error && <p role="alert">{error}</p>}{success && <p role="status">{success}</p>}{loading && <p role="status">Loading documents…</p>}{!loading && !documents.length && <p>{canManage ? 'No attached documents.' : 'No approved redacted evidence has been published.'}</p>}
    <ul>{documents.map(doc => <li key={doc.id}><p>{doc.original_filename} · {doc.detected_mime_type} · {doc.file_size_bytes} bytes · {doc.publication_status}{doc.duplicate_in_project ? ' · Duplicate in project' : ''}</p><button disabled={busy} onClick={() => void download(doc.id)}>Download (60-second link)</button>
      {canManage && !doc.is_redacted_version && <ReceiptExtraction documentId={doc.id} />}
      {canManage && doc.is_redacted_version && doc.publication_status === 'private' && expensePublished && <form onSubmit={event => { event.preventDefault(); void publication(doc.id, true); }}><label className="checkbox"><input type="checkbox" required />I reviewed this version for personal data, secrets, hidden text and metadata and approve public disclosure.</label><button disabled={busy}>Publish reviewed redaction</button></form>}
      {canManage && doc.publication_status === 'published' && <button disabled={busy} onClick={() => void publication(doc.id, false)}>Make private</button>}</li>)}</ul>
    <div className="actions"><button disabled={!page || busy} onClick={() => { setLoading(true); setPage(page - 1); }}>Previous documents</button><button disabled={documents.length < 20 || busy} onClick={() => { setLoading(true); setPage(page + 1); }}>Next documents</button></div>
  </section>;
}
