import { useAuth } from '../../context/AuthContext';
import Icon from '../Icon';
import { useEffect, useRef } from 'react';

export default function GitHubLogin() {
  const { user, loading, error, login, logout } = useAuth();
  const account = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const close = (event: KeyboardEvent | PointerEvent) => {
      if (!account.current?.open) return;
      if (event instanceof KeyboardEvent && event.key === 'Escape') { account.current.open = false; account.current.querySelector('summary')?.focus(); }
      else if (event instanceof PointerEvent && event.target instanceof Node && !account.current.contains(event.target)) account.current.open = false;
    };
    document.addEventListener('keydown', close); document.addEventListener('pointerdown', close);
    return () => { document.removeEventListener('keydown', close); document.removeEventListener('pointerdown', close); };
  }, []);
  if (loading) return <span className="muted" role="status">Checking authentication…</span>;
  if (!user) return <div className="auth-control"><button className="auth-login secondary" onClick={login}><Icon name="github" size={18} /><span>Sign in with GitHub</span></button>{error && <span className="auth-error" role="alert">{error}</span>}</div>;
  return <details className="account-menu" ref={account}><summary>{user.avatar_url ? <img src={user.avatar_url} alt="" width={32} height={32} referrerPolicy="no-referrer" /> : <span className="avatar-fallback">{user.username[0]}</span>}<span>{user.username}</span><span aria-hidden="true">⌄</span></summary><div className="account-dropdown"><div className="account-identity"><span className="field-caption">GITHUB ACCOUNT</span><strong>{user.username}</strong></div><a href={`#/maintainers/${user.id}`}>Public profile</a><a href="#/my">My projects</a><a href="#/history">Funding & rewards</a><button className="secondary" onClick={() => { void logout().catch(console.error); }}>Log out</button></div></details>;
}
