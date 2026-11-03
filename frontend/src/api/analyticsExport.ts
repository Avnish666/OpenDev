import type { DashboardFilters } from './dashboardFilters';
export const exportDatasets=['expenses','financial','budget','roadmap','github','maintainer-delivery'] as const;
export type ExportDataset=typeof exportDatasets[number];
export async function downloadCsv(projectId:number,dataset:ExportDataset,filters:DashboardFilters,signal:AbortSignal){
 const params=new URLSearchParams();for(const [key,value] of Object.entries(filters))if(value&&!['participation','reward'].includes(key))params.set(key,value);
 const response=await fetch(`${import.meta.env.VITE_API_URL??''}/api/projects/${projectId}/analytics/export/${dataset}?${params}`,{credentials:'include',cache:'no-store',signal});
 if(!response.ok)throw new Error(response.status===413?'Export exceeds capacity. Narrow the filters.':response.status===429?'Export rate limit reached. Retry in a minute.':response.status===404?'Public project unavailable.':'Unable to export. Retry or narrow the filters.');
 if(!response.headers.get('content-type')?.startsWith('text/csv'))throw new Error('Invalid export response.');
 const blob=await response.blob();if(signal.aborted)throw new DOMException('Aborted','AbortError');if(blob.size>2*1024*1024)throw new Error('Export exceeds download capacity.');
 const url=URL.createObjectURL(blob);try{const link=document.createElement('a');link.href=url;link.download=`opendev-project-${projectId}-${dataset}.csv`;document.body.append(link);link.click();link.remove();}finally{setTimeout(()=>URL.revokeObjectURL(url),1000);}
}
