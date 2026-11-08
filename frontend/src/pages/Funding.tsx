import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
export interface Contribution { id: string; project_id: number; tier_id: number; amount_cents: number; currency: string; status: string; order_id: string | null; capture_id: string | null; approval_url: string | null; reward: { name: string }; entitlement: { status: string; fulfillment_note: string } | null }
const message = (e: unknown) => e instanceof Error ? e.message : 'Funding request failed';
export function CheckoutButton({ tierId }: { tierId: number }) {
  const { user } = useAuth(); const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  async function start() {
    setBusy(true); setError('');
    const key=`paypal-checkout-${tierId}`;
    try {
      let id=sessionStorage.getItem(key); if (!id) { id=crypto.randomUUID(); sessionStorage.setItem(key,id); }
      const c=await api<Contribution>('/api/funding/orders','POST',{tier_id:tierId,checkout_key:id});
      if (c.approval_url) { const url=new URL(c.approval_url); if(url.protocol!=='https:' || url.hostname!=='www.sandbox.paypal.com') throw new Error('Invalid Sandbox approval URL'); window.location.assign(url.href); }
      else { sessionStorage.removeItem(key); window.location.hash='/history'; }
    } catch(e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <><button disabled={!user || busy} onClick={() => void start()}>{busy?'Opening Sandbox…':user?'Back with PayPal Sandbox':'Sign in to back this project'}</button>{error && <p role="alert">{error}</p>}</>;
}
export function FundingReturn({ cancelled=false }: { cancelled?: boolean }) {
  const [result,setResult]=useState<Contribution>(); const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  const id=new URLSearchParams(window.location.search).get('contribution');
  async function finish() { setBusy(true); try { const c=await api<Contribution>(`/api/funding/${encodeURIComponent(id ?? '')}/${cancelled?'cancel':'capture'}`,'POST'); setResult(c); sessionStorage.removeItem(`paypal-checkout-${c.tier_id}`); } catch(e){setError(message(e));} finally{setBusy(false);} }
  return <section className="payment-return"><span className="sandbox-label">PAYPAL SANDBOX</span><h2>{cancelled?'Checkout cancelled':'Returned from PayPal Sandbox'}</h2><p>{cancelled?'No reward is granted for cancelling checkout.':'Approval alone does not grant a reward. Complete capture below; the server verifies the result.'}</p>{id && <button disabled={busy || !!result} onClick={() => void finish()}>{busy?'Checking…':cancelled?'Record cancellation':'Complete funding'}</button>}{error && <p role="alert">{error}</p>}{!id && <p className="disclosure">No contribution reference was supplied. Open your funding history to check a contribution.</p>}{result && <article><h3>Contribution summary</h3><p role="status">Contribution status: {result.status}</p><p>{new Intl.NumberFormat(undefined, { style: 'currency', currency: result.currency }).format(result.amount_cents / 100)}</p><p>Reward: {result.reward.name} · {result.entitlement?.status ?? 'Not granted'}</p>{result.entitlement?.fulfillment_note && <p>{result.entitlement.fulfillment_note}</p>}</article>}<a href="#/history">View funding and rewards</a></section>;
}
export function FundingHistory({ projectId }: { projectId?: number }) {
  const [items,setItems]=useState<Contribution[]>([]);const [error,setError]=useState('');const [loading,setLoading]=useState(true);const [page,setPage]=useState(0); const [busy,setBusy]=useState('');
  useEffect(()=>{let live=true;api<Contribution[]>(projectId?`/api/projects/${projectId}/fulfillments`:`/api/me/contributions?offset=${page*20}`).then(data=>{if(live){setItems(data);setError('');}}).catch(e=>{if(live)setError(message(e));}).finally(()=>{if(live)setLoading(false);});return()=>{live=false;};},[projectId,page]);
  async function action(c:Contribution, operation:string, note?:string){setBusy(c.id);setError('');try{const updated=await api<Contribution>(`/api/funding/${c.id}/${operation}`,operation==='fulfill'?'PATCH':'POST',note?{note}:undefined);setItems(items.map(i=>i.id===c.id?updated:i));}catch(e){setError(message(e));}finally{setBusy('');}}
  return <section className="funding-history"><p className="eyebrow">YOUR SUPPORT, WITH VISIBILITY</p><h2>{projectId?'Reward fulfillment':'My contributions and rewards'}</h2>{loading && <p role="status">Loading history…</p>}{error && <p role="alert">{error}</p>}{!loading && !items.length && <p>No contributions yet.</p>}<div className="grid">{items.map(c=><article key={c.id}><h3>{c.reward.name}</h3><a href={`#/projects/${c.project_id}`}>Project details</a><p>{(c.amount_cents/100).toFixed(2)} {c.currency} · {c.status}</p><p>Capture: {c.capture_id ?? 'Not captured'}</p><p>Reward: {c.entitlement?.status ?? 'Not granted'}</p>{c.entitlement?.fulfillment_note && <p>{c.entitlement.fulfillment_note}</p>}{!projectId && c.status==='created' && c.approval_url && <a href={c.approval_url}>Resume Sandbox approval</a>}{!projectId && ['created','pending','denied'].includes(c.status) && <button disabled={busy===c.id} onClick={()=>void action(c,'capture')}>Check / complete capture</button>}{projectId && c.entitlement?.status==='granted' && <form onSubmit={e=>{e.preventDefault();const note=String(new FormData(e.currentTarget).get('note'));void action(c,'fulfill',note);}}><label>Fulfillment details<textarea name="note" required maxLength={2000}/></label><button disabled={busy===c.id}>Mark fulfilled</button></form>}</article>)}</div>{!projectId && <div className="actions"><button disabled={!page} onClick={()=>setPage(page-1)}>Previous</button><button disabled={items.length<20} onClick={()=>setPage(page+1)}>Next</button></div>}</section>;
}
