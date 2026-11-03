export function agentFixture(mode='deterministic',status='answered') {
 const source='opendev:project:5:finances',hash='a'.repeat(64);
 const c={source_id:source,reference:`${source}@sha256:${hash}`,api_path:'/api/projects/5/transparency',method:'GET',request_body:null,projection_sha256:hash,retrieved_at:'2026-11-03T10:00:00Z'};
 return {answer:'Net recorded funding: 2000 USD minor units. Not a verified bank balance.',citations:[c],evidence_used:[{source_type:'project',source_id:source,project_id:5,claim:'finances',value:{},observed_at:c.retrieved_at,last_updated_at:null,visibility:'public_active_projects',freshness:'unknown',citation:c,limitations:['Reports do not certify payment.']}],limitations:['Reports do not certify payment.'],confidence:'limited_evidence',answer_status:status,execution_mode:mode,source_freshness:{[source]:'unknown'},diagnostics:{}};
}
