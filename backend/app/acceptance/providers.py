"""Redacted, read-only provider readiness. No orders, refunds or object mutations."""
import argparse
import json
import os
import re
import time
import httpx

PAYPAL='https://api-m.sandbox.paypal.com'
GROUPS={'paypal':('PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PAYPAL_WEBHOOK_ID','PAYPAL_MERCHANT_ID'),
        'supabase':('SUPABASE_PROJECT_REF','SUPABASE_STORAGE_BUCKET','SUPABASE_SERVICE_ROLE_KEY'),
        'github':('GITHUB_CLIENT_ID','GITHUB_CLIENT_SECRET','GITHUB_CALLBACK_URL')}
PREFIX='ACCEPTANCE_'


def readiness(env):
    # Application presence is membership-only; never load/read production values or .env.
    return {name:{'present':[key for key in fields if PREFIX+key in env],
                  'missing':[key for key in fields if PREFIX+key not in env],
                  'application_fields_present':[key for key in (('SUPABASE_URL','SUPABASE_STORAGE_BUCKET','SUPABASE_SERVICE_ROLE_KEY') if name=='supabase' else fields) if key in env]}
            for name,fields in GROUPS.items()}


def run(env,execute=False,confirm=False,probe=False,transport=None):
    result={'environment':'disposable-test','execution':'mocked' if transport is not None else 'live_read_only' if execute else 'network_probe' if probe else 'dry_run',
            'configuration':readiness(env),'features':{},'network':{},
            'paypal':{'status':'not_run'},'supabase':{'status':'not_run'},
            'genuine_webhook_delivery':'blocked_no_verified_reachable_endpoint',
            'transactions':'not_implemented','object_mutations':'not_implemented'}
    for key in ('CHECKOUT_ENABLED','RECEIPT_PROCESSING_ENABLED','LLM_ENABLED'):
        result['features'][key]=env.get(key,'not_explicitly_configured') in ('true','false') and env[key] or 'not_explicitly_configured'
        # Only known enum labels are emitted, even for malformed input.
    if not execute and not probe:return result
    if execute and (not confirm or env.get('ACCEPTANCE_ENVIRONMENT')!='disposable-test'):
        result['blocked']='Disposable environment confirmation required';return result
    ref=env.get(PREFIX+'SUPABASE_PROJECT_REF','')
    bucket=env.get(PREFIX+'SUPABASE_STORAGE_BUCKET','')
    storage_valid=bool(re.fullmatch(r'[a-z0-9]{8,40}',ref) and re.fullmatch(r'opendev-acceptance-[a-z0-9-]{1,40}',bucket))
    # Derive one HTTPS provider host; never accept arbitrary URLs, ports or paths.
    supabase=f'https://{ref}.supabase.co' if storage_valid else None
    deadline=time.monotonic()+20
    def request(client,method,url,**kwargs):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError()
        with client.stream(method,url,timeout=min(5,remaining),**kwargs) as response:
            body=bytearray()
            for chunk in response.iter_raw():
                if time.monotonic()>deadline or len(body)+len(chunk)>16384:raise ValueError()
                body.extend(chunk)
            return response.status_code,bytes(body)
    with httpx.Client(transport=transport,follow_redirects=False,timeout=5,headers={'Accept-Encoding':'identity'}) as client:
        if probe:
            for name,url in [('paypal',PAYPAL),('supabase',supabase)]:
                if url is None:result['network'][name]='not_configured';continue
                try:
                    status,_=request(client,'HEAD',url)
                    result['network'][name]='reachable' if 200<=status<400 else 'blocked_or_provider_rejected'
                except Exception:result['network'][name]='unavailable'
        if not execute:return result
        # Only dedicated acceptance fields are used. Do not fall back to application credentials.
        keys=GROUPS['paypal']
        if any(not env.get(PREFIX+k) for k in keys):result['paypal']['status']='blocked_missing_test_configuration'
        else:
            try:
                status,body=request(client,'POST',PAYPAL+'/v1/oauth2/token',auth=(env[PREFIX+'PAYPAL_CLIENT_ID'],env[PREFIX+'PAYPAL_CLIENT_SECRET']),data={'grant_type':'client_credentials'})
                value=json.loads(body)
                if status!=200 or not isinstance(value,dict) or not isinstance(value.get('access_token'),str) or not value['access_token']:raise ValueError()
                result['paypal']={'status':'passed','scope':'Sandbox OAuth only; no order/capture/signature/merchant verification'}
            except Exception:result['paypal']={'status':'failed','reason':'Sandbox authentication/network/response check failed'}
        if not storage_valid or not env.get(PREFIX+'SUPABASE_SERVICE_ROLE_KEY'):result['supabase']['status']='blocked_missing_or_invalid_test_configuration'
        else:
            try:
                key=env[PREFIX+'SUPABASE_SERVICE_ROLE_KEY']
                status,body=request(client,'GET',supabase+'/storage/v1/bucket/'+bucket,headers={'apikey':key,'Authorization':'Bearer '+key})
                value=json.loads(body)
                if status!=200 or not isinstance(value,dict) or value.get('public') is not False or value.get('id')!=bucket:raise ValueError()
                result['supabase']={'status':'passed','scope':'Authenticated test-bucket metadata and private flag only; object policies/expiry not verified'}
            except Exception:result['supabase']={'status':'failed','reason':'Private test-bucket/network/response check failed'}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment',choices=['disposable-test'],required=True)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--execute-read-only',action='store_true')
    parser.add_argument('--confirm-disposable',action='store_true')
    parser.add_argument('--probe-network',action='store_true')
    args=parser.parse_args()
    if args.dry_run and (args.execute_read_only or args.probe_network):parser.error('Dry-run cannot perform network operations')
    try:
        result=run(os.environ,execute=args.execute_read_only,confirm=args.confirm_disposable,probe=args.probe_network)
    except Exception:
        # Even client/proxy initialization errors must not print environment values.
        print(json.dumps({'environment':'disposable-test','status':'blocked','reason':'Diagnostic initialization failed; raw details withheld'}))
        return 2
    print(json.dumps(result,indent=2))
    if args.execute_read_only and (result.get('blocked') or any(result[k]['status']!='passed' for k in ('paypal','supabase'))):return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
