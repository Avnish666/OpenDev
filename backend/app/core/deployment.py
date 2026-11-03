"""Offline production configuration checks; errors contain names, never values."""
import os
from urllib.parse import urlsplit
from sqlalchemy.engine import make_url


def feature(name,production):
    value=os.getenv(name,'false' if production else 'true')
    if value not in ('true','false'):raise RuntimeError('Invalid boolean configuration: '+name)
    return value=='true'


def validate_database(value):
    """Must run before engine construction, including malformed port/driver errors."""
    try:
        db=make_url(value)
        if db.drivername not in ('postgresql','postgresql+psycopg') or not db.host or not db.database:raise ValueError()
        if db.host not in ('localhost','127.0.0.1','::1') and db.query.get('sslmode') not in ('require','verify-ca','verify-full'):raise ValueError()
    except Exception:raise RuntimeError('Invalid production configuration: DATABASE_URL') from None


def validate(settings):
    if settings.APP_ENV not in ('development','testing','production'):
        raise RuntimeError('Invalid configuration: APP_ENV')
    try:
        port=int(os.getenv('PORT','10000'))
        if not 1<=port<=65535:raise ValueError()
    except ValueError:raise RuntimeError('Invalid configuration: PORT') from None
    if settings.APP_ENV!='production':return
    bad=[]
    try:
        origin=urlsplit(settings.FRONTEND_URL)
        invalid=(origin.port is not None and not 1<=origin.port<=65535) or origin.scheme!='https' or not origin.hostname or origin.username or origin.password or origin.path or origin.query or origin.fragment
    except ValueError:invalid=True
    if invalid:
        bad.append('FRONTEND_URL')
    if not settings.GITHUB_CALLBACK_URL:
        settings.GITHUB_CALLBACK_URL=settings.FRONTEND_URL+'/api/auth/github/callback'
    if settings.GITHUB_CALLBACK_URL!=settings.FRONTEND_URL+'/api/auth/github/callback':bad.append('GITHUB_CALLBACK_URL')
    for name in ('GITHUB_CLIENT_ID','GITHUB_CLIENT_SECRET','PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PAYPAL_WEBHOOK_ID','PAYPAL_MERCHANT_ID','SUPABASE_URL','SUPABASE_STORAGE_BUCKET','SUPABASE_SERVICE_ROLE_KEY'):
        value=os.getenv(name,'')
        if not value.strip() or value.strip().lower() in ('replace_me','changeme','placeholder'):bad.append(name)
    try:
        validate_database(settings.DATABASE_URL)
    except Exception:bad.append('DATABASE_URL')
    try:
        from app.services.storage import Storage
        Storage().configuration()
    except Exception:bad.extend(['SUPABASE_URL','SUPABASE_STORAGE_BUCKET','SUPABASE_SERVICE_ROLE_KEY'])
    try:
        from app.agent.orchestration import AgentConfig
        AgentConfig.load()
        if settings.LLM_ENABLED:
            from app.agent.providers import OllamaProvider
            OllamaProvider(os.environ['OLLAMA_BASE_URL'],os.environ['OLLAMA_MODEL'])
    except Exception:bad.append('AGENT_CONFIGURATION')
    if os.getenv('FORWARDED_ALLOW_IPS')=='*':bad.append('FORWARDED_ALLOW_IPS')
    if bad:raise RuntimeError('Invalid production configuration: '+', '.join(sorted(set(bad))))
